"""
RNA-seq quantification using Kallisto
Organism: Lotus japonicus (Gifu)
"""

import subprocess
from pathlib import Path

# ==============================
# User-configurable paths
# ==============================
KALLISTO = "kallisto"  # assume in PATH
TRANSCRIPTS = "data/reference/Lotus_transcripts.fasta"
INDEX = "data/reference/lotus_kallisto.idx"

FASTQ = {
    "inoculated": (
        "data/raw/lotus/inoculated_R1.fastq.gz",
        "data/raw/lotus/inoculated_R2.fastq.gz"
    ),
    "control": (
        "data/raw/lotus/control_R1.fastq.gz",
        "data/raw/lotus/control_R2.fastq.gz"
    )
}

OUTDIR = Path("data/processed/kallisto")
OUTDIR.mkdir(parents=True, exist_ok=True)

# ==============================
# Build index
# ==============================
subprocess.run([
    KALLISTO, "index",
    "-i", INDEX,
    TRANSCRIPTS
], check=True)

# ==============================
# Quantification
# ==============================
for condition, (r1, r2) in FASTQ.items():
    out = OUTDIR / condition
    out.mkdir(exist_ok=True)

    subprocess.run([
        KALLISTO, "quant",
        "-i", INDEX,
        "-o", str(out),
        r1, r2
    ], check=True)

