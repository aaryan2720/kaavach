# Kaavach Performance Analysis

## Summary
- Dataset: UNSW-NB15
- Models analyzed: Logistic Regression, Decision Tree
- Selection objective: Lowest False Positive Rate (FPR), then higher Recall
- Selected model: **logistic_regression**
- Selected threshold: **0.895**

## Validation Metrics

| Model | FPR | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.0015 | 0.9983 | 0.7014 | 0.8239 | 0.9782 |
| Decision Tree | 0.0065 | 0.9941 | 0.8964 | 0.9428 | 0.9916 |

## Generalization (Train vs Validation)

| Model | Train F1 | Validation F1 | F1 Gap |
|---|---:|---:|---:|
| Logistic Regression | 0.8275 | 0.8239 | 0.0035 |
| Decision Tree | 0.9531 | 0.9428 | 0.0103 |

## Chart Pack
- [ROC Curve Comparison](plots/01_roc_curve_comparison.png)
- [Precision-Recall Curve Comparison](plots/02_precision_recall_curve_comparison.png)
- [Threshold Trade-off (Selected Model)](plots/03_threshold_tradeoff_selected_model.png)
- [Confusion Matrices](plots/04_confusion_matrix_comparison.png)
- [Score Distribution (Selected Model)](plots/05_score_distribution_selected_model.png)

## Improvement Plan
- Recall is below target (>0.85). Keep FPR guardrail, then train ensemble models (Random Forest/XGBoost) and retune threshold to increase attack catch rate.
- Run stratified 5-fold cross-validation and report mean/std for FPR, precision, recall to ensure threshold stability.
- Calibrate probabilities (Platt or isotonic) before threshold tuning for more reliable confidence scores.
- Proceed with cross-dataset validation (CICIDS) to quantify domain-shift and robustness before production rollout.

## Implementation Priority (Next Sprint)
1. Keep current selected model for low-FPR production guardrail.
2. Train Random Forest and XGBoost using same preprocessing and threshold-tuning objective.
3. Add probability calibration (Platt/Isotonic) and retune threshold.
4. Add stratified cross-validation and external validation (CICIDS) before production promotion.
5. Introduce drift monitoring for score and class distribution in API logs.
