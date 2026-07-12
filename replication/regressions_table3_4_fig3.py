"""
regressions_table3_4_fig3.py
============================
Replicate the paper's central hypothesis test.

  * Table 3 -- "The impact of friend dyads and impartiality on ESC voting
               patterns" (models 1-6 pooled OLS, 7-8 pooled Tobit, 9-10 RE Tobit).
  * Table 4 -- robustness by alternative friend-group measure and voting rule.
  * Fig. 3  -- marginal effect of friend voting on the vote, conditioned by
               impartiality, over the range of song quality.

Estimating equation (paper):
    Vote_ijt = b1*Friend_ijt + b2*Impartiality_it + b3*(Friend x Impartiality)_it
               + b4*Quality_jt + song-traits + dyadic controls + e

HYPOTHESIS H1: b3 < 0 -- the voting bias from being a friend dyad shrinks as the
voter's country becomes more impartial (friends matter less where institutions
are impartial), even though b1 > 0 (friends do bias their votes).

DATA CAVEATS (documented honestly):
  * Duet / Group / Female song-trait dummies and the Diaspora control are NOT in
    the data folder, so those specific columns of Table 3/4 are omitted.
  * English / French are heuristic language flags (no "language sung" field).
  * "Friend dyad" (method 1) uses our reproduced clusters, which differ somewhat
    from the paper's, so magnitudes will not match to the decimal -- but the
    signs and significance of the key terms are what test the hypothesis.
  * Random-effects Tobit is approximated by pooled Tobit (a full RE-Tobit needs
    specialised software); this is flagged in the output.
"""

import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

from tobit import tobit

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")


# ---------------------------------------------------------------------------
# 1. Load the master panel and attach the two friend-dyad measures, matched to
#    each row's time period (pre/post 1998), exactly as the paper codes them.
# ---------------------------------------------------------------------------
def load():
    df = pd.read_csv(os.path.join(OUT, "master.csv"))
    # The master is the FULL descriptive sample; the REGRESSIONS use Charron's
    # cumulative "2nd-final entry" cohort (matches his N).  Table 1 / Appendix 3 read
    # the full master directly.
    if "cohort" in df:
        df = df[df["cohort"] == 1].copy()
    df["period"] = np.where(df["year"] <= 1997, "1975-1997", "1998-2012")

    m1 = pd.read_csv(os.path.join(OUT, "friend_dyads_method1.csv"))
    m1set = set(zip(m1["period"], m1["i"], m1["j"]))
    df["friend_m1"] = [int((p, i, j) in m1set)
                       for p, i, j in zip(df["period"], df["i"], df["j"])]

    # Alternative method 1 = Table 2 with the weak 'a'-linkage members removed
    # (Charron's Table 4 "Alternative Friend Group Method 1").
    m1a = pd.read_csv(os.path.join(OUT, "friend_dyads_method1_alt.csv"))
    m1aset = set(zip(m1a["period"], m1a["i"], m1a["j"]))
    df["friend_m1_alt"] = [int((p, i, j) in m1aset)
                           for p, i, j in zip(df["period"], df["i"], df["j"])]

    m2 = pd.read_csv(os.path.join(OUT, "friend_dyads_method2.csv"))
    m2 = m2[m2["friend_m2"] == 1]                  # keep only SIGNIFICANT dyads
    m2set = set(zip(m2["period"], m2["i"], m2["j"]))
    df["friend_m2"] = [int((p, i, j) in m2set)
                       for p, i, j in zip(df["period"], df["i"], df["j"])]

    # interaction terms
    df["fm1_x_imp"] = df["friend_m1"] * df["imp_i"]
    df["fm1alt_x_imp"] = df["friend_m1_alt"] * df["imp_i"]
    df["fm2_x_imp"] = df["friend_m2"] * df["imp_i"]
    return df


# ---------------------------------------------------------------------------
# 2. Estimation helpers.
# ---------------------------------------------------------------------------
def _prep(df, cols):
    """Drop rows with any missing regressor; return y, X(with const), names."""
    d = df.dropna(subset=cols + ["vote"]).copy()
    X = sm.add_constant(d[cols], has_constant="add")
    return d["vote"].values, X, cols


def run_ols(df, cols):
    y, X, _ = _prep(df, cols)
    m = sm.OLS(y, X).fit(cov_type="HC1")          # Huber-White robust SE
    return {"kind": "OLS", "params": m.params, "bse": m.bse,
            "nobs": int(m.nobs), "r2": m.rsquared, "names": list(X.columns)}


