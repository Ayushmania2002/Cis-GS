"""
Compute gene–gene correlation matrix

Results reference:
Section: "Identification of co-expressed genes associated with CYCLOPS"

Pearson correlation is calculated across all genes using normalized
time-course expression values.
"""

import pandas as pd

# -----------------------------
# Load expression matrix
# -----------------------------
df = pd.read_csv(
    "data/processed/coexpression/WGCNA_expression_matrix.csv"
)

exp_cols = ["0dpi", "6dpi", "10dpi", "15dpi", "21dpi"]

# Ensure numeric
df[exp_cols] = df[exp_cols].apply(pd.to_numeric, errors="coerce")

# Remove incomplete rows
df = df.dropna(subset=exp_cols)

# Set gene IDs
genes = df["Gene_ID"].tolist()
expr = df[exp_cols].T

# -----------------------------
# Pearson correlation
# -----------------------------
corr = expr.corr(method="pearson")
corr.index = genes
corr.columns = genes

corr.to_csv(
    "data/processed/coexpression/correlation_matrix.csv"
)

print("✅ Correlation matrix saved.")

