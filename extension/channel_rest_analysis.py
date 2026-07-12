"""
channel_rest_analysis.py
========================
Two analyses beyond the main extension:

(A) JURY-CHANNEL vs PUBLIC-CHANNEL panels.  Charron's DV is a single 0-12 vote,
    but the "voice" behind it changes by era.  Here we pool the vote across ALL
    years in which each voice is cleanly observed:
      * JURY channel   = 1975-1997 (juries were the whole vote) + 2016-2026 (the
                         jury HALF).  [1998-2015 has no separable jury signal.]
      * PUBLIC channel = 1998-2008 (100% televote) + 2016-2026 (televote HALF).
                         [1975-1997 has no public vote; 2009-2015 is a combined
                          jury+televote score, not separable, so it is excluded.]
    Quality (eq.1) and Bias (eq.2) are recomputed on each channel's DV, friend
    dyads = Charron Table 2, impartiality = ICRG.  We then re-estimate Charron's
    Friend x Impartiality test on each channel -- does the moderation hold for
    juries?  for publics?  -- pooled and split into the early / split-era halves.

(B) REST-OF-WORLD ("XX") benchmark.  Since 2023 an aggregate global online
    televote ("Rest of the World", giver code XX) awards a normal 0-12 set but has
    NO nationality, impartiality, friend group or diaspora.  It is therefore a
    natural "impartial voter" benchmark: does it reward song quality and refrain
    from the bloc/diaspora bias that national electorates show?

Builds the panels in Python and EXPORTS them; `channel_rest_regressions.R`
estimates them in R (AER::tobit), the authoritative estimator.
"""

import os
import sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
REPL = os.path.join(os.path.dirname(HERE), "replication")
sys.path.insert(0, REPL)

import friend_groups as FG
from lib_countries import alias
from diaspora import diaspora
from pairwise_bias import directed_bias

PERIODS = {"1975-1997": (1975, 1997), "1998-2026": (1998, 2026)}


def _recompute(df):
    """Recompute dyad-specific Quality (eq.1) / Bias (eq.2) / lags on df['vote']."""
    part = df.groupby("year").apply(
        lambda g: len(set(g["i"]) | set(g["j"])), include_groups=False)
    total = df.groupby(["year", "j"])["vote"].sum().rename("total_j")
    df = df.drop(columns=[c for c in ["total_j"] if c in df]).merge(total, on=["year", "j"])
    df["n_part"] = df["year"].map(part)
    df["quality"] = (df["total_j"] - df["vote"]) / (df["n_part"] - 2)
    df["bias"] = df["vote"] - df["quality"]
    vm = {(y, i, j): v for y, i, j, v in zip(df["year"], df["i"], df["j"], df["vote"])}
    df["lag_vote_ij"] = [vm.get((y - 1, i, j), np.nan) for y, i, j in zip(df["year"], df["i"], df["j"])]
    return df


def _friend(df):
    """Attach method-1 (Table 2 verbatim) and method-2 (pairwise) friend dyads."""
    t2 = {"1975-1997": "1975-1997", "1998-2026": "1998-2012"}
    m1 = {(p, a, b) for ext, t in t2.items() for a, b in FG.friend_pairs(t)
          for p in [ext]}
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


def load_channel(channel):
    """Build the jury- or public-channel panel with its own 0-12 DV."""
    df = pd.read_csv(os.path.join(OUT, "master_extended.csv"))
    if channel == "jury":
        df = df[(df.year <= 1997) | (df.year >= 2016)].copy()
        df["vote"] = np.where(df.year >= 2016, df["vote_jury"], df["vote"])
    elif channel == "public":
        df = df[((df.year >= 1998) & (df.year <= 2008)) | (df.year >= 2016)].copy()
        df["vote"] = np.where(df.year >= 2016, df["vote_tele"], df["vote"])
    else:
        raise ValueError(channel)
    df = df.dropna(subset=["vote"]).copy()
    df = _recompute(df)
    df["period"] = np.where(df["year"] <= 1997, "1975-1997", "1998-2026")
    if "cohort" in df:
        df = df[df["cohort"] == 1].copy()
    df = _friend(df)
    return df


# ---------------------------------------------------------------------------
# (B) Rest-of-World benchmark frame.
# ---------------------------------------------------------------------------
def load_rest_of_world():
    """2023-2026 PUBLIC (televote) dyads: national voters (vote_tele) + XX, each
    with the receiver's national televote-quality, so XX sits on the same 0-12
    public scale.  Adds is_xx, bias, diaspora, and whether the receiver is in a
    friend bloc (a 'friend magnet')."""
    v = pd.read_csv(os.path.join(OUT, "votes_eschome.csv"))
    v = v[(v["round"] == "final") & (v.year >= 2023)].copy()
    v["i"] = v["from_country_id"].map(alias)
    v["j"] = v["to_country_id"].map(alias)
    v = v[v["i"] != v["j"]]
    # public points: televote half (2023+ are split years, tele_points populated);
    # XX has only tele_points.
    v["pub"] = v["tele_points"]
    v = v.dropna(subset=["pub"]).copy()
    # national televote-quality of receiver j (exclude XX so the benchmark is the
    # national public consensus): mean national tele points to j that year.
    nat = v[v["i"] != "xx"]
    part = nat.groupby("year")["i"].nunique()
    tot = nat.groupby(["year", "j"])["pub"].sum().rename("tot_j")
    v = v.merge(tot, on=["year", "j"])
    v["p"] = v["year"].map(part)
    # quality excludes the voter's own point only for nationals; XX is not in the
    # national total, so subtract only when i is national.
    own = np.where(v["i"] == "xx", 0.0, v["pub"])
    v["quality"] = (v["tot_j"] - own) / (v["p"] - 1 - np.where(v["i"] == "xx", 0, 1))
    v["bias"] = v["pub"] - v["quality"]
    v["is_xx"] = (v["i"] == "xx").astype(int)
    v["diaspora"] = [0 if i == "xx" else diaspora(i, j) for i, j in zip(v["i"], v["j"])]
    # receiver is a "friend magnet": in any 1998-2012 Table-2 friend group
    bloc = set()
    for g in FG.groups("1998-2012"):
        bloc |= set(g)
    v["recv_bloc"] = v["j"].isin(bloc).astype(int)
    return v[["year", "i", "j", "pub", "quality", "bias", "is_xx", "diaspora", "recv_bloc"]]


def main():
    j = load_channel("jury")
    p = load_channel("public")
    row = load_rest_of_world()
    j.to_csv(os.path.join(OUT, "regression_data_jurychannel.csv"), index=False)
    p.to_csv(os.path.join(OUT, "regression_data_pubchannel.csv"), index=False)
    row.to_csv(os.path.join(OUT, "regression_data_rowvote.csv"), index=False)
    print(f"JURY channel:   {len(j):5} dyad-years "
          f"({j.year.min()}-{j.year.max()}); friend dyads {int(j.friend_m1.sum())}")
    print(f"PUBLIC channel: {len(p):5} dyad-years "
          f"({p.year.min()}-{p.year.max()}); friend dyads {int(p.friend_m1.sum())}")
    print(f"Rest-of-World:  {len(row):5} public dyads 2023-2026 "
          f"({int(row.is_xx.sum())} are XX)")


if __name__ == "__main__":
    main()