def run_tobit(df, cols):
    y, X, _ = _prep(df, cols)
    r = tobit(y, X.values, list(X.columns), upper=12.0)
    params = pd.Series(r.params, index=r.names)
    bse = pd.Series(r.bse, index=r.names)
    return {"kind": "Tobit", "params": params, "bse": bse,
            "nobs": r.nobs, "sigma": r.sigma, "names": r.names}


def stars(p):
    return "***" if p < .01 else "**" if p < .05 else "*" if p < .10 else ""


def fmt_model(res, wanted):
    """Format one model's coefficients for the console table."""
    from scipy import stats
    out = {}
    for name in wanted:
        if name in res["params"].index:
            b = res["params"][name]; se = res["bse"][name]
            z = b / se
            p = 2 * (1 - stats.norm.cdf(abs(z)))
            out[name] = f"{b:.3f}{stars(p)} ({se:.3f})"
        else:
            out[name] = ""
    out["N"] = str(res["nobs"])
    out["type"] = res["kind"]
    return out


# ---------------------------------------------------------------------------
# 3. Table 3.
# ---------------------------------------------------------------------------
# Base controls.  Duet/Group/Female (authoritative Wikidata performer lookup) and
# Diaspora (Charron Appendix 2) were previously unavailable; they are now recovered
# and included, so this reproduces Charron's full Table 3/4 control set.
BASE = ["quality", "friend_m1", "imp_i", "fm1_x_imp",
        "english", "french", "duet", "group", "female", "song_order", "host",
        "contig", "language", "n_part"]


def table3(df):
    specs = [
        ("1 OLS all",      "ols", df,                         BASE),
        ("2 OLS 75-97",    "ols", df[df.year <= 1997],        BASE),
        ("3 OLS 98-12",    "ols", df[df.year >= 1998],        BASE),
        ("4 OLS 98-12+Dia","ols", df[df.year >= 1998],        BASE + ["diaspora"]),
        ("5 OLS +lagIJ",   "ols", df,                         BASE + ["lag_vote_ij"]),
        ("6 OLS +lagJI",   "ols", df,                         BASE + ["lag_vote_ji"]),
        ("7 Tobit +lagIJ", "tob", df,                         BASE + ["lag_vote_ij"]),
        ("8 Tobit +lagJI", "tob", df,                         BASE + ["lag_vote_ji"]),
        ("9 ~RE Tobit IJ", "tob", df,                         BASE + ["lag_vote_ij"]),
        ("10 ~RE Tobit JI","tob", df,                         BASE + ["lag_vote_ji"]),
    ]
    results, labels = [], []
    for lab, kind, d, cols in specs:
        res = run_ols(d, cols) if kind == "ols" else run_tobit(d, cols)
        results.append(res); labels.append(lab)

    _print_table(results, labels,
                 title="Table 3. Impact of friend dyads and impartiality on ESC voting.",
                 fname="table3.txt",
                 rows=["quality", "friend_m1", "imp_i", "fm1_x_imp",
                       "english", "french", "duet", "group", "female", "diaspora",
                       "song_order", "host",
                       "contig", "language", "lag_vote_ij", "lag_vote_ji",
                       "n_part", "const"])
    return results


# ---------------------------------------------------------------------------
# 4. Table 4 -- alternative friend measure (method 2) and voting-rule subsets.
#    Voting rules: jury only = 1975-1997; televote only = 1998-2008;
#    hybrid = 2009-2012.  We report both friend definitions (method 1 & 2).
# ---------------------------------------------------------------------------
def table4(df):
    def m2base(extra=()):
        return ["quality", "friend_m2", "imp_i", "fm2_x_imp",
                "english", "french", "duet", "group", "female", "song_order", "host",
                "contig", "language", "n_part"] + list(extra)

    subsets = {
        "all":     df,
        "jury":    df[df.year <= 1997],
        "tele":    df[(df.year >= 1998) & (df.year <= 2008)],
        "hybrid":  df[df.year >= 2009],
    }
    # Charron's Table 4 "Alternative Friend Group Method 1" = Table 2 with the
    # weak 'a' members removed (friend_m1_alt), not the full method-1 measure.
    base_alt = ["quality", "friend_m1_alt", "imp_i", "fm1alt_x_imp",
                "english", "french", "duet", "group", "female", "song_order", "host",
                "contig", "language", "n_part"]
    specs = [
        ("M2 all",   m2base(), subsets["all"]),
        ("M2 jury",  m2base(), subsets["jury"]),
        ("M2 tele",  m2base(), subsets["tele"]),
        ("M2 hybrid",m2base(), subsets["hybrid"]),
        ("M2 98+Dia",m2base(extra=["diaspora"]), df[df.year >= 1998]),  # Charron model-4 (diaspora, televote era)
        ("M1alt all",   base_alt, subsets["all"]),
        ("M1alt jury",  base_alt, subsets["jury"]),
        ("M1alt tele",  base_alt, subsets["tele"]),
        ("M1alt hybrid",base_alt, subsets["hybrid"]),
    ]
    results, labels = [], []
    for lab, cols, d in specs:
        results.append(run_tobit(d, cols)); labels.append(lab)

    _print_table(results, labels,
                 title="Table 4. Robustness: friend measures x voting rules (pooled Tobit).",
                 fname="table4.txt",
                 rows=["quality", "friend_m2", "friend_m1_alt", "imp_i",
                       "fm2_x_imp", "fm1alt_x_imp", "duet", "group", "female",
                       "diaspora", "const"])
    return results


