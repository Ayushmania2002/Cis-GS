"""
Prepare expression matrix for co-expression analysis

Results reference:
Section: "Co-expression analysis of CYCLOPS-associated genes"

This script harmonizes gene identifiers, merges expression values with the
GO/KEGG-filtered gene list, and produces a clean expression matrix suitable
for correlation-based network analysis.
"""

import pandas as pd
import re

# -----------------------------
# Input files
# -----------------------------
expression_file = "data/raw/alldeg_data_normalized.csv"
gene_list_file = "data/processed/GO_KEGG_List.csv"

# -----------------------------
# Load data
# -----------------------------
expr = pd.read_csv(expression_file)
genes = pd.read_csv(gene_list_file)

# -----------------------------
# Clean gene identifiers
# -----------------------------
expr.rename(columns={"Unnamed: 0": "Gene_ID"}, inplace=True)

expr["Gene_ID"] = (
    expr["Gene_ID"]
    .str.replace("^rna-", "", regex=True)
    .str.replace(r"\.\d+$", "", regex=True)
)

genes["Gene_ID"] = genes["Gene_ID"].str.replace(r"\.\d+$", "", regex=True)

# -----------------------------
# Merge expression with gene list
# -----------------------------
merged = genes.merge(expr, on="Gene_ID", how="left")

# -----------------------------
# Define expression columns
# -----------------------------
exp_cols = ["0dpi", "6dpi", "10dpi", "15dpi", "21dpi"]

# -----------------------------
# Add CYCLOPS explicitly if missing
# -----------------------------
cyclops_id = "XM_025842227"
if cyclops_id not in merged["Gene_ID"].values:
    merged = pd.concat([
        merged,
        pd.DataFrame([[cyclops_id] + [None]*len(exp_cols)],
                     columns=["Gene_ID"] + exp_cols)
    ])

# -----------------------------
# Final expression matrix
# -----------------------------
expr_matrix = merged[["Gene_ID"] + exp_cols]
expr_matrix.to_csv(
    "data/processed/coexpression/WGCNA_expression_matrix.csv",
    index=False
)

print("✅ Co-expression expression matrix prepared.")
