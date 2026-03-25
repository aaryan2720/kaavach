# Model Architecture: ML Strategy & Implementation Plan

## Overview

This document specifies the machine learning architecture, algorithms, hyperparameters, evaluation methodology, and success criteria for the UNSW-NB15 intrusion detection project.

---

## 1. Model Development Strategy

### Core Philosophy

**False Positives First**: We optimize metrics in this priority order:

1. **FPR < 2%** ⭐ Primary (user experience, operational viability)
2. **Precision > 90%** (alert confidence)
3. **Recall > 85%** (catch rate, after FPR stable)

**Why?** One false alert costs $5-50 in analyst time. 10,000 daily alerts at 5% FPR = $2,500-$25,000 in wasted labor daily.

---

## 2. Phase 1: Baseline Models (Weeks 1-4)

### Goal
Establish interpretable baseline with FPR < 2% to understand feature relationships

### Models Selected

#### A. Logistic Regression

**Why**: Simplest linear classifier, fully interpretable

```python
# Pseudocode
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    penalty='l2',              # L2 regularization (Ridge)
    C=1.0,                     # Regularization strength (inverse)
    solver='lbfgs',            # optimization algorithm
    max_iter=1000,             # convergence iterations
    class_weight='balanced',   # handle 55%-45% imbalance
    random_state=42
)

model.fit(X_train_scaled, y_train)
```

**Hyperparameters to Tune**:
- `C` (regularization): [0.001, 0.01, 0.1, 1.0, 10.0]
- `penalty`: ['l1', 'l2'] (if solver supports)

**Pros**:
- Interpretable coefficients (feature importance)
- Fast training (< 1 second)
- Fast inference (< 1ms)
- Works as baseline

**Cons**:
- Linear only (cannot capture complex interactions)
- May underfit if patterns are non-linear

**Expected Performance**:
- FPR: 2.0-2.5%
- Precision: 85-87%
- Recall: 80-82%

---

#### B. Decision Tree

**Why**: Captures non-linear relationships, interpretable

```python
from sklearn.tree import DecisionTreeClassifier

model = DecisionTreeClassifier(
    max_depth=10,              # prevent overfitting
    min_samples_split=50,      # minimum samples to split
    min_samples_leaf=25,       # minimum samples in leaf
    class_weight='balanced',   # handle 55%-45% imbalance
    random_state=42
)

model.fit(X_train, y_train)  # No scaling needed
```

**Hyperparameters to Tune**:
- `max_depth`: [5, 10, 15, 20, 30]
- `min_samples_split`: [20, 50, 100]
- `min_samples_leaf`: [10, 25, 50]

**Pros**:
- Interpretable decision paths (if/then rules)
- Handles non-linear relationships
- No feature scaling needed
- Fast inference

**Cons**:
- Prone to overfitting (even with regularization)
- May not reach best performance

**Expected Performance**:
- FPR: 2.1-2.5%
- Precision: 83-86%
- Recall: 78-81%

---

### Phase 1 Training Workflow

```
Dataset: 82,332 flows
    ↓
[Stratified Split]
├─ Training: 52,693 flows (80% of 65,866)
├─ Validation: 13,173 flows (20% of 65,866)
└─ Test: 16,466 flows (hold-out, never seen)
    ↓
[Feature Engineering]
├─ Drop: 'id' (non-predictive)
├─ One-hot: proto, state
├─ Target-encode: service (131 → single numeric)
└─ Standardize: all numeric features
    ↓
[Hyperparameter Tuning - GridSearchCV]
├─ Logistic Regression:
│  └─ CV: 5-fold stratified
│     Parameters: C=[0.001, 0.01, 0.1, 1.0, 10.0]
│     Metric: f1 (balanced for imbalance)
│     Best: C=1.0 (example)
│
└─ Decision Tree:
   └─ CV: 5-fold stratified
      Parameters: max_depth=[5,10,15,20,30]
      Metric: f1
      Best: max_depth=15 (example)
    ↓
[Threshold Tuning]
├─ Default threshold: 0.5
├─ Sweep range: [0.1, 0.2, ..., 0.9]
├─ Calculate FPR, Precision, Recall for each
└─ Select threshold with FPR < 2%, max Recall
    ↓
[Final Validation on Hold-Out Test Set]
├─ Compute: FPR, Precision, Recall, F1, ROC-AUC
└─ Generate confusion matrix
    ↓
[Go/No-Go Decision]
├─ If FPR < 2%: PASS, Proceed to Phase 2
└─ If FPR ≥ 2%: FAIL, analyze features/data
```

