"""
Co-expression heatmap and hierarchical clustering

Results reference:
Section: "Co-expression patterns and network topology of CYCLOPS-associated genes"

This script visualizes the Topological Overlap Matrix (TOM) as a clustered
heatmap to reveal co-expression structure and module-level organization.
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage

# -----------------------------
# Input
# -----------------------------
tom_file = "data/processed/coexpression/TOM_matrix.csv"

# -----------------------------
# Load TOM matrix
# -----------------------------
tom = pd.read_csv(tom_file, index_col=0)

# Remove self-correlation diagonal for visualization clarity
for gene in tom.index:
    tom.loc[gene, gene] = 0

# -----------------------------
# Hierarchical clustering
# -----------------------------
linkage_matrix = linkage(
    tom,
    method="average",
    metric="euclidean"
)

# -----------------------------
# Heatmap visualization
# -----------------------------
sns.set(style="white")

clustermap = sns.clustermap(
    tom,
    row_linkage=linkage_matrix,
    col_linkage=linkage_matrix,
    cmap="viridis",
    figsize=(14, 14),
    xticklabels=False,
    yticklabels=False
)

clustermap.fig.suptitle(
    "Topological Overlap Matrix (TOM) of Co-expressed Genes",
    fontsize=16
)

# -----------------------------
# Export figure
# -----------------------------
plt.savefig(
    "results/figures/coexpression_TOM_heatmap.png",
    dpi=1000,
    bbox_inches="tight"
)

plt.show()

print("Co-expression heatmap generated.")

