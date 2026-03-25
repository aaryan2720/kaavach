# Cyber Attack Detection Model Reading Plan

## 1) Problem Scope (Phase 1)
- Primary task: Network intrusion detection and attack prediction using UNSW-NB15.
- Initial optimization goal: Minimize false positives.
- Secondary optimization goal: Increase attack recall after false-positive control is stable.
- Validation goal: Cross-dataset evaluation to measure generalization.

## 2) Data We Have
- Dataset now: UNSW-NB15.
- Data type: Structured tabular data (flow/network features + labels).
- Typical labels:
  - `label`: binary (normal vs attack)
  - `attack_cat`: multiclass attack family (if available in file)

## 3) Future Expansion
- Later phase: Malware annual detection module.
- Note: Malware classification datasets are usually a separate task/pipeline with different features.

## 4) Algorithm Strategy

### Phase A: Baseline (Low complexity, interpretable)
- Logistic Regression (binary baseline)
- Decision Tree (interpretable splits)

### Phase B: Strong tabular models
- Random Forest
- XGBoost / LightGBM (if environment allows)

### Phase C: Recall optimization
- Threshold tuning (decision threshold < 0.5 when needed)
- Class weights and cost-sensitive learning
- Optional re-sampling (SMOTE) after baseline checks

## 5) Structured vs Unstructured Mapping
- UNSW-NB15: Structured -> best with classical ML on tabular features.
- Malware binaries/text artifacts (future): often semi-structured/unstructured -> may need separate feature extraction pipeline.

## 6) Evaluation Metrics (Priority Order)
1. False Positive Rate (FPR) -> highest priority now
2. Precision for attack class
3. Recall for attack class (priority increases in next phase)
4. F1-score (class-wise)
5. Confusion matrix

## 7) Cross-Dataset Validation Plan
- Train on UNSW-NB15.
- Validate on held-out UNSW split first.
- Then test external dataset (for example CICIDS) using aligned features.
- Track performance drop to quantify domain shift.

## 8) EDA and Visualization Required Now
- Basic info (shape, columns, dtypes)
- Missing values report
- Class distribution
- Bar chart for class counts
- Correlation heatmap (numeric columns)
- Summary statistics
- Unique values per column

## 9) Immediate Next Deliverables
- Python EDA script for UNSW-NB15 (completed as `unsw_nb15_analysis.py`).
- Run EDA, inspect label quality and imbalance.
- Finalize first training-ready feature set.