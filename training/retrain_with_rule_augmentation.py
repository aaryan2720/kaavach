"""Quick retrain that augments the training set with synthetic examples matching
the rule (state=REQ_RST and spkts>30) so the model learns to flag them.

This is an experimental helper — it trains a LogisticRegression pipeline and
saves `models/selected_model.joblib` and updates `models/model_metadata.json`.

Usage:
  python training/retrain_with_rule_augmentation.py --data UNSW_NB15.csv --augment 500
"""
from __future__ import annotations

from pathlib import Path
import argparse
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression


def build_preprocessor(X: pd.DataFrame):
    categorical_cols = X.select_dtypes(include=["object", "string"]).columns.tolist()
    numeric_cols = [c for c in X.columns if c not in categorical_cols]
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
        ],
        remainder="drop",
    )
    return preprocessor, numeric_cols, categorical_cols


def make_synthetic_rule_rows(n: int, template_row: pd.Series) -> pd.DataFrame:
    rows = []
    for i in range(n):
        r = template_row.copy()
        r["state"] = "REQ_RST"
        r["spkts"] = int(31 + np.random.poisson(10))
        r["dpkts"] = int(max(1, int(r.get("dpkts", 1) * np.random.uniform(0.1, 1.0))))
        r["sbytes"] = int(max(100, int(r.get("sbytes", 500) * np.random.uniform(0.5, 5.0))))
        r["dbytes"] = int(max(0, int(r.get("dbytes", 100) * np.random.uniform(0.1, 1.0))))
        r["rate"] = float(max(1.0, r.get("rate", 100) * np.random.uniform(0.5, 5.0)))
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="UNSW_NB15.csv")
    parser.add_argument("--models-dir", default="models")
    parser.add_argument("--augment", type=int, default=200)
    args = parser.parse_args()

    data_path = Path(args.data)
    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    df = pd.read_csv(data_path)

    if "label" not in df.columns:
        raise SystemExit("Dataset must include 'label' column (0/1)")

    # Use only feature columns (drop identifiers if present)
    drop_cols = ["label"]
    if "id" in df.columns:
        drop_cols.append("id")
    X = df.drop(columns=drop_cols).copy()
    y = df["label"].astype(int)

    # Create synthetic attack rows based on a random normal row
    template = X[y == 1].sample(1, random_state=42).iloc[0] if any(y == 1) else X.sample(1, random_state=42).iloc[0]
    synth = make_synthetic_rule_rows(args.augment, template)
    synth["label"] = 1

    # Append to original df
    df_aug = pd.concat([df, synth], ignore_index=True, sort=False)

    X_aug = df_aug.drop(columns=[c for c in ["label", "id"] if c in df_aug.columns]).copy()
    y_aug = df_aug["label"].astype(int)

    preprocessor, numeric_cols, categorical_cols = build_preprocessor(X_aug)

    model = LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear")
    pipe = Pipeline([("preprocessor", preprocessor), ("model", model)])

    print("Training logistic regression on augmented data... (this may take a moment)")
    pipe.fit(X_aug, y_aug)

    selected_path = models_dir / "selected_model.joblib"
    joblib.dump(pipe, selected_path)

    metadata = {
        "project": "kaavach",
        "label_column": "label",
        "training_data": str(data_path),
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "selected_model_name": "logistic_regression_augmented",
        "selected_threshold": 0.5,
        "artifact_paths": {"selected": str(selected_path)},
    }
    with open(models_dir / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("Saved augmented model and metadata to:")
    print(f" - {selected_path}")
    print(f" - {models_dir / 'model_metadata.json'}")


if __name__ == "__main__":
    main()
