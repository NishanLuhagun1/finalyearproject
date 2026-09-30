"""Quick look at the raw datasets (run from anywhere: paths are relative to this file)."""

from pathlib import Path

import pandas as pd

DATASETS = Path(__file__).resolve().parent / "datasets"

# UCI Student Performance data used to train the grade-prediction model
students = pd.read_csv(DATASETS / "s.csv")
# Second dataset (needs `openpyxl`, listed in requirements.txt)
dma = pd.read_excel(DATASETS / "DMA DATASET.xlsx")

for name, frame in (("s.csv", students), ("DMA DATASET.xlsx", dma)):
    print(f"\n=== {name}: {frame.shape[0]} rows x {frame.shape[1]} columns")
    print(frame.head())
    print("\nMissing values per column:")
    print(frame.isnull().sum()[frame.isnull().sum() > 0].to_string() or "none")
