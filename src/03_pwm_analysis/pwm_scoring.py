"""
PWM-based scoring of cis-element occurrences

Results reference:
Section: "Quantitative scoring of cis-elements"
"""

import pandas as pd
from math import log2

# --------------------------------------------------
# PWM helpers
# --------------------------------------------------
def build_pwm(consensus, pseudocount=0.5):
    bases = ["A", "C", "G", "T"]
    pwm = []
    for base in consensus:
        col = {}
        if base == "N":
            for b in bases:
                col[b] = 0.25
        else:
            for b in bases:
                col[b] = 1.0 if b == base else pseudocount
            total = sum(col.values())
            for b in bases:
                col[b] /= total
        pwm.append(col)
    return pwm

def pwm_score(seq, pwm, background=0.25):
    score = 0.0
    for i, base in enumerate(seq.upper()):
        if i >= len(pwm):
            break
        if base in pwm[i]:
            score += log2(pwm[i][base] / background)
    return round(score, 3)

# --------------------------------------------------
# Consensus motifs
# --------------------------------------------------
motifs = {
    "RAM1": "TGGGCCGGCCCA",
    "NIN":  "NGCCANNTGGCN",
    "ERN1": "NNTNNANNNGNNCNNT",
    "CBP1": "TNNANGNNGGC"
}

pwms = {k: build_pwm(v) for k, v in motifs.items()}

# --------------------------------------------------
# Score sequences
# --------------------------------------------------
df = pd.read_csv("data/processed/cis_elements/relevant_genes.csv")

for name, pwm in pwms.items():
    df[f"{name}_PWM_score"] = df["sequence_match"].apply(
        lambda s: pwm_score(s, pwm)
    )

df.to_csv(
    "results/tables/relevant_genes_with_PWM_scores.csv",
    index=False
)

print("PWM scoring completed.")