### Evaluation: Phase 1

```python
from sklearn.metrics import (
    false_positive_rate,  # FP / (FP + TN)
    precision_score,      # TP / (TP + FP)
    recall_score,         # TP / (TP + FN)
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

# Compute metrics
fpr = false_positive_rate(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_pred_proba)

# Check success criteria
if fpr < 0.02 and precision > 0.85:
    print("✅ Phase 1 PASS - Ready for Phase 2")
else:
    print("❌ Phase 1 FAIL - Investigate features")
```

---

## 3. Phase 2: Ensemble Models (Weeks 5-10)

### Goal
Improve accuracy while maintaining FPR < 2%

### Models Selected

#### A. Random Forest

**Why**: Ensemble robustness, feature importance ranking

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=100,          # number of trees
    max_depth=15,              # tree depth
    min_samples_split=50,      # split criterion
    min_samples_leaf=25,       # leaf criterion
    max_features='sqrt',       # features per split
    class_weight='balanced',   # handle imbalance
    n_jobs=-1,                 # parallel processing
    random_state=42
)

model.fit(X_train_scaled, y_train)
```

**Hyperparameters to Tune**:
- `n_estimators`: [50, 100, 200, 300]
- `max_depth`: [10, 15, 20, 25]
- `min_samples_split`: [20, 50, 100]
- `max_features`: ['sqrt', 'log2']

**Pros**:
- Robust ensemble (averaging reduces overfitting)
- Good generalization
- Built-in feature importance
- Out-of-bag (OOB) error estimation

**Cons**:
- Longer training time (~10-30 seconds)
- Less interpretable (100 trees vs 1)

**Expected Performance**:
- FPR: 1.8-2.0%
- Precision: 91-93%
- Recall: 84-86%

---

#### B. XGBoost

**Why**: State-of-the-art gradient boosting

```python
import xgboost as xgb

model = xgb.XGBClassifier(
    n_estimators=100,          # boosting rounds
    max_depth=5,               # tree depth (shallower than RF)
    learning_rate=0.1,         # shrinkage parameter
    subsample=0.8,             # row subsampling
    colsample_bytree=0.8,      # column subsampling
    gamma=1,                   # minimum loss reduction
    scale_pos_weight=0.82,     # handle 55%-45% imbalance (1-class_weight)
    random_state=42
)

model.fit(X_train_scaled, y_train)
```

**Hyperparameters to Tune**:
- `max_depth`: [3, 5, 7, 9]
- `learning_rate`: [0.01, 0.05, 0.1, 0.2]
- `subsample`: [0.6, 0.8, 1.0]
- `colsample_bytree`: [0.6, 0.8, 1.0]
- `gamma`: [0, 0.5, 1, 2]

**Pros**:
- Best-in-class performance
- Fast training (GPU-accelerated option)
- Built-in regularization
- Native categorical support (new versions)

**Cons**:
- Slower than Random Forest (sequential boosting)
- Hyperparameter tuning critical
- Less interpretable

**Expected Performance**:
- FPR: 1.6-1.9%
- Precision: 93-95%
- Recall: 86-89%

---

### Phase 2 Training Workflow

```
[Random Search over hyperparameter space]
├─ RF Grid: 4 × 3 × 3 × 2 = 72 combinations
├─ XGB Grid: 4 × 4 × 3 × 3 × 5 = 720 combinations
│
├─ Sampling: Use RandomizedSearchCV (sample 100-200 combinations)
├─ CV: 5-fold stratified cross-validation
├─ Scoring: f1_micro (balance precision & recall)
└─ Time: 2-4 hours per model on 8-core CPU

    ↓
