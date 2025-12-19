"""
Merge NCBI definitions with gene ID table.
"""

import pandas as pd


def main():
    ids = pd.read_csv("NCBI_IDs_of_gene_cleaned.csv")
    defs = pd.read_csv("gene_definitions.csv")

    merged = pd.merge(
        ids,
        defs[["accession", "definition"]],
        on="accession",
        how="left"
    )

    merged.to_csv("NCBI_IDs_of_gene_with_definitions.csv", index=False)
    print("Merged annotation table created")


if __name__ == "__main__":
    main()

