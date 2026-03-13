"""
Extract full-length gene sequences using GFF3 annotations and genome FASTA.
"""

import csv
from Bio import SeqIO
from BCBio import GFF
from Bio.SeqRecord import SeqRecord


CSV_FILE = "relevant_genes_with_short_ids.csv"
GFF_FILE = "phytozome_annotations.gff3"
FASTA_FILE = "phytozome_wgs.fasta"
OUTPUT_FASTA = "extracted_gene_sequences.fasta"


def main():
    # Step 1: read gene IDs
    gene_ids = set()
    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            gene_ids.add(row["gene_id"])

    # Step 2: parse GFF
    gene_locations = {}
    with open(GFF_FILE) as gff_handle:
        for rec in GFF.parse(gff_handle):
            for feature in rec.features:
                if feature.type == "gene":
                    gene_id = feature.qualifiers.get("ID", [None])[0]
                    if gene_id in gene_ids:
                        gene_locations[gene_id] = {
                            "chrom": rec.id,
                            "start": int(feature.location.start),
                            "end": int(feature.location.end),
                            "strand": feature.strand
                        }

    # Step 3: extract sequences
    genome = SeqIO.to_dict(SeqIO.parse(FASTA_FILE, "fasta"))

    with open(OUTPUT_FASTA, "w") as out:
        for gene_id, loc in gene_locations.items():
            seq = genome[loc["chrom"]].seq[loc["start"]:loc["end"]]
            if loc["strand"] == -1:
                seq = seq.reverse_complement()

            record = SeqRecord(seq, id=gene_id, description="")
            SeqIO.write(record, out, "fasta")

    print(f"Gene sequences saved to {OUTPUT_FASTA}")


if __name__ == "__main__":
    main()

