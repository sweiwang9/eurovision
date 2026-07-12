"""
compare_sources.py
==================
Diff the freshly-scraped eschome data (output/votes_eschome.csv) against the
bundled votes.csv, on the overlapping FINAL dyad-years, and summarise where the
two sources disagree.  This is the input to a manual/official verification step
(eurovision.tv) to decide which source is correct.

Writes:
  output/source_mismatches.csv   -- every disagreeing (year,i,j) with both values
  and prints a summary by year + a sample of the largest discrepancies.
"""

import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.dirname(HERE)
OUT = os.path.join(HERE, "output")


def load_final(path, year_col="year"):
    d = {}
    with open(path, encoding="utf-8", errors="ignore") as f:
        for r in csv.DictReader(f):
            if r.get("round") != "final" or not r.get(year_col):
                continue
            if r.get("total_points") in ("", None):
                continue
            key = (int(r[year_col]), r["from_country_id"], r["to_country_id"])
            d[key] = int(float(r["total_points"]))
    return d


def main():
    bundled = load_final(os.path.join(DATA, "votes.csv"))
    esc = load_final(os.path.join(OUT, "votes_eschome.csv"))

    common = set(bundled) & set(esc)
    only_b = set(bundled) - set(esc)
    only_e = set(esc) - set(bundled)
    mism = [(k, bundled[k], esc[k]) for k in common if bundled[k] != esc[k]]
    mism.sort(key=lambda x: -abs(x[1] - x[2]))

    print(f"bundled final dyads : {len(bundled):,}")
    print(f"eschome final dyads : {len(esc):,}")
    print(f"overlap             : {len(common):,}")
    print(f"only in bundled     : {len(only_b):,}")
    print(f"only in eschome     : {len(only_e):,}")
    print(f"value mismatches    : {len(mism):,} "
          f"({100*len(mism)/max(len(common),1):.2f}% of overlap)")

    # mismatches by year
    by_year = defaultdict(int)
    for (y, _, _), _, _ in mism:
        by_year[y] += 1
    if by_year:
        print("\nmismatches by year:")
        for y in sorted(by_year):
            print(f"  {y}: {by_year[y]}")

    print("\nlargest 15 discrepancies (year, i->j, bundled, eschome):")
    for (y, i, j), b, e in mism[:15]:
        print(f"  {y} {i}->{j}: bundled={b}  eschome={e}  (|d|={abs(b-e)})")

    with open(os.path.join(OUT, "source_mismatches.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "from", "to", "bundled_total", "eschome_total", "abs_diff"])
        for (y, i, j), b, e in mism:
            w.writerow([y, i, j, b, e, abs(b - e)])
    # also record coverage gaps for context
    with open(os.path.join(OUT, "source_coverage_gaps.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "from", "to", "present_in"])
        for (y, i, j) in sorted(only_b):
            w.writerow([y, i, j, "bundled_only"])
        for (y, i, j) in sorted(only_e):
            w.writerow([y, i, j, "eschome_only"])
    print("\nwrote output/source_mismatches.csv and output/source_coverage_gaps.csv")


if __name__ == "__main__":
    main()
