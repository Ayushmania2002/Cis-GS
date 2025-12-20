"""
PWM construction and sequence logo generation for cis-elements

Results reference:
Section: "Construction of cis-element PWMs"

Aligned motif instances were used to generate position weight matrices
(PWMs) and publication-quality sequence logos.
"""

from Bio import motifs
from Bio.Seq import Seq
import pandas as pd
import matplotlib.pyplot as plt
import logomaker
import os

# --------------------------------------------------
# Aligned motif sequences
# --------------------------------------------------
alignments = {
    "RAM1": [
        "GTGAACAGATGGGCCGGCCCAAAAAGTGGG",
        "GTAAATAGATGGGCCGGCCCAAATAAAGTGGG",
        "GTAAAAAGGTGGGCCGGCCCATAGAAAGTAG"
    ],
    "NIN": [
        "ATTTTGTACGATTGCCATGTGGCACGCAGAGAGGAGCCCA",
        "TATTTGTAGAGTCGCCATGTGGCTCACGACGAGGGAACCCG"
    ],
    "CBP1": [
        "GTGCACTAATAAATAAATGCCGGCCTTTACCCTCGTTATTT",
        "GAGTGATGCCACGTGGAAGAAGGCAAGCAAAGCAATTAAGA"
    ],
    "ERN1": [
        "ATCATTTTGGAGCCTCCATGTGGCAGTCGTTCATGCCTTTA",
        "TTCGTTTTTAATATTTGAAACGTCTTATTTTTATTCTAA"
    ]
}

# --------------------------------------------------
# Utilities
# --------------------------------------------------
def clean_and_pad(seqs):
    seqs = [s.replace("-", "").upper() for s in seqs]
    max_len = max(len(s) for s in seqs)
    return [s.ljust(max_len, "N") for s in seqs]

def make_pwm(gene, seqs, output_dir="results/pwm"):
    os.makedirs(output_dir, exist_ok=True)
    seqs = clean_and_pad(seqs)
    motif = motifs.create([Seq(s) for s in seqs])

    pwm = motif.counts.normalize(pseudocounts=0.5)
    pwm_df = pd.DataFrame({b: pwm[b] for b in "ACGT"})
    pwm_df.to_csv(f"{output_dir}/{gene}_PWM.csv", index=False)

    # Sequence logo
    plt.figure(figsize=(12, 3))
    logomaker.Logo(pwm_df, color_scheme="classic")
    plt.title(f"{gene} cis-element motif")
    plt.xlabel("Position")
    plt.ylabel("Bits")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/{gene}_logo.png", dpi=600)
    plt.close()

# --------------------------------------------------
# Run
# --------------------------------------------------
for gene, seqs in alignments.items():
    make_pwm(gene, seqs)

print("PWMs and logos generated.")

