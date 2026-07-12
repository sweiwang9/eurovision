"""
table1.py
=========
Replicate Table 1: "Top 10 most bias dyads pre and post televoting."

The paper splits the sample at the spread of televoting (1998) and, within each
period, averages each ordered dyad's bias (eq. 2) over the years it occurred,
keeping dyads observed at least a few times, then lists the 10 largest.

SAMPLE: Table 1 is DESCRIPTIVE, so it uses the FULL master (every dyad-year among
countries with >=2 finals) -- NOT the regression's cumulative "2nd-final entry"
cohort.  Applying the regression cohort here would wrongly drop each dyad's early
years and push many pairs below the observation floor; on the full sample the
biases reproduce Charron's to the decimal.

MIN_OBS = 3: Charron's note is "a: Pair contains only 2 observations, all others
contain 3 or more" -- i.e. his list is essentially n>=3 with a single flagged n=2
exception (Malta->Slovakia).  We tried n>=2, but our data has many high-bias n=1/2
dyads in the sparse jury era (relegation years -> few co-final appearances) that
Charron's list does not, so n>=2 floods the table with noise pairs.  n>=3 gives the
clean, Charron-like list; the one n=2 pair he flags is simply outside a uniform
n>=3 rule (a top-10-of-small-n-averages is inherently noisy in the tail).
"""

import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")

MIN_OBS = 3


def top_dyads(df, lo, hi, n=10):
    """Average bias per ordered dyad in [lo, hi]; return the n largest."""
    sub = df[(df["year"] >= lo) & (df["year"] <= hi)]
    g = sub.groupby(["i", "j"]).agg(bias=("bias", "mean"),
                                    n=("bias", "size")).reset_index()
    g = g[g["n"] >= MIN_OBS].sort_values("bias", ascending=False).head(n)
    return g


def main():
    df = pd.read_csv(os.path.join(OUT, "master.csv"))   # FULL sample (ignore cohort)
    from lib_countries import NAME

    periods = [("1975-1997", 1975, 1997), ("1998-2012", 1998, 2012)]
    lines = ["Table 1. Top 10 most bias dyads pre and post televoting.\n"]
    frames = []
    for label, lo, hi in periods:
        t = top_dyads(df, lo, hi)
        lines.append(f"\n=== {label} ===")
        lines.append(f"{'Rank':<5}{'Voter':<22}{'Receiver':<22}{'Bias':>6}{'N':>5}")
        for rank, (_, row) in enumerate(t.iterrows(), 1):
            lines.append(f"{rank:<5}{NAME[row['i']]:<22}{NAME[row['j']]:<22}"
                         f"{row['bias']:>6.1f}{int(row['n']):>5}")
        t.insert(0, "period", label)
        frames.append(t)

    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(OUT, "table1.txt"), "w") as f:
        f.write(txt + "\n")
    pd.concat(frames).to_csv(os.path.join(OUT, "table1.csv"), index=False)


if __name__ == "__main__":
    main()
