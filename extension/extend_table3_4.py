"""
extend_table3_4.py
=================
Re-estimate Charron's Table 3 & Table 4 on the EXTENDED panel (1975-2026) to test
whether the finding -- impartiality offsets friend-voting bias (Friend x
Impartiality < 0) -- still holds in the later years.

Dependent variable on a consistent 0-12 scale (`vote12`):
  * 1975-2015 : the single 0-12 vote (jury pre-1998; televote/hybrid 1998-2015).
  * 2016-2026 : the 0-12 TELEVOTE component (the public vote), which is the
                continuation of the public preference measured 1998-2015.  (The
                combined 2016+ total is 0-24 and not comparable, so we use the
                public-vote half; a jury-half robustness run is trivial to add.)

Everything else follows the replication: eschome data with fn.18 ever-finalist
givers and cumulative ">=2 finals" entry (shared build_dataset.py); dyad-specific
Quality (eq.1)/Bias (eq.2) recomputed on `vote12`; Friend Dyads by method 1
(Charron's Table 2, VERBATIM -- the 1998-2026 period uses his 1998-2012 groups)
and method 2 (significant pairwise bias, recomputed on the extended data so it can
pick up post-2012 friendships).

GENUINELY-BETTER DEVIATIONS from the strict replication (this is an extension, not
a faithful reproduction): (a) Impartiality uses ALL available real ICRG plus the
wider hot-deck donor set, so real Balkan voters (Bosnia, etc.) stay in the panel
rather than being dropped; (b) the 0-12 `vote12` DV (televote half for 2016+);
(c) English/French dropped (no 2024-2026 lyrics).
"""

import os
import sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")               # extension artifacts
# Reuse the replication's shared estimators/helpers (they live one folder over).
REPL = os.path.join(os.path.dirname(HERE), "replication")
sys.path.insert(0, REPL)

import friend_groups as FG                        # Charron Table 2 (verbatim)
from pairwise_bias import directed_bias
from regressions_table3_4_fig3 import run_ols, run_tobit, _print_table

PERIODS = {"1975-1997": (1975, 1997), "1998-2026": (1998, 2026)}


# ---------------------------------------------------------------------------
# 1. Build the 0-12 DV and recompute Quality/Bias/lags on it.
# ---------------------------------------------------------------------------
def load(dv2016="tele"):
    """Build the 0-12 DV.  For 2016+ use the televote half (default, the public
    vote, continuous with 1998-2015) or the jury half (robustness check)."""
    df = pd.read_csv(os.path.join(OUT, "master_extended.csv"))
    half = df["vote_tele"] if dv2016 == "tele" else df["vote_jury"]
    df["vote12"] = np.where(df["year"] >= 2016, half, df["vote"])
    df = df.dropna(subset=["vote12"]).copy()
    df["vote"] = df["vote12"]                       # so shared helpers use it

    # dyad-specific quality (eq.1) and bias (eq.2) on the 0-12 vote
    part = df.groupby("year").apply(
        lambda g: len(set(g["i"]) | set(g["j"])), include_groups=False)
    total = df.groupby(["year", "j"])["vote"].sum().rename("total_j")
    df = df.drop(columns=[c for c in ["total_j"] if c in df]).merge(total, on=["year", "j"])
    df["n_part"] = df["year"].map(part)
    df["quality"] = (df["total_j"] - df["vote"]) / (df["n_part"] - 2)
    df["bias"] = df["vote"] - df["quality"]

    # lagged votes on the 0-12 scale
    vm = {(y, i, j): v for y, i, j, v in zip(df["year"], df["i"], df["j"], df["vote"])}
    df["lag_vote_ij"] = [vm.get((y - 1, i, j), np.nan) for y, i, j in zip(df["year"], df["i"], df["j"])]
    df["lag_vote_ji"] = [vm.get((y - 1, j, i), np.nan) for y, i, j in zip(df["year"], df["i"], df["j"])]

    df["period"] = np.where(df["year"] <= 1997, "1975-1997", "1998-2026")
    # Quality/lags were computed on the FULL sample (all voters); the regressions use
    # Charron's cumulative "2nd-final entry" cohort (same rule as the replication).
    if "cohort" in df:
        df = df[df["cohort"] == 1].copy()
    return df


# ---------------------------------------------------------------------------
# 2. Friend dyads, recomputed on the extended data.
# ---------------------------------------------------------------------------
def friend_dyads(df):
    # METHOD 1: Charron's Table 2 friend groups, VERBATIM -- same as the replication
    # (friend_groups.py).  The extended 1998-2026 period uses Charron's 1998-2012
    # friend structure (blocs are slow-moving and Table 2 is the authoritative set);
    # post-2012 entrants not in any Table 2 group (e.g. Australia) have no method-1
    # friends.
    t2_of = {"1975-1997": "1975-1997", "1998-2026": "1998-2012"}
    m1 = set()
    for ext_label, t2_label in t2_of.items():
        for a, b in FG.friend_pairs(t2_label, alt=False):
            m1.add((ext_label, a, b))

    # METHOD 2: significant positive pairwise bias, RECOMPUTED on the extended data.
    # Deliberately kept DATA-DRIVEN (a genuine improvement for the extension): it can
    # capture friendships that emerged after 2012, which frozen Table 2 cannot.
    m2 = set()
    for label, (lo, hi) in PERIODS.items():
        d = directed_bias(df, lo, hi)
        for _, r in d.iterrows():
            if r["sig_pos"]:
                m2.add((label, r["i"], r["j"]))

    df["friend_m1"] = [int((p, i, j) in m1) for p, i, j in zip(df["period"], df["i"], df["j"])]
    df["friend_m2"] = [int((p, i, j) in m2) for p, i, j in zip(df["period"], df["i"], df["j"])]
    df["fm1_x_imp"] = df["friend_m1"] * df["imp_i"]
    df["fm2_x_imp"] = df["friend_m2"] * df["imp_i"]
    return df


