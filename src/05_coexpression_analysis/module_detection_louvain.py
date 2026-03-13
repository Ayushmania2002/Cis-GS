"""
Module detection using Louvain clustering

Results reference:
Section: "Modular organization of the co-expression network"
"""

import pandas as pd
import networkx as nx
from networkx.algorithms.community import louvain_communities

corr = pd.read_csv(
    "data/processed/coexpression/correlation_matrix.csv",
    index_col=0
)

threshold = 0.75
G = nx.Graph()

genes = corr.index.tolist()
G.add_nodes_from(genes)

for i, g1 in enumerate(genes):
    for j, g2 in enumerate(genes):
        if j <= i:
            continue
        if corr.loc[g1, g2] >= threshold:
            G.add_edge(g1, g2, weight=corr.loc[g1, g2])

communities = louvain_communities(G, seed=42)

# -----------------------------
# Export modules
# -----------------------------
for i, module in enumerate(communities):
    pd.DataFrame(
        list(module),
        columns=["Gene"]
    ).to_csv(
        f"results/tables/module_{i}_genes.csv",
        index=False
    )

print(f"✅ {len(communities)} modules detected.")

