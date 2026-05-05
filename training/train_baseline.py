"""
Baseline training pipeline for kaavach (UNSW-NB15).

Implements:
1) Preprocessing pipeline (numeric + categorical)
2) Baseline model training (Logistic Regression, Decision Tree)
3) Threshold tuning with FPR-first objective
4) Held-out validation metrics
5) Artifact export for API integration

Usage:
    python training/train_baseline.py --data UNSW_NB15.csv
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


@dataclass
class EvalResult:
    model_name: str
    threshold: float
    fpr: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    tn: int
    fp: int
    fn: int
    tp: int


def load_dataset(data_path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(data_path, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(data_path, encoding="latin1")


def split_features_target(df: pd.DataFrame, label_col: str = "label") -> tuple[pd.DataFrame, pd.Series]:
    if label_col not in df.columns:
        raise ValueError(f"Expected target column '{label_col}' in dataset")

    # Keep attack_cat for future multiclass work, but exclude for binary target training.
    drop_cols = [label_col]
    if "attack_cat" in df.columns:
        drop_cols.append("attack_cat")
    # `id` is an identifier, not a behavioral feature.
    if "id" in df.columns:
        drop_cols.append("id")

    X = df.drop(columns=drop_cols).copy()
    y = df[label_col].astype(int)
    return X, y


def build_preprocessor(X: pd.DataFrame) -> tuple[ColumnTransformer, list[str], list[str]]:
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


def metrics_at_threshold(y_true: np.ndarray, proba: np.ndarray, threshold: float) -> dict[str, Any]:
    y_pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_true, proba)

    return {
        "threshold": float(threshold),
        "fpr": float(fpr),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def tune_threshold(
    y_true: np.ndarray,
    proba: np.ndarray,
    min_precision: float = 0.85,
    min_recall: float = 0.70,
) -> dict[str, Any]:
    thresholds = np.linspace(0.05, 0.95, 181)
    all_metrics = [metrics_at_threshold(y_true, proba, thr) for thr in thresholds]

    feasible = [
        m for m in all_metrics if m["precision"] >= min_precision and m["recall"] >= min_recall
    ]

    # FPR-first objective: among feasible points minimize FPR, then maximize recall.
    if feasible:
        best = sorted(feasible, key=lambda m: (m["fpr"], -m["recall"], -m["precision"]))[0]
    else:
        # Fallback: best FPR regardless of constraints.
        best = sorted(all_metrics, key=lambda m: (m["fpr"], -m["recall"], -m["precision"]))[0]

    return {
        "selected": best,
        "constraints": {
            "min_precision": min_precision,
            "min_recall": min_recall,
            "constraints_met": bool(feasible),
        },
    }


def train_and_evaluate(
    model_name: str,
    estimator,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    preprocessor: ColumnTransformer,
) -> tuple[Pipeline, EvalResult, dict[str, Any]]:
    pipe = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", estimator),
        ]
    )

    pipe.fit(X_train, y_train)
    proba = pipe.predict_proba(X_val)[:, 1]

    threshold_info = tune_threshold(y_val.to_numpy(), proba)
    chosen = threshold_info["selected"]

    result = EvalResult(
        model_name=model_name,
        threshold=float(chosen["threshold"]),
        fpr=float(chosen["fpr"]),
        precision=float(chosen["precision"]),
        recall=float(chosen["recall"]),
        f1=float(chosen["f1"]),
        roc_auc=float(chosen["roc_auc"]),
        tn=int(chosen["tn"]),
        fp=int(chosen["fp"]),
        fn=int(chosen["fn"]),
        tp=int(chosen["tp"]),
    )

    return pipe, result, threshold_info


def as_dict(result: EvalResult) -> dict[str, Any]:
    return {
        "model_name": result.model_name,
        "threshold": result.threshold,
        "fpr": result.fpr,
        "precision": result.precision,
        "recall": result.recall,
        "f1": result.f1,
        "roc_auc": result.roc_auc,
        "confusion_matrix": {
            "tn": result.tn,
            "fp": result.fp,
            "fn": result.fn,
            "tp": result.tp,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train baseline models for kaavach")
    parser.add_argument("--data", default="UNSW_NB15.csv", help="Path to dataset CSV")
    parser.add_argument("--models-dir", default="models", help="Directory to save model artifacts")
    parser.add_argument("--test-size", type=float, default=0.2, help="Validation split size")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    data_path = Path(args.data)
    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    print("Loading dataset...")
    df = load_dataset(data_path)
    X, y = split_features_target(df, label_col="label")

    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    preprocessor, numeric_cols, categorical_cols = build_preprocessor(X_train)

    lr_estimator = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        solver="liblinear",
        random_state=args.random_state,
    )
    dt_estimator = DecisionTreeClassifier(
        max_depth=12,
        min_samples_leaf=10,
        class_weight="balanced",
        random_state=args.random_state,
    )

    print("Training Logistic Regression baseline...")
    lr_pipe, lr_result, lr_threshold = train_and_evaluate(
        "logistic_regression", lr_estimator, X_train, y_train, X_val, y_val, preprocessor
    )

    print("Training Decision Tree baseline...")
    dt_pipe, dt_result, dt_threshold = train_and_evaluate(
        "decision_tree", dt_estimator, X_train, y_train, X_val, y_val, preprocessor
    )

    results = [lr_result, dt_result]
    # FPR-first model selection.
    best = sorted(results, key=lambda r: (r.fpr, -r.recall, -r.precision))[0]

    print("\nValidation summary (FPR-first):")
    for r in results:
        print(
            f"- {r.model_name}: FPR={r.fpr:.4f}, Precision={r.precision:.4f}, "
            f"Recall={r.recall:.4f}, F1={r.f1:.4f}, Threshold={r.threshold:.3f}"
        )
    print(f"Selected model: {best.model_name}")

    # Save artifacts.
    lr_path = models_dir / "baseline_logistic_regression.joblib"
    dt_path = models_dir / "baseline_decision_tree.joblib"
    selected_path = models_dir / "selected_model.joblib"

    joblib.dump(lr_pipe, lr_path)
    joblib.dump(dt_pipe, dt_path)
    if best.model_name == "logistic_regression":
        joblib.dump(lr_pipe, selected_path)
        best_threshold = lr_threshold
    else:
        joblib.dump(dt_pipe, selected_path)
        best_threshold = dt_threshold

    metrics_payload = {
        "project": "kaavach",
        "dataset": str(data_path),
        "rows": int(len(df)),
        "feature_count_raw": int(X.shape[1]),
        "train_size": int(len(X_train)),
        "validation_size": int(len(X_val)),
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "baseline_results": [as_dict(lr_result), as_dict(dt_result)],
        "selected_model": as_dict(best),
    }

    metadata_payload = {
        "project": "kaavach",
        "label_column": "label",
        "training_data": str(data_path),
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "selected_model_name": best.model_name,
        "selected_threshold": best.threshold,
        "artifact_paths": {
            "logistic_regression": str(lr_path),
            "decision_tree": str(dt_path),
            "selected": str(selected_path),
        },
    }

    with open(models_dir / "baseline_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    with open(models_dir / "threshold_tuning.json", "w", encoding="utf-8") as f:
        json.dump(best_threshold, f, indent=2)

    with open(models_dir / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata_payload, f, indent=2)

    print("\nSaved artifacts:")
    print(f"- {lr_path}")
    print(f"- {dt_path}")
    print(f"- {selected_path}")
    print(f"- {models_dir / 'baseline_metrics.json'}")
    print(f"- {models_dir / 'threshold_tuning.json'}")
    print(f"- {models_dir / 'model_metadata.json'}")


if __name__ == "__main__":
    main()
