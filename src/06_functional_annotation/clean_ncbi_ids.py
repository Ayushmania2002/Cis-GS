"""
Remove duplicate NCBI accession IDs.
"""

import pandas as pd


INPUT = "NCBI_IDs_of_gene.csv"
OUTPUT = "cleaned_file.csv"


def main():
    df = pd.read_csv(INPUT)
    df = df.drop_duplicates(subset=["accession"])
    df.to_csv(OUTPUT, index=False)
    print(f"Cleaned file saved to {OUTPUT}")


if __name__ == "__main__":
    main()

