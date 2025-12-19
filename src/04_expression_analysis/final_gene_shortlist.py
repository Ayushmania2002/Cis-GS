"""
Merge shortlisted genes with NCBI definitions.
"""

import pandas as pd


def main():
    a = pd.read_csv("Analysis 164 genes.csv")
    n = pd.read_csv("NCBI_IDs_of_gene_with_definitions.csv")

    merged = pd.merge(a, n[["gene_id", "definition"]], on="gene_id", how="left")
    merged.to_csv("Analysis_164_genes_with_definitions.csv", index=False)


if __name__ == "__main__":
    main()

