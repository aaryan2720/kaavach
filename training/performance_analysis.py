"""
Performance analysis for kaavach baseline models.

Generates:
- Comparative metrics for Logistic Regression and Decision Tree
- Overfitting check (train vs validation delta)
- Chart suite (ROC, PR, threshold trade-offs, confusion matrices, score distribution)
- A structured performance report in performance_analysis/README.md

Usage:
    python training/performance_analysis.py --data UNSW_NB15.csv --outdir performance_analysis
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    auc,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from train_baseline import build_preprocessor, load_dataset, split_features_target, tune_threshold

sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)


def metric_pack(y_true: np.ndarray, y_proba: np.ndarray, threshold: float) -> dict[str, Any]:
    y_pred = (y_proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    return {
        "threshold": float(threshold),
        "fpr": float(fpr),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def build_model(name: str, random_state: int):
    if name == "logistic_regression":
        return LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            solver="liblinear",
            random_state=random_state,
        )
    if name == "decision_tree":
        return DecisionTreeClassifier(
            max_depth=12,
            min_samples_leaf=10,
            class_weight="balanced",
            random_state=random_state,
        )
    raise ValueError(f"Unknown model: {name}")


def threshold_curve(y_true: np.ndarray, y_proba: np.ndarray) -> pd.DataFrame:
    rows = []
    for thr in np.linspace(0.01, 0.99, 197):
        m = metric_pack(y_true, y_proba, thr)
        rows.append(m)
    return pd.DataFrame(rows)


def write_markdown_report(
    outdir: Path,
    selected_model: str,
    selected_threshold: float,
    model_eval: dict[str, Any],
    suggestions: list[str],
) -> None:
    lr = model_eval["logistic_regression"]
    dt = model_eval["decision_tree"]

    content = f"""# Kaavach Performance Analysis

## Summary
- Dataset: UNSW-NB15
- Models analyzed: Logistic Regression, Decision Tree
- Selection objective: Lowest False Positive Rate (FPR), then higher Recall
- Selected model: **{selected_model}**
- Selected threshold: **{selected_threshold:.3f}**

## Validation Metrics

| Model | FPR | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | {lr['val']['fpr']:.4f} | {lr['val']['precision']:.4f} | {lr['val']['recall']:.4f} | {lr['val']['f1']:.4f} | {lr['val']['roc_auc']:.4f} |
| Decision Tree | {dt['val']['fpr']:.4f} | {dt['val']['precision']:.4f} | {dt['val']['recall']:.4f} | {dt['val']['f1']:.4f} | {dt['val']['roc_auc']:.4f} |

## Generalization (Train vs Validation)

| Model | Train F1 | Validation F1 | F1 Gap |
|---|---:|---:|---:|
| Logistic Regression | {lr['train']['f1']:.4f} | {lr['val']['f1']:.4f} | {lr['generalization_gap_f1']:.4f} |
| Decision Tree | {dt['train']['f1']:.4f} | {dt['val']['f1']:.4f} | {dt['generalization_gap_f1']:.4f} |

## Chart Pack
- [ROC Curve Comparison](plots/01_roc_curve_comparison.png)
- [Precision-Recall Curve Comparison](plots/02_precision_recall_curve_comparison.png)
- [Threshold Trade-off (Selected Model)](plots/03_threshold_tradeoff_selected_model.png)
- [Confusion Matrices](plots/04_confusion_matrix_comparison.png)
- [Score Distribution (Selected Model)](plots/05_score_distribution_selected_model.png)

## Improvement Plan
"""

    for item in suggestions:
        content += f"- {item}\n"

    content += """
