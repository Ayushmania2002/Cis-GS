"""
RNA-seq quantification for Lotus japonicus using Kallisto.

Biological design:
- Inoculated sample: rhizobia-treated plants
- Control sample: untreated plants

Paired-end RNA-seq reads are quantified against the reference transcriptome.
"""

import subprocess
from pathlib import Path

# Tools
KALLISTO = "kallisto"  # assume available in PATH

# Input files (repository-relative)
TRANSCRIPTS = Path("data/genome/Lotus_transcripts.fna")
INDEX = Path("data/genome/lotus.idx")

FASTQ_INOC_1 = Path("data/expression/DRR001926_1.fastq")
FASTQ_INOC_2 = Path("data/expression/DRR001926_2.fastq")

FASTQ_CTRL_1 = Path("data/expression/DRR001932_1.fastq")
FASTQ_CTRL_2 = Path("data/expression/DRR001932_2.fastq")

OUT_INOC = Path("results/expression/lotus_inoculated")
OUT_CTRL = Path("results/expression/lotus_control")


def build_index():
    subprocess.run([
        KALLISTO, "index",
        "-i", str(INDEX),
        str(TRANSCRIPTS)
    ], check=True)


def quantify():
    subprocess.run([
        KALLISTO, "quant",
        "-i", str(INDEX),
        "-o", str(OUT_INOC),
        str(FASTQ_INOC_1), str(FASTQ_INOC_2)
    ], check=True)

    subprocess.run([
        KALLISTO, "quant",
        "-i", str(INDEX),
        "-o", str(OUT_CTRL),
        str(FASTQ_CTRL_1), str(FASTQ_CTRL_2)
    ], check=True)


if __name__ == "__main__":
    build_index()
    quantify()

