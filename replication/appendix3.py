"""
appendix3.py
============
Replicate Appendix 3:

  Part A -- "Test of within-group bias by friend dyads and groups: averaged over
            time periods."  For each friend group (Table 2) we regress the within
            group dyad bias on a group dummy with no constant, i.e. we estimate
            the group's mean bias (beta) and test it against 0 (Huber-White SE).

  Part B -- "Stability of bias by group over time ... by year 1998-2012."  For
            each 1998-2012 group we report the average within-group bias in each
            year plus the overall average ('Ave.Total').

A positive, significant beta means countries inside the group systematically
over-vote for one another -- the paper's evidence that the blocs are real.
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")

PERIODS = [("1975-1997", 1975, 1997), ("1998-2012", 1998, 2012)]


def within_group_bias(df, groups_df, lo, hi):
    """Return, per group, the list of within-group directed dyad-year biases."""
    # map country code -> group id for this period
    code2grp = dict(zip(groups_df["code"], groups_df["group"]))
    sub = df[(df["year"] >= lo) & (df["year"] <= hi)].copy()
    sub["gi"] = sub["i"].map(code2grp)
    sub["gj"] = sub["j"].map(code2grp)
    # keep dyads whose voter and receiver are in the SAME group (and not self)
    win = sub[(sub["gi"] == sub["gj"]) & sub["gi"].notna() & (sub["i"] != sub["j"])]
    return win.groupby("gi")["bias"]


def part_a(df):
    lines = ["Appendix 3 (Part A). Test of within-group bias (beta = mean bias).\n"]
    for label, lo, hi in PERIODS:
        g = pd.read_csv(os.path.join(OUT, f"friend_groups_{label}.csv"))
        grouped = within_group_bias(df, g, lo, hi)
        lines.append(f"\n=== {label} ===")
        lines.append(f"{'Group':<8}{'Beta':>8}{'p-value':>10}{'N':>7}   members")
        # readable member string per group
        members = (g.groupby("group")["country"].apply(lambda s: ", ".join(s)))
        for grp, b in grouped:
            b = b.values
            if len(b) < 2:
                continue
            beta = b.mean()
            p = (stats.ttest_1samp(b, 0).pvalue if not np.allclose(b, b[0])
                 else (0.0 if abs(beta) > 1e-9 else 1.0))
            lines.append(f"{grp:<8}{beta:>8.2f}{p:>10.3f}{len(b):>7}   {members.get(grp,'')}")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(OUT, "appendix3_partA.txt"), "w") as f:
        f.write(txt + "\n")


def part_b(df):
    label, lo, hi = "1998-2012", 1998, 2012
    g = pd.read_csv(os.path.join(OUT, f"friend_groups_{label}.csv"))
    code2grp = dict(zip(g["code"], g["group"]))
    sub = df[(df["year"] >= lo) & (df["year"] <= hi)].copy()
    sub["gi"] = sub["i"].map(code2grp); sub["gj"] = sub["j"].map(code2grp)
    win = sub[(sub["gi"] == sub["gj"]) & sub["gi"].notna() & (sub["i"] != sub["j"])]

    # average within-group bias by year, plus overall average.
    tab = win.groupby(["gi", "year"])["bias"].mean().unstack()
    tab["Ave.Total"] = win.groupby("gi")["bias"].mean()
    tab = tab.round(1)
    tab.to_csv(os.path.join(OUT, "appendix3_partB_stability.csv"))
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print("\nAppendix 3 (Part B). Within-group average bias by year 1998-2012:")
        print(tab)


def main():
    df = pd.read_csv(os.path.join(OUT, "master.csv"))
    part_a(df)
    part_b(df)


if __name__ == "__main__":
    main()
