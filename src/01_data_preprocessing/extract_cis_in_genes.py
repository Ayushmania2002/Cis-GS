"""
Purpose:
---------
Searches for cis-acting sequences within genome gene sequences
and outputs their genomic positions. This is part of the genome
preprocessing module for CYCLOPS-associated gene analysis.

Inputs:
-------
- genes.fasta          : FASTA file of gene sequences
- cis_sequences.fasta  : FASTA file of cis-acting motifs

Outputs:
--------
- Prints results of matches with gene ID, cis-element ID,
  and start/end positions.
- Can be easily extended to save results as CSV for downstream analyses.

Usage:
------
python extract_cis_in_genes.py
"""

from Bio import SeqIO
import os
import csv

# ------------------------------
# File paths (relative to repository root)
# ------------------------------
GENE_FASTA = os.path.join("01_genome_preprocessing", "genes.fasta")
CIS_FASTA = os.path.join("01_genome_preprocessing", "cis_sequences.fasta")
OUTPUT_CSV = os.path.join("01_genome_preprocessing", "gene_cis_matches.csv")

# ------------------------------
# Read genome sequences
# ------------------------------
print("Loading genome sequences...")
genome_records = SeqIO.to_dict(SeqIO.parse(GENE_FASTA, "fasta"))

# Read cis-acting sequences
print("Loading cis-element sequences...")
cis_sequences = SeqIO.to_dict(SeqIO.parse(CIS_FASTA, "fasta"))

# ------------------------------
# Search for cis-elements in each gene
# ------------------------------
print("Searching for cis-elements in genes...")
results = []

for gene_id, gene_seq in genome_records.items():
    gene_str = str(gene_seq.seq)
    for cis_id, cis_seq in cis_sequences.items():
        cis_str = str(cis_seq.seq)
        start = gene_str.find(cis_str)
        if start != -1:
            results.append({
                "Gene_ID": gene_id,
                "Cis_Element_ID": cis_id,
                "Start": start,
                "End": start + len(cis_str)
            })

# ------------------------------
# Save results to CSV
# ------------------------------
if results:
    with open(OUTPUT_CSV, "w", newline="") as csvfile:
        fieldnames = ["Gene_ID", "Cis_Element_ID", "Start", "End"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"Search complete! Results saved to: {OUTPUT_CSV}")
else:
    print(" No cis-elements found in the genome sequences.")