[Best Hyperparameters Found]
├─ RF best: n_estimators=200, max_depth=18, ...
├─ XGB best: max_depth=5, learning_rate=0.1, ...
│
[Train Final Models on Full Training Set]
├─ RF (best params): Fit on 52,693 flows
├─ XGB (best params): Fit on 52,693 flows
│
[Threshold Tuning]
├─ Sweep thresholds: [0.1, 0.15, 0.2, ..., 0.9]
├─ For each:
│  └─ Calculate FPR, Precision, Recall
├─ Select: FPR < 2%, max Recall
│
[Ensemble Voting]
├─ Combine RF + XGB predictions (averaging)
├─ threshold_ensemble = 0.5
│
[Validation on Hold-Out Test Set]
├─ 3 models: RF, XGB, Ensemble
├─ Compare performance
└─ Select best
    ↓
[Feature Importance Analysis (SHAP)]
├─ Install: pip install shap
├─ Generate SHAP values for top 100 test samples
├─ Plot: Feature importance, dependence plots
└─ Document findings
    ↓
[Phase 2 Report]
├─ Model comparison table
├─ Feature importance rankings
├─ Threshold configuration
└─ Go/No-Go (Proceed to Phase 3?)
```

### Cross-Validation Strategy

```python
from sklearn.model_selection import StratifiedKFold

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
    X_train_fold = X[train_idx]
    y_train_fold = y[train_idx]
    X_val_fold = X[val_idx]
    y_val_fold = y[val_idx]
    
    # Train model on fold
    model.fit(X_train_fold, y_train_fold)
    
    # Evaluate on validation fold
    y_pred = model.predict(X_val_fold)
    fpr = compute_fpr(y_val_fold, y_pred)
    
    print(f"Fold {fold}: FPR = {fpr:.3f}")

# Final: Average across 5 folds
print(f"Avg FPR: {avg_fpr:.3f} ± {std_fpr:.3f}")
```

---

## 4. Phase 3: Optimization & Deployment (Weeks 11-14)

### Goal
Maximize recall while maintaining FPR < 2%, prepare for production

### Optimization Techniques

#### 1. Threshold Tuning

```python
# Sweep thresholds and plot ROC-like curve
thresholds = np.linspace(0.1, 0.9, 50)
fpr_list, precision_list, recall_list = [], [], []

