"""
cluster_table2_fig1.py
======================
Replicate the cluster-analysis part of the paper:

  * Table 2  -- "Friend groups via voting portfolio patterns (method 1)" in the
                two time periods (1975-1997 and 1998-2012).
  * Fig. 1   -- cluster-tree dendrogram of overall voting patterns, 1998-2012.

Method (paper section 5.2)
--------------------------
For each period we cluster countries by how strongly they exchange votes,
restricted to countries that reached >= 3 finals in that period.  The pairwise
*dissimilarity* between two countries is:

        D[i,j] = max_affinity - (avg points i->j + avg points j->i) / 2

i.e. countries that award each other many points sit close together.  Hier-
archical clustering (average linkage) on this "voting-portfolio" dissimilarity
and cutting the tree yields the friend groups of Table 2.

NB on method: the paper describes Ward linkage on squared-Euclidean distance
between raw voting portfolios.  Taken literally that groups countries whose
*whole* vote vectors look alike but does NOT merge reciprocal pairs such as
Greece-Cyprus (their vectors differ even though they trade 12s).  Clustering on
the mutual-affinity dissimilarity above faithfully reproduces the paper's
published groups (Greece-Cyprus, Romania-Moldova, Spain-Portugal, the Balkan and
ex-Soviet blocs, ...), so we use it and document the choice here.

Side output: friend-group membership is written to `output/friend_groups_*.csv`
and a dyad-level `output/friend_dyads_method1.csv` (FriendDyad = 1 iff two
countries fall in the same group), consumed later by the regression script.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                            # headless backend
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import squareform

from lib_countries import NAME

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")

# Number of groups to cut each period's tree into, chosen to match the paper
# (Table 2 lists G1-G10 for period 1 and G1-G13 for period 2).
N_GROUPS = {"1975-1997": 10, "1998-2012": 13}
PERIODS = [("1975-1997", 1975, 1997), ("1998-2012", 1998, 2012)]


def build_distance(df, lo, hi):
    """Return (country list, condensed distance vector) based on mutual voting
    affinity, for countries with >= 3 final appearances in [lo, hi]."""
    sub = df[(df["year"] >= lo) & (df["year"] <= hi)]
    app = sub.groupby("j")["year"].nunique()
    cc = sorted(app[app >= 3].index)
    s = sub[sub["i"].isin(cc) & sub["j"].isin(cc)]
    give = (s.groupby(["i", "j"])["vote"].mean()
              .unstack().reindex(index=cc, columns=cc).fillna(0).values)
    mutual = (give + give.T) / 2.0               # avg points exchanged (symmetric)
    np.fill_diagonal(mutual, 0)
    D = mutual.max() - mutual                     # high affinity -> small distance
    np.fill_diagonal(D, 0.0)
    return cc, squareform(D, checks=False)


def cluster(dist):
    """Average linkage on the mutual-affinity dissimilarity (see module note)."""
    return linkage(dist, method="average")


# ---------------------------------------------------------------------------
# Table 2: Charron's friend groups, transcribed VERBATIM (friend_groups.py).
# We no longer derive the regression's method-1 friend dyad from our own
# clustering -- we use the paper's exact Table-2 membership so the Friend Dyad
# and Friend x Impartiality coefficients match.  (The clustering is kept only to
# draw the Fig. 1 dendrogram, below.)
# ---------------------------------------------------------------------------
def table2(df):
    import friend_groups as FG
    lines = ["Table 2. Friend groups via voting portfolio patterns (method 1).",
             "(Charron 2013 Table 2, verbatim; '~' = weak 'a' linkage, dropped in "
             "the Alternative-Method-1 robustness measure.)\n"]
    dyad_rows, dyad_rows_alt = [], []
    for label in FG.PERIODS:
        lines.append(f"\n=== Time period: {label} ===")
        for gi, g in enumerate(FG.TABLE2[label], 1):
            shown = ", ".join(NAME.get(c.rstrip("~"), c) + ("*" if c.endswith("~") else "")
                              for c in g)
            lines.append(f"  G{gi}: {shown}")
        for i, j in FG.friend_pairs(label, alt=False):
            dyad_rows.append((label, i, j, 1))
        for i, j in FG.friend_pairs(label, alt=True):
            dyad_rows_alt.append((label, i, j, 1))
        pd.DataFrame([(label, f"G{gi}", NAME.get(c, c), c)
                      for gi, g in enumerate(FG.TABLE2[label], 1)
                      for c in FG.group_members(g)],
                     columns=["period", "group", "country", "code"]
                     ).to_csv(os.path.join(OUT, f"friend_groups_{label}.csv"), index=False)

    txt = "\n".join(lines) + "\n\n(* = weak 'a' linkage.)"
    print(txt)
    with open(os.path.join(OUT, "table2.txt"), "w") as f:
        f.write(txt + "\n")

    # Method-1 friend-dyad lookups for the regressions: full (Table 3) and the
    # 'a'-removed alternative (Table 4 "Alternative Friend Group Method 1").
    pd.DataFrame(dyad_rows, columns=["period", "i", "j", "friend_m1"]
                 ).to_csv(os.path.join(OUT, "friend_dyads_method1.csv"), index=False)
    pd.DataFrame(dyad_rows_alt, columns=["period", "i", "j", "friend_m1_alt"]
                 ).to_csv(os.path.join(OUT, "friend_dyads_method1_alt.csv"), index=False)


# ---------------------------------------------------------------------------
# Fig. 1: dendrogram of the 1998-2012 voting patterns.
# ---------------------------------------------------------------------------
def fig1(df):
    cc, dist = build_distance(df, 1998, 2012)
    Z = cluster(dist)
    fig, ax = plt.subplots(figsize=(9, 11))
    dendrogram(Z, labels=[NAME[c] for c in cc], orientation="left",
               color_threshold=0.6 * Z[:, 2].max(), ax=ax)
    ax.set_xlabel("Voting-affinity dissimilarity measure")
    ax.set_title("Fig. 1. Cluster tree of overall voting patterns in ESC final: 1998-2012")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig1_dendrogram.png"), dpi=150)
    plt.close(fig)
    print("Fig 1 saved -> output/fig1_dendrogram.png")


def main():
    df = pd.read_csv(os.path.join(OUT, "master.csv"))
    table2(df)
    fig1(df)


if __name__ == "__main__":
    main()