# ---------------------------------------------------------------------------
# 5. Fig. 3 -- marginal effect of friend voting over song quality, by
#    impartiality (low = mean-1sd, high = mean+1sd) and friend status (0/1),
#    from the Table-3 model 9 coefficients.
# ---------------------------------------------------------------------------
def fig3(df, model9):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = model9["params"]
    q0 = df["quality"].mean()
    qs = df["quality"].std()
    qgrid = np.linspace(q0, q0 + 2 * qs, 50)      # mean to +2 s.d.
    imp_lo = df["imp_i"].mean() - df["imp_i"].std()
    imp_hi = df["imp_i"].mean() + df["imp_i"].std()

    # means of the remaining controls, held constant.
    def base_pred(friend, imp):
        val = p.get("const", 0)
        val += p.get("quality", 0) * qgrid
        val += p.get("friend_m1", 0) * friend
        val += p.get("imp_i", 0) * imp
        val += p.get("fm1_x_imp", 0) * friend * imp
        for c in ["english", "french", "song_order", "host",
                  "contig", "language", "n_part", "lag_vote_ij"]:
            if c in p.index:
                val += p[c] * df[c].mean()
        return np.clip(val, 0, 12)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(qgrid, base_pred(0, imp_lo), "k--", label="low impartiality, F.D.=0")
    ax.plot(qgrid, base_pred(1, imp_lo), "k-o", ms=3, label="low impartiality, F.D.=1")
    ax.plot(qgrid, base_pred(0, imp_hi), "k-x", ms=4, label="high impartiality, F.D.=0")
    ax.plot(qgrid, base_pred(1, imp_hi), "k-", label="high impartiality, F.D.=1")
    ax.set_xlabel("Song quality of country j")
    ax.set_ylabel("Predicted vote i -> j")
    ax.set_title("Fig. 3. Marginal effect of friend voting on bias, conditioned by impartiality")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_marginal_effects.png"), dpi=150)
    plt.close(fig)
    print("Fig 3 saved -> output/fig3_marginal_effects.png")


# ---------------------------------------------------------------------------
# Pretty console/file printer shared by Table 3 and Table 4.
# ---------------------------------------------------------------------------
def _print_table(results, labels, title, fname, rows, out_dir=None):
    cols = [fmt_model(r, rows) for r in results]
    width = max(len(r) for r in rows) + 2
    lines = [title, ""]
    header = " " * width + "".join(f"{lab:<22}" for lab in labels)
    lines.append(header)
    for name in rows:
        line = f"{name:<{width}}" + "".join(f"{c.get(name,''):<22}" for c in cols)
        lines.append(line)
    lines.append(f"{'N':<{width}}" + "".join(f"{c['N']:<22}" for c in cols))
    lines.append(f"{'model':<{width}}" + "".join(f"{c['type']:<22}" for c in cols))
    lines.append("\nSignif: *** p<.01, ** p<.05, * p<.10.  SE in parentheses.")
    txt = "\n".join(lines)
    print("\n" + txt)
    with open(os.path.join(out_dir or OUT, fname), "w") as f:
        f.write(txt + "\n")


def main():
    df = load()
    # Export the fully-merged, regression-ready frame so the R script
    # (regressions.R, using AER::tobit) can reproduce Tables 3-4 independently.
    df.to_csv(os.path.join(OUT, "regression_data.csv"), index=False)
    res3 = table3(df)
    table4(df)
    fig3(df, res3[8])            # model 9
    print("\nNOTE: Duet/Group/Female song traits and Diaspora are not in the data "
          "folder and are omitted; English/French are heuristic; RE-Tobit is "
          "approximated by pooled Tobit. See script docstring.")


if __name__ == "__main__":
    main()
