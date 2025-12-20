"""
PWM summary statistics and supplementary tables

Results reference:
Supplementary Tables S2–S5
"""

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(
    "results/tables/relevant_genes_with_PWM_scores.csv"
)

motifs = ["RAM1", "NIN", "ERN1", "CBP1"]
summary = df[[f"{m}_PWM_score" for m in motifs]].describe().T
summary.reset_index(inplace=True)
summary.columns = [
    "Motif", "Count", "Mean", "Std", "Min",
    "Q1", "Median", "Q3", "Max"
]

summary["Motif"] = summary["Motif"].str.replace("_PWM_score", "")
summary.to_csv(
    "results/tables/PWM_score_summary.csv",
    index=False
)

# Render as PNG
fig, ax = plt.subplots(figsize=(9, 3))
ax.axis("off")
table = ax.table(
    cellText=summary.round(3).values,
    colLabels=summary.columns,
    cellLoc="center",
    loc="center"
)
table.scale(1.2, 1.2)
plt.savefig(
    "results/figures/PWM_score_summary_table.png",
    dpi=600,
    bbox_inches="tight"
)
plt.close()

print("PWM summary tables generated.")