## Implementation Priority (Next Sprint)
1. Keep current selected model for low-FPR production guardrail.
2. Train Random Forest and XGBoost using same preprocessing and threshold-tuning objective.
3. Add probability calibration (Platt/Isotonic) and retune threshold.
4. Add stratified cross-validation and external validation (CICIDS) before production promotion.
5. Introduce drift monitoring for score and class distribution in API logs.
"""

    (outdir / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate performance analysis for baseline models")
    parser.add_argument("--data", default="UNSW_NB15.csv")
    parser.add_argument("--outdir", default="performance_analysis")
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    plots_dir = outdir / "plots"
    outdir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    df = load_dataset(Path(args.data))
    X, y = split_features_target(df, label_col="label")

    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    preprocessor, _, _ = build_preprocessor(X_train)

    eval_data: dict[str, Any] = {}
    all_val_proba: dict[str, np.ndarray] = {}
    all_train_proba: dict[str, np.ndarray] = {}
    tuned_thresholds: dict[str, float] = {}

    for model_name in ["logistic_regression", "decision_tree"]:
        model = build_model(model_name, args.random_state)
        pipe = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", model),
            ]
        )
        pipe.fit(X_train, y_train)

        train_proba = pipe.predict_proba(X_train)[:, 1]
        val_proba = pipe.predict_proba(X_val)[:, 1]

        chosen = tune_threshold(y_val.to_numpy(), val_proba)["selected"]
        threshold = float(chosen["threshold"])
        tuned_thresholds[model_name] = threshold

        train_metrics = metric_pack(y_train.to_numpy(), train_proba, threshold)
        val_metrics = metric_pack(y_val.to_numpy(), val_proba, threshold)

        eval_data[model_name] = {
            "train": train_metrics,
            "val": val_metrics,
            "generalization_gap_f1": float(train_metrics["f1"] - val_metrics["f1"]),
        }
        all_val_proba[model_name] = val_proba
        all_train_proba[model_name] = train_proba

    selected_model = sorted(
        ["logistic_regression", "decision_tree"],
        key=lambda m: (eval_data[m]["val"]["fpr"], -eval_data[m]["val"]["recall"], -eval_data[m]["val"]["precision"]),
    )[0]
    selected_threshold = tuned_thresholds[selected_model]

    # Chart 1: ROC comparison
    plt.figure(figsize=(10, 6))
    for model_name in ["logistic_regression", "decision_tree"]:
        fpr, tpr, _ = roc_curve(y_val, all_val_proba[model_name])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, linewidth=2, label=f"{model_name} (AUC={roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.5)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "01_roc_curve_comparison.png", dpi=150)
    plt.close()

    # Chart 2: PR comparison
    plt.figure(figsize=(10, 6))
    for model_name in ["logistic_regression", "decision_tree"]:
        precision, recall, _ = precision_recall_curve(y_val, all_val_proba[model_name])
        pr_auc = auc(recall, precision)
        plt.plot(recall, precision, linewidth=2, label=f"{model_name} (AUC={pr_auc:.4f})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "02_precision_recall_curve_comparison.png", dpi=150)
    plt.close()

    # Chart 3: Threshold trade-off for selected model
    selected_curve = threshold_curve(y_val.to_numpy(), all_val_proba[selected_model])
    plt.figure(figsize=(10, 6))
    plt.plot(selected_curve["threshold"], selected_curve["fpr"], label="FPR", linewidth=2)
    plt.plot(selected_curve["threshold"], selected_curve["precision"], label="Precision", linewidth=2)
    plt.plot(selected_curve["threshold"], selected_curve["recall"], label="Recall", linewidth=2)
    plt.axvline(selected_threshold, color="red", linestyle="--", label=f"Selected={selected_threshold:.3f}")
    plt.xlabel("Threshold")
    plt.ylabel("Metric Value")
    plt.title(f"Threshold Trade-off ({selected_model})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "03_threshold_tradeoff_selected_model.png", dpi=150)
    plt.close()

    # Chart 4: Confusion matrices
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for i, model_name in enumerate(["logistic_regression", "decision_tree"]):
        m = eval_data[model_name]["val"]
        cm = np.array([[m["tn"], m["fp"]], [m["fn"], m["tp"]]])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=axes[i])
        axes[i].set_title(f"{model_name} @ thr={tuned_thresholds[model_name]:.3f}")
        axes[i].set_xlabel("Predicted")
        axes[i].set_ylabel("Actual")
        axes[i].set_xticklabels(["Normal", "Attack"])
        axes[i].set_yticklabels(["Normal", "Attack"])
    plt.tight_layout()
    plt.savefig(plots_dir / "04_confusion_matrix_comparison.png", dpi=150)
    plt.close()

    # Chart 5: Score distribution for selected model
    selected_scores = all_val_proba[selected_model]
    y_val_np = y_val.to_numpy()
    plt.figure(figsize=(10, 6))
    plt.hist(selected_scores[y_val_np == 0], bins=50, alpha=0.6, label="Actual Normal")
    plt.hist(selected_scores[y_val_np == 1], bins=50, alpha=0.6, label="Actual Attack")
    plt.axvline(selected_threshold, color="red", linestyle="--", label=f"Selected={selected_threshold:.3f}")
    plt.xlabel("Predicted Attack Probability")
    plt.ylabel("Count")
    plt.title(f"Score Distribution ({selected_model})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "05_score_distribution_selected_model.png", dpi=150)
    plt.close()

    suggestions: list[str] = []
    sel_val = eval_data[selected_model]["val"]

    if sel_val["recall"] < 0.85:
        suggestions.append(
            "Recall is below target (>0.85). Keep FPR guardrail, then train ensemble models (Random Forest/XGBoost) and retune threshold to increase attack catch rate."
        )
    if eval_data["decision_tree"]["generalization_gap_f1"] > 0.05:
        suggestions.append(
            "Decision Tree shows a larger train-validation F1 gap; use stronger regularization or move to ensembles to reduce overfitting."
        )
    suggestions.append(
        "Run stratified 5-fold cross-validation and report mean/std for FPR, precision, recall to ensure threshold stability."
    )
    suggestions.append(
        "Calibrate probabilities (Platt or isotonic) before threshold tuning for more reliable confidence scores."
    )
    suggestions.append(
        "Proceed with cross-dataset validation (CICIDS) to quantify domain-shift and robustness before production rollout."
    )

    summary = {
        "project": "kaavach",
        "selected_model": selected_model,
        "selected_threshold": selected_threshold,
        "evaluation": eval_data,
        "improvement_suggestions": suggestions,
        "charts": [
            "plots/01_roc_curve_comparison.png",
            "plots/02_precision_recall_curve_comparison.png",
            "plots/03_threshold_tradeoff_selected_model.png",
            "plots/04_confusion_matrix_comparison.png",
            "plots/05_score_distribution_selected_model.png",
        ],
    }

    with open(outdir / "performance_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    write_markdown_report(outdir, selected_model, selected_threshold, eval_data, suggestions)

    print(f"Performance analysis completed. Report folder: {outdir}")


if __name__ == "__main__":
    main()
