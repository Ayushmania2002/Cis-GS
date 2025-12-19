"""
Genome-wide scanning of cis-acting regulatory elements (CYC-RE).
"""

import re
from Bio import SeqIO
import pandas as pd


CIS_PATTERNS = {
    "RAM1": "TGGGCCGGCCCA",
    "NIN": ".GCCATGTGGC.",
}


def scan_sequence(sequence, patterns):
    hits = []
    for name, pattern in patterns.items():
        for match in re.finditer(pattern, str(sequence)):
            hits.append({
                "cis_element_name": name,
                "start_position": match.start() + 1,
                "end_position": match.end(),
                "sequence_match": match.group()
            })
    return hits


def main():
    fasta_file = "phytozome_wgs.fasta"
    output_csv = "cis_elements_matches.csv"

    all_hits = []

    for record in SeqIO.parse(fasta_file, "fasta"):
        hits = scan_sequence(record.seq, CIS_PATTERNS)
        for hit in hits:
            hit["chromosome"] = record.id
            all_hits.append(hit)

    pd.DataFrame(all_hits).to_csv(output_csv, index=False)
    print(f"cis-elements written to {output_csv}")


if __name__ == "__main__":
    main()

