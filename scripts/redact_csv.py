"""Redact copyrighted text columns from story metadata CSV."""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_FILE = DATA_DIR / "2023-11-02-story-metadata.csv"

REDACT_COLUMNS = [
    "poll_question",
    "poll_option_a",
    "poll_option_b",
    "hashtags",
    "mentions",
    "tappable_objects",
    "fallback",
]

df = pd.read_csv(CSV_FILE)
print(f"Loaded {len(df)} rows from {CSV_FILE.name}")

redacted = 0
for col in REDACT_COLUMNS:
    if col in df.columns:
        non_empty = df[col].notna().sum()
        df[col] = ""
        print(f"  Cleared {non_empty} non-null values in column '{col}'")
        redacted += non_empty
    else:
        print(f"  Column '{col}' not found — skipping")

df.to_csv(CSV_FILE, index=False)
print(f"\nDone. Redacted {redacted} total values. Saved to {CSV_FILE.name}")
