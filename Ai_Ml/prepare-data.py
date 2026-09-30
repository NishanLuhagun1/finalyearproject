"""
Data preparation for the Student Performance Predictor's grade prediction model.

Loads the raw UCI Student Performance dataset (student-mat.csv), drops the
demographic/lifestyle columns that the project intentionally does not use,
and keeps only what the app actually collects from students: G1 (midterm),
G2 (preboard), studytime, and the target G3 (final grade).

All three grade columns are on the UCI 0-20 scale. The Django app stores
weighted scores on a 0-100 scale, so the app-side integration will need a
simple *5 / /5 conversion layer -- this script keeps everything on the
original 0-20 scale, matching the dataset's native units, so the model
itself stays simple and the conversion lives in one clearly-marked place
in the Django integration step, not scattered through training code.
"""

import pandas as pd

RAW_PATH = "datasets/s.csv"
OUTPUT_PATH = "datasets/prepared_data.csv"

KEEP_COLUMNS = ["studytime", "G1", "G2", "G3"]


def prepare_data():
    df = pd.read_csv(RAW_PATH)

    # Drop the unnamed index column pandas/Excel export sometimes leaves behind
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    missing = [c for c in KEEP_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Expected columns missing from dataset: {missing}")

    prepared = df[KEEP_COLUMNS].copy()

    # Sanity checks -- fail loudly rather than silently training on bad data
    assert prepared.isnull().sum().sum() == 0, "Unexpected missing values in kept columns"
    assert prepared["studytime"].between(1, 4).all(), "studytime outside expected 1-4 range"
    assert prepared["G1"].between(0, 20).all(), "G1 outside expected 0-20 range"
    assert prepared["G2"].between(0, 20).all(), "G2 outside expected 0-20 range"
    assert prepared["G3"].between(0, 20).all(), "G3 outside expected 0-20 range"

    prepared.to_csv(OUTPUT_PATH, index=False)
    print(f"Prepared {len(prepared)} rows -> {OUTPUT_PATH}")
    print(f"Columns kept: {KEEP_COLUMNS}")
    print(f"Dropped {len(df.columns) - len(KEEP_COLUMNS)} demographic/lifestyle columns")
    return prepared


if __name__ == "__main__":
    prepare_data() 