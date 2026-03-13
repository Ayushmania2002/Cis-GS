"""
PWM frequency tables for supplementary material
"""

import pandas as pd

files = {
    "NIN": "results/pwm/NIN_PWM.csv",
    "RAM1": "results/pwm/RAM1_PWM.csv",
    "CBP1": "results/pwm/CBP1_PWM.csv",
    "ERN1": "results/pwm/ERN1_PWM.csv"
}

for motif, path in files.items():
    pwm = pd.read_csv(path)
    pwm.insert(0, "Position", range(1, len(pwm) + 1))
    pwm.to_csv(
        f"results/tables/{motif}_PWM_frequency_table.csv",
        index=False
    )

print("PWM frequency tables exported.")
