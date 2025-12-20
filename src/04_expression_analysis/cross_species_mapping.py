"""
Cross-species mapping between Arachis hypogaea and Lotus japonicus
using BLAST-based homology.
"""

import pandas as pd

BLAST = "results/tables/Arachis_vs_Lotus_matches.tsv"
OUT = "results/tables/common_conserved_genes.csv"


def main():
    cols = [
        "Arachis_gene", "Lotus_gene", "identity", "length",
        "mismatch", "gap", "qstart", "qend",
        "sstart", "send", "evalue", "bitscore"
    ]

    df = pd.read_csv(BLAST, sep="\t", names=cols)
    common = df["Lotus_gene"].unique()

    pd.DataFrame(common, columns=["Lotus_gene"]).to_csv(OUT, index=False)
    print(f"Saved {len(common)} conserved genes")


if __name__ == "__main__":
    main()

