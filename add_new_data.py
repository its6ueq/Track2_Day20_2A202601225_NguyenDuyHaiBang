import pandas as pd
import os

df1 = pd.read_csv("data/train_phase1.csv")
df2 = pd.read_csv("data/train_phase2.csv")

df_combined = pd.concat([df1, df2], ignore_index=True)
df_combined.to_csv("data/train_phase1.csv", index=False)

print(f"Cap nhat du lieu: {len(df1)} -> {len(df_combined)} mau")