for thresh in thresholds:
    y_pred = (y_pred_proba[:, 1] >= thresh).astype(int)
    fpr = compute_fpr(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    
    fpr_list.append(fpr)
    precision_list.append(precision)
    recall_list.append(recall)

# Plot: threshold vs FPR, Precision, Recall
fig, (ax1, ax2) = plt.subplots(1, 2)

ax1.plot(thresholds, fpr_list, label='FPR', color='red')
ax1.axhline(y=0.02, color='r', linestyle='--', label='Target FPR')
ax1.set_xlabel('Decision Threshold')
ax1.set_ylabel('False Positive Rate')

ax2.plot(thresholds, precision_list, label='Precision', color='blue')
ax2.plot(thresholds, recall_list, label='Recall', color='green')
ax2.set_xlabel('Decision Threshold')
ax2.set_ylabel('Score')
ax2.legend()

plt.show()

# Select threshold: FPR < 2%, max recall
valid_idx = np.where(np.array(fpr_list) < 0.02)[0]
best_idx = valid_idx[np.argmax(np.array(recall_list)[valid_idx])]
best_threshold = thresholds[best_idx]
print(f"Best threshold: {best_threshold:.2f}")
```

**Expected result**: threshold ≈ 0.35-0.40 (lower than default 0.5)

#### 2. Class Weighting

```python
# Increase weight of minority positive class (attack)
# class_weight = {0: weight_0, 1: weight_1}
# weight_0 + weight_1 ≈ 2.0

class_weights = [
    {0: 0.82, 1: 1.18},  # slight weight increase
    {0: 0.64, 1: 1.36},  # moderate
    {0: 0.55, 1: 1.45},  # strong (inverse of class ratio)
]

best_model = None
best_f1 = 0

for weights in class_weights:
    model = xgb.XGBClassifier(
        ...,
        scale_pos_weight=weights[1] / weights[0],
        ...
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_val)
    f1 = f1_score(y_val, y_pred)
    
    if f1 > best_f1:
        best_f1 = f1
        best_model = model

print(f"Best F1 with weighting: {best_f1:.3f}")
```

#### 3. SMOTE Resampling (if recall still < 85%)

```python
from imblearn.over_sampling import SMOTE

# Generate synthetic attack samples
smote = SMOTE(sampling_strategy=0.8, random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)

print(f"Original: {X_train.shape}, New: {X_train_resampled.shape}")
print(f"Class balance before: {np.bincount(y_train)}")
print(f"Class balance after: {np.bincount(y_train_resampled)}")

# Train model on resampled data
model_smote = xgb.XGBClassifier(...).fit(X_train_resampled, y_train_resampled)

# Evaluate
y_pred = model_smote.predict(X_test)
new_recall = recall_score(y_test, y_pred)
print(f"Recall after SMOTE: {new_recall:.3f}")
```

#### 4. Ensemble Stacking (optional)

```python
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression

# Base learners
rf = RandomForestClassifier(n_estimators=200, max_depth=18)
xgb_model = xgb.XGBClassifier(max_depth=5, learning_rate=0.1)

# Meta-learner
meta_learner = LogisticRegression()

# Stacking
stacking = StackingClassifier(
    estimators=[('rf', rf), ('xgb', xgb_model)],
    final_estimator=meta_learner
)

stacking.fit(X_train, y_train)
y_pred = stacking.predict(X_test)
f1_stack = f1_score(y_test, y_pred)
print(f"Stacking F1: {f1_stack:.3f}")
```

---

## 5. Feature Importance & Explainability

### SHAP Analysis (Phase 3)

```python
import shap

# Create SHAP explainer
explainer = shap.TreeExplainer(best_model)
shap_values = explainer.shap_values(X_test[:1000])  # First 1000 samples

# Global importance
shap.summary_plot(shap_values, X_test[:1000], plot_type="bar")
plt.title("Top 20 Important Features (SHAP)")
plt.show()

# Individual prediction explanation
shap.force_plot(
    explainer.expected_value,
    shap_values[0],
    X_test.iloc[0]
)
```

**Output**: 
```
Feature                Impact (SHAP)
─────────────────────────────────────
1. ct_dst_ltm              +0.35     (high connection count → attack signal)
2. dload                   +0.28     (high download rate → attack)
3. sload                   +0.25     (high upload rate → attack)
4. rate                    +0.19     (high packet rate → DoS)
5. ct_src_ltm              +0.17     (many sources → suspicious)
...
30. id                     +0.00     (no impact - dropped for Phase 3)
```

---

## 6. Final Model Evaluation

### Metrics Summary (Phase 3 Target)

| Metric | Phase 1 Baseline | Phase 2 Strong | Phase 3 Final | Target |
|--------|----------|----------|----------|--------|
| **FPR** | 2.0% | 1.8% | 1.8% | < 2% ✓ |
| **Precision** | 86% | 92% | 92.5% | > 90% ✓ |
| **Recall** | 81% | 87% | 88% | > 85% ✓ |
| **F1-Score** | 0.83 | 0.89 | 0.90 | > 0.87 ✓ |
| **ROC-AUC** | 0.93 | 0.97 | 0.975 | > 0.95 ✓ |

### Confusion Matrix (Example - Phase 3)

```
                Predicted
                Normal    Attack
Actual  Normal     36,432     244    (FPR = 244/36,676 = 0.67%)
        Attack        568    15,094  (FNR = 568/15,662 = 3.62%)

True Negatives:  36,432
False Positives:    244 ← Keep < 2% of normal traffic
True Positives:  15,094
False Negatives:    568 ← Miss 3.62% of attacks (acceptable)
```

### Per-Attack-Type Performance

| Attack Type | Precision | Recall | F1-Score | N Samples |
|---|---|---|---|---|
| DoS | 95% | 87% | 0.91 | 1,278 |
| Exploits | 91% | 89% | 0.90 | 1,516 |
| Backdoor | 94% | 85% | 0.89 | 482 |
| Fuzzer | 88% | 91% | 0.89 | 1,231 |
| Generic | 90% | 86% | 0.88 | 2,188 |
| Reconnaissance | 86% | 79% | 0.82 | 715 |
| Worms | 92% | 83% | 0.87 | 485 |
| Shellcode | 89% | 76% | 0.82 | 301 |
| Analysis | 75% | 50% | 0.60 | 52 |
| **Macro Average** | **89% | **83% | **0.85** | 7,848 |

---

## 7. Model Serialization & Deployment

### Save Final Model

```python
import pickle
import json

# Save model
model_path = 'models/best_model_phase3.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(best_model, f)

# Save scaler
scaler_path = 'models/feature_scaler.pkl'
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)

