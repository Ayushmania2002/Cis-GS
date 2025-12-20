"""
Visualization of co-expression network

Results reference:
Section: "Visualization of CYCLOPS-associated co-expression modules"
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm

corr = pd.read_csv(
    "data/processed/coexpression/correlation_matrix.csv",
    index_col=0
)

threshold = 0.75
cyclops_id = "XM_025842227"

G = nx.Graph()
genes = corr.index.tolist()
G.add_nodes_from(genes)

for i, g1 in enumerate(genes):
    for j, g2 in enumerate(genes):
        if j <= i:
            continue
        if corr.loc[g1, g2] >= threshold:
            G.add_edge(g1, g2)

pos = nx.spring_layout(G, seed=42, k=0.4)

plt.figure(figsize=(14, 12))
nx.draw_networkx_edges(G, pos, alpha=0.2)

nx.draw_networkx_nodes(
    G, pos,
    node_color="skyblue",
    node_size=250
)

if cyclops_id in G.nodes():
    nx.draw_networkx_nodes(
        G, pos,
        nodelist=[cyclops_id],
        node_color="red",
        node_size=800,
        edgecolors="black"
    )

nx.draw_networkx_labels(G, pos, font_size=8)

plt.title("CYCLOPS-Centered Co-expression Network")
plt.axis("off")
plt.tight_layout()

plt.savefig(
    "results/figures/coexpression_network.png",
    dpi=600
)

plt.show()

