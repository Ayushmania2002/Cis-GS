"""
Tissue-specific expression heatmap.
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


def main():
    df = pd.read_csv("relevant_genes_with_short_ids_tissue_exp_new.csv")
    df.set_index("GeneID", inplace=True)

    log_df = np.log10(df.replace(0, np.nan))
    log_df["avg"] = log_df[["root", "nodule"]].mean(axis=1)
    log_df = log_df.sort_values("avg", ascending=False).drop(columns="avg")

    sns.heatmap(log_df, cmap="coolwarm")
    plt.savefig("tissue_expression_heatmap.pdf")
    plt.close()


if __name__ == "__main__":
    main()

