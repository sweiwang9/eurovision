"""
pairwise_bias.py
================
Helper shared by Fig 2, Appendix 3 and the "method 2" friend-dyad definition.

For a given time period it computes, for every ordered dyad (i -> j) observed
at least 3 times, the average bias and a one-sample t-test of H0: mean bias = 0.
A dyad is flagged "significant positive" when mean bias > 0 and p < 0.05 -- the
paper's "significant at the 95% level of confidence" criterion.
"""

import numpy as np
import pandas as pd
from scipy import stats

MIN_OBS = 3


def directed_bias(df, lo, hi):
    """Per ordered dyad (i->j) in [lo,hi]: mean bias, n, t-test p-value, sig flag."""
    sub = df[(df["year"] >= lo) & (df["year"] <= hi)]
    out = []
    for (i, j), g in sub.groupby(["i", "j"]):
        b = g["bias"].values
        if len(b) < MIN_OBS:
            continue
        # one-sample t-test against 0; degenerate (zero variance) handled.
        if np.allclose(b, b[0]):
            p = 0.0 if abs(b.mean()) > 1e-9 else 1.0
        else:
            p = stats.ttest_1samp(b, 0.0).pvalue
        out.append((i, j, b.mean(), len(b), p, int(b.mean() > 0 and p < 0.05)))
    return pd.DataFrame(out, columns=["i", "j", "bias", "n", "pval", "sig_pos"])


def undirected_edges(df, lo, hi):
    """Collapse to unordered pairs for the network graph (Fig 2): a pair is an
    edge if at least one direction is a significant positive bias; edge weight is
    the mean of the significant directed biases."""
    d = directed_bias(df, lo, hi)
    edges = {}
    for _, r in d.iterrows():
        key = frozenset((r["i"], r["j"]))
        edges.setdefault(key, [])
        if r["sig_pos"]:
            edges[key].append(r["bias"])
    out = []
    for key, biases in edges.items():
        if biases:                              # keep only pairs with >=1 sig dir
            a, b = tuple(key)
            out.append((a, b, float(np.mean(biases)), len(biases)))
    return pd.DataFrame(out, columns=["a", "b", "bias", "n_sig_dir"])
