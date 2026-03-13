"""
Gene-level zoomed visualisation of cis-elements and gene structure.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from Bio import SeqIO


def load_sequence(fasta, chrom):
    for record in SeqIO.parse(fasta, "fasta"):
        if record.id == chrom:
            return record.seq
    raise ValueError(f"{chrom} not found")


def plot_gene(data, gene_id, chrom, fasta):
    gene = data[(data["gene_id"] == gene_id) & (data["chromosome"] == chrom)]

    start = gene["gene_start"].min() - 5000
    end = gene["gene_end"].max() + 5000

    fig, ax = plt.subplots(figsize=(15, 8))
    ax.plot([start, end], [1, 1], lw=8, color="black")
    ax.plot([start, end], [-1, -1], lw=8, color="grey")

    for _, row in gene.iterrows():
        y = 1 if row["strand"] == "+" else -1
        ax.add_patch(patches.Rectangle(
            (row["gene_start"], y - 0.3),
            row["gene_end"] - row["gene_start"],
            0.6, color="red"
        ))
        ax.add_patch(patches.Rectangle(
            (row["cis_start"], y - 0.8),
            row["cis_end"] - row["cis_start"],
            0.4, color="purple"
        ))

    ax.set_xlim(start, end)
    ax.set_ylim(-2, 2)
    ax.set_title(gene_id)

    plt.savefig(f"{gene_id}_focused.png", dpi=1200, bbox_inches="tight")
    plt.close()

