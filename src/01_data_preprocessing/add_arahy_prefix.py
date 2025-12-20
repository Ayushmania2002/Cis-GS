"""
Add 'Arahy.' prefix to short gene IDs.
"""

import pandas as pd


def main():
    df = pd.read_csv("relevant_genes_with_short_ids.csv")
    df["short_gene_id"] = "Arahy." + df["short_gene_id"].astype(str)
    df.to_csv("relevant_genes_with_short_ids.csv", index=False)
    print("Prefix added")


if __name__ == "__main__":
    main()

