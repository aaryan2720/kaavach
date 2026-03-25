#!/usr/bin/env python
"""Download UNSW-NB15 dataset and perform initial analysis"""

import subprocess
import sys
import os
import pandas as pd
import json

# Install kagglehub if not available
try:
    import kagglehub
except ImportError:
    print("Installing kagglehub...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "kagglehub", "-q"])
    import kagglehub

# Download the dataset
print("=" * 70)
print("Downloading UNSW-NB15 dataset from Kaggle...")
print("=" * 70)
path = kagglehub.dataset_download("mrwellsdavid/unsw-nb15")
print(f"\nDataset downloaded to: {path}\n")

# List files in the directory
files = [f for f in os.listdir(path) if f.endswith('.csv')]
print(f"CSV files found:")
for f in files:
    print(f"  - {f}")

if not files:
    print("ERROR: No CSV files found in the dataset!")
    sys.exit(1)

# Load the training set (it's the most complete dataset)
csv_file = os.path.join(path, "UNSW_NB15_training-set.csv")
if not os.path.exists(csv_file):
    # Fallback to first valid file
    csv_file = os.path.join(path, files[0])

print(f"\nLoading: {os.path.basename(csv_file)}")
try:
    df = pd.read_csv(csv_file, encoding='utf-8')
except UnicodeDecodeError:
    print("UTF-8 encoding failed, trying latin1...")
    df = pd.read_csv(csv_file, encoding='latin1')

print("\n" + "=" * 70)
print("DATASET OVERVIEW")
print("=" * 70)
print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"\nColumn Names and Types:")
print(df.dtypes)

print("\n" + "=" * 70)
print("FIRST FEW ROWS")
print("=" * 70)
print(df.head())

print("\n" + "=" * 70)
print("MISSING VALUES")
print("=" * 70)
missing = df.isnull().sum()
if missing.sum() > 0:
    print(missing[missing > 0])
else:
    print("No missing values found!")

print("\n" + "=" * 70)
print("STATISTICAL SUMMARY")
print("=" * 70)
print(df.describe())

# Find label column
label_col = None
for col in ["label", "Label", "class", "Class", "attack_cat"]:
    if col in df.columns:
        label_col = col
        break

if label_col:
    print(f"\n" + "=" * 70)
    print(f"LABEL INFORMATION ({label_col})")
    print("=" * 70)
    print(df[label_col].value_counts())
    print(f"\nClass distribution (%):")
    print((df[label_col].value_counts() / len(df) * 100).round(2))

# Display feature statistics
print("\n" + "=" * 70)
print("FEATURE ANALYSIS")
print("=" * 70)
numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
print(f"Numeric features: {len(numeric_cols)}")
for col in numeric_cols[:10]:  # Show first 10
    print(f"  - {col}: range [{df[col].min()}, {df[col].max()}]")

# Save to local directory
local_csv = os.path.join(os.path.dirname(__file__), "UNSW_NB15.csv")
print(f"\n" + "=" * 70)
print(f"Saving to local directory: {local_csv}")
print("=" * 70)
df.to_csv(local_csv, index=False)
print("✓ Dataset saved locally")

# Save dataset info to JSON
info_file = os.path.join(os.path.dirname(__file__), "dataset_info.json")
info = {
    "shape": df.shape,
    "columns": df.columns.tolist(),
    "dtypes": df.dtypes.astype(str).to_dict(),
    "label_column": label_col,
}
if label_col:
    info["label_distribution"] = df[label_col].value_counts().to_dict()

with open(info_file, "w") as f:
    json.dump(info, f, indent=2)
print(f"✓ Dataset info saved to {info_file}")

print("\n" + "=" * 70)
print("Download and analysis complete!")
print("=" * 70)
