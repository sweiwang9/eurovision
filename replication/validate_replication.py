"""
validate_replication.py
=======================
Phase-0 validation harness for the "exact replication" effort.

Runs the key OLS models on the current master panel and prints, for each, the
sample size and the four hypothesis coefficients side-by-side with Charron's
PUBLISHED Table 3 values, plus a signed difference.  This is the yardstick used
to measure each phase of the convergence toward exact replication.

    python3 validate_replication.py

It reuses the real estimation code (regressions_table3_4_fig3.load / run_ols /
BASE), so it always reflects the live pipeline.  Note: Friend-Dyad magnitudes
will not match until the friend groups are taken verbatim from Table 2
(Phase 3); Phase 1 targets the SAMPLE SIZE (N) first.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import regressions_table3_4_fig3 as R

# Charron (2013), Table 3 -- published coefficients and N for the OLS models.
KEYS = ["quality", "friend_m1", "imp_i", "fm1_x_imp", "diaspora"]
CHARRON = {
    "M1 OLS all  1975-2012":  dict(N=16686, quality=0.90, friend_m1=8.30, imp_i=0.22,  fm1_x_imp=-6.61),
    "M2 OLS jury 1975-1997":  dict(N=6442,  quality=0.87, friend_m1=8.29, imp_i=-0.03, fm1_x_imp=-7.29),
    "M3 OLS tele 1998-2012":  dict(N=10402, quality=0.89, friend_m1=6.59, imp_i=0.30,  fm1_x_imp=-3.85),
    "M4 OLS 98-12+Dia":       dict(N=10424, quality=0.89, friend_m1=5.28, imp_i=0.10,  fm1_x_imp=-2.87, diaspora=0.66),
}


def keyrun(df, cols):
    res = R.run_ols(df, cols)
    p = res["params"]
    return res["nobs"], {k: (float(p[k]) if k in p.index else None) for k in KEYS}


def main():
    df = R.load()
    specs = [
        ("M1 OLS all  1975-2012", R.BASE,                df),
        ("M2 OLS jury 1975-1997", R.BASE,                df[df.year <= 1997]),
        ("M3 OLS tele 1998-2012", R.BASE,                df[df.year >= 1998]),
        ("M4 OLS 98-12+Dia",      R.BASE + ["diaspora"], df[df.year >= 1998]),
    ]
    print(f"Master panel: {len(df):,} rows, {df.year.min()}-{df.year.max()}, "
          f"{df.j.nunique()} receiver countries.\n")
    print(f"{'model':<24}{'stat':<12}{'ours':>10}{'Charron':>10}{'diff':>10}")
    print("-" * 66)
    for label, cols, d in specs:
        n, coeffs = keyrun(d, cols)
        ch = CHARRON[label]
        print(f"{label:<24}{'N':<12}{n:>10}{ch['N']:>10}{n - ch['N']:>+10}")
        for k in KEYS:
            ov, cv = coeffs.get(k), ch.get(k)
            if cv is None and ov is None:
                continue
            os_ = f"{ov:.3f}" if ov is not None else "--"
            cs_ = f"{cv:.3f}" if cv is not None else "--"
            ds_ = f"{ov - cv:+.3f}" if (ov is not None and cv is not None) else ""
            print(f"{'':<24}{k:<12}{os_:>10}{cs_:>10}{ds_:>10}")
        print("-" * 66)


if __name__ == "__main__":
    main()
