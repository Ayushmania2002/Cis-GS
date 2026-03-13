"""
Chromosome-level visualisation of genes and cis-elements.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def plot_chromosome(data, chromosome_id, max_len):
    chrom = data[data["chromosome"] == chromosome_id]
    fwd = chrom[chrom["strand"] == "+"]
    rev = chrom[chrom["strand"] == "-"]

    fig, ax = plt.subplots(figsize=(15, 4))

    ax.plot([0, max_len], [2, 2], lw=10, color="black")
    ax.plot([0, max_len], [-2, -2], lw=10, color="grey")

    for _, row in fwd.iterrows():
        ax.add_patch(patches.Rectangle(
            (row["gene_start"], 1.9),
            row["gene_end"] - row["gene_start"],
            1, color="blue", alpha=0.6
        ))

    for _, row in rev.iterrows():
        ax.add_patch(patches.Rectangle(
            (row["gene_start"], -2.2),
            row["gene_end"] - row["gene_start"],
            1, color="green", alpha=0.6
        ))

    ax.set_xlim(0, max_len)
    ax.set_ylim(-5, 5)
    ax.set_xlabel("Position (bp)")
    ax.set_ylabel("Strand")
    ax.set_title(f"Chromosome {chromosome_id}")

    plt.savefig(f"{chromosome_id}_overview.png", dpi=1200, bbox_inches="tight")
    plt.close()


def main():
    data = pd.read_csv("relevant_genes_with_short_ids.csv")
    max_len = data["gene_end"].max() * 1.1

    for chrom in data["chromosome"].unique():
        plot_chromosome(data, chrom, max_len)


if __name__ == "__main__":
    main()

