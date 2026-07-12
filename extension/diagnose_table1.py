"""
diagnose_table1.py
==================
Forensic check of why Table 1's numbers are hard to reproduce.

We now KNOW the vote values are correct (scraped eschome == bundled == official),
so any gap must come from the Quality/Bias *computation* or the *sample of years*.
This script:
  1. reproduces the paper's Table-1 dyads under our current method and prints the
     per-dyad bias + n for both periods, next to the paper's published value;
  2. prints a full year-by-year breakdown for the worst offender (Greece->Cyprus)
     under several candidate Quality definitions, so we can see exactly which
     years and which formula drive the difference.
"""

import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
VOTES = os.path.join(OUT, "votes_eschome.csv")   # the verified source

# Paper Table 1 published values (voter, receiver, bias).
PAPER = {
    "1975-1997": [("mt","sk",9.5),("cy","gr",9.1),("gr","cy",7.1),("tr","ba",6.7),
                  ("hr","mt",5.6),("si","ru",5.1),("ee","fr",4.6),("nl","ru",4.5),
                  ("fi","it",3.6),("pl","hu",3.5)],
    "1998-2012": [("ro","md",9.6),("mk","al",9.4),("md","ro",9.2),("gr","cy",9.0),
                  ("az","tr",8.5),("rs","mk",8.5),("fr","pt",8.2),("tr","az",8.0),
                  ("it","ro",7.9),("lt","ge",7.8)],
}


def load_finalists():
    """EXPLICIT finalist roster per year, from finalists_eschome.csv (scraped
    from the scoreboard) -- a country that PERFORMED in the final, regardless of
    how many points it scored.  This is the authoritative identification and does
    NOT rely on a country having received points."""
    fin = defaultdict(set)
    with open(os.path.join(OUT, "finalists_eschome.csv")) as f:
        for r in csv.DictReader(f):
            fin[int(r["year"])].add(r["country_id"])
    return fin


def load(finalists_only=True):
    """Return list of (year,i,j,vote) finals; optionally restricted to
    finalist->finalist dyads using the EXPLICIT finalist roster."""
    fin = load_finalists()
    rows = []
    with open(VOTES) as f:
        for r in csv.DictReader(f):
            if r["round"] != "final":
                continue
            y = int(r["year"]); i = r["from_country_id"]; j = r["to_country_id"]
            if i == "xx":                        # exclude Rest-of-World giver here
                continue
            if finalists_only and (i not in fin[y] or j not in fin[y]):
                continue
            rows.append((y, i, j, float(r["total_points"])))
    return rows


def quality_variants(rows):
    """Precompute, per (year), the pieces needed for several quality defs."""
    part = defaultdict(set); total = defaultdict(float); ngiv = defaultdict(int)
    for y, i, j, v in rows:
        part[y].add(i); part[y].add(j)
        total[(y, j)] += v; ngiv[(y, j)] += 1
    return part, total, ngiv


def bias_for(rows, dyads, qdef):
    part, total, ngiv = quality_variants(rows)
    out = {}
    series = defaultdict(list)
    for y, i, j, v in rows:
        p = len(part[y])
        T = total[(y, j)]; ng = ngiv[(y, j)]
        if qdef == "D1":   q = (T - v) / (p - 2)          # dyad-specific, p-2  [current]
        elif qdef == "D2": q = T / (p - 1)                 # simple avg over field
        elif qdef == "D3": q = (T - v) / (ng - 1) if ng > 1 else 0   # dyad, actual givers
        elif qdef == "D4": q = T / (p - 2)                 # total / (p-2), no subtract
        else: q = (T - v) / (p - 2)
        series[(i, j)].append((y, v, q, v - q))
    for (i, j) in dyads:
        s = series.get((i, j), [])
        if s:
            out[(i, j)] = (sum(x[3] for x in s) / len(s), len(s), s)
    return out


def main():
    rows = load(finalists_only=True)
    for period, lo, hi in [("1975-1997", 1975, 1997), ("1998-2012", 1998, 2012)]:
        sub = [r for r in rows if lo <= r[0] <= hi]
        dyads = [(i, j) for i, j, _ in PAPER[period]]
        res = bias_for(sub, dyads, "D1")
        print(f"\n=== {period}: paper vs reproduced (D1 = current method) ===")
        print(f"{'dyad':10}{'paper':>7}{'mine':>7}{'diff':>7}{'n':>4}")
        for i, j, pv in PAPER[period]:
            b, n, _ = res.get((i, j), (float('nan'), 0, []))
            print(f"{i+'->'+j:10}{pv:>7.1f}{b:>7.1f}{b-pv:>+7.1f}{n:>4}")

    # Year-by-year forensic for Greece->Cyprus 1998-2012 under 4 quality defs.
    sub = [r for r in rows if 1998 <= r[0] <= 2012]
    print("\n=== Greece->Cyprus 1998-2012: year-by-year ===")
    print(f"{'year':6}{'vote':>5}{'Total_cy':>9}{'p':>4}{'ngiv':>5}"
          f"{'D1 bias':>9}{'D2 bias':>9}{'D4 bias':>9}")
    part, total, ngiv = quality_variants(sub)
    accum = defaultdict(list)
    for y, i, j, v in sorted(sub):
        if i == "gr" and j == "cy":
            p = len(part[y]); T = total[(y, j)]; ng = ngiv[(y, j)]
            d1 = v - (T - v)/(p-2); d2 = v - T/(p-1); d4 = v - T/(p-2)
            accum["D1"].append(d1); accum["D2"].append(d2); accum["D4"].append(d4)
            print(f"{y:<6}{v:>5.0f}{T:>9.0f}{p:>4}{ng:>5}{d1:>9.2f}{d2:>9.2f}{d4:>9.2f}")
    for k in ["D1", "D2", "D4"]:
        print(f"  mean {k}: {sum(accum[k])/len(accum[k]):.2f}   (paper 8.5)")


if __name__ == "__main__":
    main()
