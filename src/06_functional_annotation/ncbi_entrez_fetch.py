"""
Fetch gene definitions from NCBI using accession IDs.
"""

import csv
from Bio import Entrez


Entrez.email = "your_email@example.com"
Entrez.api_key = "YOUR_API_KEY"

INPUT_CSV = "cleaned_file.csv"
OUTPUT_CSV = "gene_definitions.csv"


def fetch_definition(accession):
    try:
        handle = Entrez.efetch(
            db="nucleotide",
            id=accession,
            rettype="gb",
            retmode="text"
        )
        record = handle.read()
        handle.close()

        start = record.find("DEFINITION")
        end = record.find("\nACCESSION")
        return record[start+10:end].strip()
    except Exception as e:
        print(f"{accession}: {e}")
        return None


def main():
    with open(INPUT_CSV) as inp, open(OUTPUT_CSV, "w", newline="") as out:
        reader = csv.DictReader(inp)
        writer = csv.DictWriter(out, fieldnames=["accession", "definition"])
        writer.writeheader()

        for row in reader:
            acc = row["accession"]
            definition = fetch_definition(acc)
            writer.writerow({
                "accession": acc,
                "definition": definition
            })

    print(f"Definitions saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

