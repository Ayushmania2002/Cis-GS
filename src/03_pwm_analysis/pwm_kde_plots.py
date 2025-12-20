"""
PWM score distribution analysis

Results reference:
Section: "Distribution of PWM scores"
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv(
    "results/tables/relevant_genes_with_PWM_scores.csv"
)

plt.figure(figsize=(8, 6))

for motif in ["RAM1", "NIN", "ERN1", "CBP1"]:
    sns.kdeplot(
        df[f"{motif}_PWM_score"],
        fill=True,
        label=motif,
        alpha=0.6
    )

plt.xlabel("PWM log-likelihood score", fontsize=16, weight="bold")
plt.ylabel("Density", fontsize=16, weight="bold")
plt.title("PWM Score Distributions of cis-elements", fontsize=18, weight="bold")
plt.legend(fontsize=12)
plt.tight_layout()

plt.savefig(
    "results/figures/PWM_score_distribution.png",
    dpi=600
)
plt.close()

print("PWM KDE plot saved.")

