"""
Differential expression analysis for Lotus japonicus.

Computes log2 fold change between inoculated and control samples
using TPM values from Kallisto.
"""

import pandas as pd
import numpy as np
from pathlib import Path

INOC = Path("results/expression/lotus_inoculated/abundance.tsv")
CTRL = Path("results/expression/lotus_control/abundance.tsv")
OUT = Path("results/tables/lotus_log2FC.csv")


def main():
    inoc = pd.read_csv(INOC, sep="\t")[["target_id", "tpm"]]
    ctrl = pd.read_csv(CTRL, sep="\t")[["target_id", "tpm"]]

    df = inoc.merge(ctrl, on="target_id", suffixes=("_inoc", "_ctrl"))

    pseudocount = 0.1
    df["log2FC"] = np.log2(
        (df["tpm_inoc"] + pseudocount) /
        (df["tpm_ctrl"] + pseudocount)
    )

    df["regulation"] = np.where(
        df["log2FC"] > 1, "Upregulated",
        np.where(df["log2FC"] < -1, "Downregulated", "No_change")
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved differential expression to {OUT}")


if __name__ == "__main__":
    main()

