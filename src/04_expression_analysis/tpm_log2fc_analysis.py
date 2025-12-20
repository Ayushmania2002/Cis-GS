"""
Merge Kallisto TPM values and compute log2 fold-change
"""

import pandas as pd
import numpy as np
from pathlib import Path

INOC = Path("data/processed/kallisto/inoculated/abundance.tsv")
CTRL = Path("data/processed/kallisto/control/abundance.tsv")

outdir = Path("data/processed/differential_expression")
outdir.mkdir(exist_ok=True)

inoc = pd.read_csv(INOC, sep="\t")[["target_id", "tpm"]]
ctrl = pd.read_csv(CTRL, sep="\t")[["target_id", "tpm"]]

merged = inoc.merge(ctrl, on="target_id", suffixes=("_inoc", "_ctrl"))

pseudocount = 0.1
merged["log2FC"] = np.log2(
    (merged["tpm_inoc"] + pseudocount) /
    (merged["tpm_ctrl"] + pseudocount)
)

merged.to_csv(outdir / "log2FC_results.csv", index=False)

