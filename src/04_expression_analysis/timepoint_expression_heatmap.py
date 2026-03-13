"""
Time-course expression heatmap.
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


def main():
    df = pd.read_csv("relevant_genes_with_short_ids_time_exp.csv")
    df.set_index("GeneID", inplace=True)

    log_df = np.log10(df.replace(0, np.nan))
    log_df["avg"] = log_df[["0dpi", "6dpi", "10dpi"]].mean(axis=1)
    log_df = log_df.sort_values("avg", ascending=False).drop(columns="avg")

    sns.heatmap(log_df, cmap="coolwarm")
    plt.savefig("timepoint_expression_heatmap.pdf")
    plt.close()


if __name__ == "__main__":
    main()