# Controls available across 1975-2026 (english/french dropped: no 2024-26 lyrics).
# Duet/Group/Female (authoritative Wikidata performer lookup) and Diaspora (Charron
# Appendix 2) were previously unavailable and are now included -- these are the
# song-trait and diaspora controls the original Table 3/4 carried.
BASE = ["quality", "friend_m1", "imp_i", "fm1_x_imp",
        "song_order", "host", "contig", "language", "n_part",
        "duet", "group", "female"]


def table3(df, suffix="", tag=""):
    specs = [
        ("1 OLS all",     "ols", df,                          BASE),
        ("2 OLS 75-97",   "ols", df[df.year <= 1997],         BASE),
        ("3 OLS 98-26",   "ols", df[df.year >= 1998],         BASE),
        ("4 OLS 16-26",   "ols", df[df.year >= 2016],         BASE),   # split-vote era
        ("5 OLS +lagIJ",  "ols", df,                          BASE + ["lag_vote_ij"]),
        ("6 OLS +lagJI",  "ols", df,                          BASE + ["lag_vote_ji"]),
        ("7 Tobit lagIJ", "tob", df,                          BASE + ["lag_vote_ij"]),
        ("8 Tobit lagJI", "tob", df,                          BASE + ["lag_vote_ji"]),
        ("9 OLS 98-26+dia", "ols", df[df.year >= 1998],       BASE + ["diaspora"]),  # diaspora: televote era
    ]
    results, labels = [], []
    for lab, kind, d, cols in specs:
        results.append(run_ols(d, cols) if kind == "ols" else run_tobit(d, cols))
        labels.append(lab)
    _print_table(results, labels,
                 title=f"Table 3 (EXTENDED 1975-2026{tag}). Friend dyads & impartiality on ESC voting.",
                 fname=f"table3_extended{suffix}.txt",
                 rows=["quality", "friend_m1", "imp_i", "fm1_x_imp", "contig",
                       "language", "duet", "group", "female", "diaspora",
                       "lag_vote_ij", "lag_vote_ji", "song_order",
                       "host", "n_part", "const"],
                 out_dir=OUT)


def table4(df, suffix="", tag=""):
    def m2base(): return ["quality", "friend_m2", "imp_i", "fm2_x_imp",
                          "song_order", "host", "contig", "language", "n_part",
                          "duet", "group", "female"]
    subs = {
        "all":    df,
        "jury":   df[df.year <= 1997],
        "tele":   df[(df.year >= 1998) & (df.year <= 2008)],
        "hybrid": df[(df.year >= 2009) & (df.year <= 2015)],
        "split":  df[df.year >= 2016],
        "tvera":  df[df.year >= 1998],           # televote era: diaspora meaningful
    }
    specs = [("M2 all", m2base(), subs["all"]), ("M2 jury", m2base(), subs["jury"]),
             ("M2 tele", m2base(), subs["tele"]), ("M2 hybrid", m2base(), subs["hybrid"]),
             ("M2 split16-26", m2base(), subs["split"]),
             ("M2 98-26+dia", m2base() + ["diaspora"], subs["tvera"]),   # Charron model-4 analogue
             ("M1 all", BASE, subs["all"]), ("M1 split16-26", BASE, subs["split"])]
    results, labels = [], []
    for lab, cols, d in specs:
        results.append(run_tobit(d, cols)); labels.append(lab)
    _print_table(results, labels,
                 title=f"Table 4 (EXTENDED{tag}). Robustness by friend measure & voting rule (pooled Tobit).",
                 fname=f"table4_extended{suffix}.txt",
                 rows=["quality", "friend_m2", "friend_m1", "imp_i",
                       "fm2_x_imp", "fm1_x_imp", "duet", "group", "female",
                       "diaspora", "const"],
                 out_dir=OUT)


def main():
    # DV for 2016+: 'tele' (default, main analysis) or 'jury' (robustness check).
    dv2016 = "tele"
    if "--dv2016" in sys.argv:
        dv2016 = sys.argv[sys.argv.index("--dv2016") + 1]
    suffix = "" if dv2016 == "tele" else f"_{dv2016}2016"
    tag = "" if dv2016 == "tele" else f"; 2016+ DV = {dv2016.upper()} half"

    df = load(dv2016=dv2016)
    df = friend_dyads(df)
    # Export the regression-ready frame so the authoritative R estimator
    # (extend_regressions.R, AER::tobit) can consume it -- same Python-builds /
    # R-estimates split as the replication.  `vote` here is the 0-12 vote12 DV.
    df.to_csv(os.path.join(OUT, f"regression_data_extended{suffix}.csv"), index=False)
    print(f"Extended panel [2016+ DV = {dv2016}]: {len(df):,} dyad-years, "
          f"{df.year.min()}-{df.year.max()}, {df.j.nunique()} countries.\n")
    table3(df, suffix=suffix, tag=tag)
    table4(df, suffix=suffix, tag=tag)
    note = ("televote for 2016+" if dv2016 == "tele" else
            "JURY for 2016+ (ROBUSTNESS CHECK, does not replace the televote analysis)")
    print(f"\nDV = 0-12 vote, {note}. english/french dropped (no 2024-26 lyrics).")


if __name__ == "__main__":
    main()
