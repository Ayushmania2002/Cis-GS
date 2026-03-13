"""
Visualization of Lotus japonicus differential expression.

Generates:
- Volcano plot
- Upregulated vs downregulated gene comparison
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib_venn import venn2
from scipy import stats
from pathlib import Path

DATA = Path("results/tables/lotus_log2FC.csv")


def volcano_plot(df):
    df["neglog10_p"] = -np.log10(0.05)  # placeholder threshold

    plt.figure(figsize=(8, 6))
    plt.scatter(df["log2FC"], df["neglog10_p"], s=5, alpha=0.5)
    plt.axvline(1, linestyle="--")
    plt.axvline(-1, linestyle="--")
    plt.xlabel("log2 Fold Change")
    plt.ylabel("-log10(p-value)")
    plt.title("Lotus japonicus Volcano Plot")
    plt.savefig("results/figures/lotus_volcano.png", dpi=400)
    plt.close()


def venn_plot(df):
    up = set(df[df["regulation"] == "Upregulated"]["target_id"])
    down = set(df[df["regulation"] == "Downregulated"]["target_id"])

    plt.figure(figsize=(6, 6))
    venn2([up, down], set_labels=("Up", "Down"))
    plt.title("Lotus Differential Expression")
    plt.savefig("results/figures/lotus_venn.png", dpi=400)
    plt.close()


if __name__ == "__main__":
    df = pd.read_csv(DATA)
    volcano_plot(df)
    venn_plot(df)

