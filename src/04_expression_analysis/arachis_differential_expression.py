"""
Differential expression analysis for Arachis hypogaea
using multi-timepoint RNA-seq data.
"""

import pandas as pd
import numpy as np
from scipy import stats

DATA = "data/expression/alldeg_data_normalized.csv"
OUT_UP = "results/tables/arachis_upregulated.csv"
OUT_DOWN = "results/tables/arachis_downregulated.csv"


def main():
    df = pd.read_csv(DATA)
    gene_col = df.columns[0]

    ctrl = ["2a", "2b", "2c"]
    dpi3 = ["3a", "3b", "3c"]
    dpi21 = ["4a", "4b", "4c"]

    df["ctrl_mean"] = df[ctrl].mean(axis=1)
    df["dpi3_mean"] = df[dpi3].mean(axis=1)
    df["dpi21_mean"] = df[dpi21].mean(axis=1)

    df["log2FC_3dpi"] = np.log2(df["dpi3_mean"] + 1) - np.log2(df["ctrl_mean"] + 1)
    df["log2FC_21dpi"] = np.log2(df["dpi21_mean"] + 1) - np.log2(df["ctrl_mean"] + 1)

    df["pval"] = df.apply(
        lambda r: stats.ttest_ind(
            r[dpi3 + dpi21], r[ctrl], equal_var=False
        )[1], axis=1
    )

    up = df[(df["log2FC_3dpi"] > 1) & (df["pval"] < 0.05)]
    down = df[(df["log2FC_3dpi"] < -1) & (df["pval"] < 0.05)]

    up[[gene_col]].to_csv(OUT_UP, index=False)
    down[[gene_col]].to_csv(OUT_DOWN, index=False)


if __name__ == "__main__":
    main()