# Save metadata
metadata = {
    'model_type': 'XGBoost',
    'phase': 3,
    'threshold': 0.38,
    'training_date': '2024-01-15',
    'metrics': {
        'fpr': 0.018,
        'precision': 0.925,
        'recall': 0.88,
        'f1': 0.90
    },
    'features': feature_names,
    'feature_count': 28,
    'categorical_features': ['proto_TCP', 'proto_UDP', 'state_CON', ...],
}

with open('models/model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"✅ Model saved to {model_path}")
```

### Load & Use Model

```python
def load_model(model_path, scaler_path):
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    return model, scaler

def predict_flow(flow_dict, model, scaler, threshold=0.38):
    """
    Predict if network flow is attack
    
    Args:
        flow_dict: Dict with 44 features
        model: Loaded XGBoost model
        scaler: Loaded feature scaler
        threshold: Decision threshold
        
    Returns:
        Dict with prediction, probability, explanation
    """
    
    # Feature engineering
    X = engineer_features(flow_dict)  # 1×44 array
    X_scaled = scaler.transform(X)
    
    # Prediction
    y_pred_proba = model.predict_proba(X_scaled)[0, 1]
    y_pred = 1 if y_pred_proba >= threshold else 0
    
    # Explanation (SHAP)
    shap_values = explainer.shap_values(X_scaled)[0]
    
    return {
        'label': 'Attack' if y_pred == 1 else 'Normal',
        'confidence': y_pred_proba,
        'threshold': threshold,
        'top_features': get_top_shap_features(shap_values, n=5)
    }

# Usage
model, scaler = load_model('models/best_model.pkl', 'models/scaler.pkl')
result = predict_flow(flow_dict, model, scaler)
print(result)
# {'label': 'Attack', 'confidence': 0.92, 'threshold': 0.38, 
#  'top_features': [('dload', 0.35), ('ct_dst_ltm', 0.28), ...]}
```

---

## 8. Success Criteria Checkpoints

### ✅ Phase 1 Success (Week 4)
- FPR ≤ 2.0% on test set
- Precision ≥ 85%
- Recall ≥ 80%
- Feature importance documented
- **Decision**: Go to Phase 2

### ✅ Phase 2 Success (Week 10)
- FPR ≤ 2.0% (maintained)
- Precision ≥ 90%
- Recall ≥ 85%
- Cross-validation consistent (< 5% std)
- **Decision**: Go to Phase 3

### ✅ Phase 3 Success (Week 14)
- FPR 1.5-2.0%
- Precision ≥ 92%
- Recall ≥ 88%
- Latency < 50ms (P95)
- **Decision**: Ready for production deployment

---

## 9. Monitoring & Maintenance (Post-Deployment)

### Real-Time Performance Monitoring

```python
def monitor_model_performance(predictions, actual_labels, window_size=1000):
    """
    Monitor model performance in production
    Alert if drift detected
    """
    
    # Sliding window metrics
    recent_fpr = compute_fpr(actual_labels[-window_size:], 
                             predictions[-window_size:])
    
    baseline_fpr = 0.018  # Phase 3 target
    drift_threshold = 0.05  # 5% increase = alert
    
    if recent_fpr > baseline_fpr * (1 + drift_threshold):
        send_alert(f"⚠️ FPR DRIFT: {recent_fpr:.3f} (baseline: {baseline_fpr:.3f})")
        trigger_retraining_review()
    
    return {
        'current_fpr': recent_fpr,
        'baseline_fpr': baseline_fpr,
        'drift_detected': recent_fpr > baseline_fpr * 1.05
    }
```

### Retraining Strategy
- Monthly: Collect new data, evaluate performance
- Quarterly: Retrain if FPR > 2.5% or recall < 80%
- Yearly: Full model review + feature update

---

**Architecture Version**: 1.0  
**Last Updated**: 2024  
**Expected Deployment**: Week 14 of project  
**Model Type**: XGBoost (Phase 3)  
**Status**: Ready for Phase 1 Implementation
