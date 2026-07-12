"""
fig2_network.py
===============
Replicate Fig. 2: "Alternative Friend Groups (method 2): 1998-2012" -- a network
of countries connected by *significant pairwise bias*.

Edges: an undirected pair is drawn when at least one direction shows a
statistically significant positive bias (>= 3 observations, p < 0.05); edge
thickness follows the paper's bias bins:  <2.5, 2.5-4.5, 4.5-6.5, >6.5.
Nodes are coloured by the friend group (method 1) they belong to, and laid out
with a force-directed (spring) layout so blocs pull together, as in the paper.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from lib_countries import NAME
from pairwise_bias import undirected_edges

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")

# Paper's edge-thickness bins for pairwise bias.
def _width(bias):
    if bias < 2.5:   return 0.8
    if bias < 4.5:   return 2.0
    if bias < 6.5:   return 3.5
    return 5.5


def main():
    df = pd.read_csv(os.path.join(OUT, "master.csv"))
    edges = undirected_edges(df, 1998, 2012)

    # Group colouring from the method-1 clustering already computed.
    grp = pd.read_csv(os.path.join(OUT, "friend_groups_1998-2012.csv"))
    code2grp = dict(zip(grp["code"], grp["group"]))
    groups = sorted(set(code2grp.values()))
    cmap = plt.get_cmap("tab20")
    grp_color = {g: cmap(k % 20) for k, g in enumerate(groups)}

    # Build the graph.
    G = nx.Graph()
    for _, r in edges.iterrows():
        G.add_edge(r["a"], r["b"], bias=r["bias"])
    # include isolated significant nodes only if they appear in edges
    pos = nx.spring_layout(G, seed=42, k=0.9, iterations=300)

    fig, ax = plt.subplots(figsize=(12, 10))
    # edges
    for a, b, d in G.edges(data=True):
        x = [pos[a][0], pos[b][0]]; y = [pos[a][1], pos[b][1]]
        ax.plot(x, y, color="0.4", linewidth=_width(d["bias"]), zorder=1)
    # nodes
    for n in G.nodes():
        c = grp_color.get(code2grp.get(n, ""), "lightgray")
        ax.scatter(*pos[n], s=900, color=c, edgecolors="black", zorder=2)
        ax.text(pos[n][0], pos[n][1], NAME.get(n, n), ha="center", va="center",
                fontsize=7, zorder=3)

    # legend for edge widths
    from matplotlib.lines import Line2D
    leg = [Line2D([0], [0], color="0.4", lw=_width(v), label=lab)
           for v, lab in [(1, "<2.5"), (3, "2.5-4.5"), (5, "4.5-6.5"), (7, ">6.5")]]
    ax.legend(handles=leg, title="Pairwise bias level", loc="lower left")
    ax.set_title("Fig. 2. Alternative Friend Groups (method 2): 1998-2012\n"
                 "(edges: significant positive pairwise bias, >=3 obs, p<0.05)")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2_network.png"), dpi=150)
    plt.close(fig)

    # Persist method-2 friend dyads for the regression (both periods).
    rows = []
    for label, lo, hi in [("1975-1997", 1975, 1997), ("1998-2012", 1998, 2012)]:
        from pairwise_bias import directed_bias
        d = directed_bias(df, lo, hi)
        for _, r in d.iterrows():
            rows.append((label, r["i"], r["j"], r["sig_pos"]))
    pd.DataFrame(rows, columns=["period", "i", "j", "friend_m2"]).to_csv(
        os.path.join(OUT, "friend_dyads_method2.csv"), index=False)

    print(f"Fig 2 saved -> output/fig2_network.png ({G.number_of_edges()} edges, "
          f"{G.number_of_nodes()} nodes)")


if __name__ == "__main__":
    main()
