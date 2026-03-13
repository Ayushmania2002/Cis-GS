"""
Topological Overlap Matrix (TOM) calculation

Results reference:
Section: "Network topology and module structure"

A WGCNA-inspired TOM is computed to emphasize shared connectivity
between gene pairs.
"""

import pandas as pd
import numpy as np

# -----------------------------
# Load correlation matrix
# -----------------------------
corr = pd.read_csv(
    "data/processed/coexpression/correlation_matrix.csv",
    index_col=0
)

# -----------------------------
# Adjacency matrix
# -----------------------------
beta = 6
adj = corr.abs() ** beta

# -----------------------------
# TOM computation
# -----------------------------
A = adj.values
numerator = A + A @ A
denominator = (
    np.minimum(A.sum(axis=1)[:, None], A.sum(axis=0)[None, :])
    - A + 1e-9
)

TOM = numerator / denominator

TOM_df = pd.DataFrame(
    TOM,
    index=corr.index,
    columns=corr.columns
)

TOM_df.to_csv(
    "data/processed/coexpression/TOM_matrix.csv"
)

print("✅ TOM matrix computed.")

