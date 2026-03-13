"""
CYCLOPS-centered co-expression network

Results reference:
Section: "CYCLOPS-centered co-expression network"

Genes exhibiting strong positive correlation with CYCLOPS are identified
and retained for network construction.
"""

import pandas as pd
import numpy as np

df = pd.read_csv(
    "data/processed/coexpression/WGCNA_expression_matrix.csv"
)

exp_cols = ["0dpi", "6dpi", "10dpi", "15dpi", "21dpi"]

df[exp_cols] = df[exp_cols].apply(pd.to_numeric, errors="coerce")
df = df.dropna(subset=exp_cols)

cyclops_id = "XM_025842227"
cyclops_profile = df.loc[
    df["Gene_ID"] == cyclops_id, exp_cols
].values.flatten()

# -----------------------------
# Correlation with CYCLOPS
# -----------------------------
correlations = []

for _, row in df.iterrows():
    r = np.corrcoef(cyclops_profile, row[exp_cols])[0, 1]
    correlations.append(r)

df["Cyclops_corr"] = correlations

# Threshold
threshold = 0.7
neighbors = df[df["Cyclops_corr"] >= threshold]

neighbors.to_csv(
    "data/processed/coexpression/cyclops_neighbors.csv",
    index=False
)

print(f"✅ {neighbors.shape[0]} CYCLOPS-coexpressed genes identified.")

