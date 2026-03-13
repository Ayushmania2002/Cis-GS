"""
BLASTn search of extracted gene sequences against NCBI nt database.
"""

from Bio.Blast import NCBIWWW, NCBIXML
from Bio import SeqIO


FASTA_FILE = "extracted_gene_sequences.fasta"
OUTPUT_XML = "blast_results.xml"


def main():
    with open(FASTA_FILE) as handle:
        for record in SeqIO.parse(handle, "fasta"):
            print(f"BLASTing {record.id}")
            result_handle = NCBIWWW.qblast(
                program="blastn",
                database="nt",
                sequence=record.seq
            )

            with open(OUTPUT_XML, "w") as out:
                out.write(result_handle.read())

            result_handle.close()

            with open(OUTPUT_XML) as res:
                blast_record = NCBIXML.read(res)

            if blast_record.alignments:
                hit = blast_record.alignments[0]
                print(f"Top hit: {hit.hit_def}")
            else:
                print("No hits found")

            print("-" * 60)


if __name__ == "__main__":
    main()

