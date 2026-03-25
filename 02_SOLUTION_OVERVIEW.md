# Solution Overview: ML-Based Network Intrusion Detection

## Executive Summary

This document outlines the **technical approach**, **architecture**, and **methodology** for building a machine learning-based intrusion detection system using the UNSW-NB15 dataset.

---

## 1. What We're Building

### System Vision

A **production-ready ML model** that:
- ✅ Classifies network flows as **Normal or Attack** in real-time
- ✅ Identifies **attack type** (10 categories)
- ✅ Reduces **false positives** to < 2% (vs 20-50% for signature-based systems)
- ✅ Maintains **high precision** (> 90%)
- ✅ Achieves **high recall** (> 85%)
- ✅ Operates at **8,500+ flows/second** throughput
- ✅ Provides **inference latency < 50ms**

### Key Characteristics

| Aspect | Details |
|--------|---------|
| **Input** | Network flow records (45 attributes) |
| **Output** | Binary prediction (Attack=1, Normal=0) + Attack type (10 classes) |
| **Decision Basis** | Behavioral patterns, not signatures |
| **Scale** | 8,500+ flows analyzed per second |
| **Latency** | < 50ms per flow |
| **Accuracy Target** | FPR < 2%, Precision > 90%, Recall > 85% |

---

## 2. Technical Approach: 3-Phase Strategy

### Philosophy: Prioritize False Positives First

**Why?**
- False positives → analyst alert fatigue → ignored alerts → missed real attacks
- Each false alert = $25-$50 in investigation cost
- High FPR makes system unusable operationally
- Once FPR is stable, optimize for recall

### Phase 1: Baseline Models (FPR Optimization)

**Goal**: Establish low FPR with interpretable models

**Models**:
1. **Logistic Regression**
   - Simplest linear classifier
   - Interpretable coefficients (feature importance)
   - Fast inference
   - Purpose: Understand feature relationships

2. **Decision Tree**
   - Rule-based classification
   - Interpretable decision paths
   - CapturesNon-linear relationships
   - Purpose: Identify feature interactions

**Approach**:
```
Data (82,332 flows)
    ↓
[Train/Validation Split: 80/20]
    ↓
[Feature Scaling & Encoding]
    ↓
[Model A: Logistic Regression] → [Threshold Tuning] → FPR, Precision, Recall
[Model B: Decision Tree]       → [Threshold Tuning] → Compare performance
    ↓
[Select baseline with FPR < 2%]
    ↓
[Analyze feature importance]
    ↓
[Document findings for Phase 2]
```

**Success Criteria**:
- FPR ≤ 2% on validation set
- Precision ≥ 85%
- Model is interpretable
- Feature importance is documented

**Deliverables**:
- Baseline model (pickle file)
- Performance metrics report
- Feature importance analysis
- Threshold configuration

---

### Phase 2: Strong Ensemble Models (Accuracy Optimization)

**Goal**: Improve overall accuracy while maintaining FPR < 2%

**Models**:
1. **Random Forest**
   - Ensemble of decision trees
   - Out-of-bag (OOB) error estimation
   - Built-in feature importance
   - Robust to outliers

2. **XGBoost / LightGBM**
   - Gradient boosting (sequential tree building)
   - State-of-the-art performance
   - Handles complex non-linear patterns
   - Fast training & inference

**Approach**:
```
Data (82,332 flows)
    ↓
[K-Fold Cross-Validation: 5-fold]
    ↓
[Hyperparameter Grid Search]
    ├─ RF: (n_estimators, max_depth, min_samples_leaf)
    └─ XGB: (learning_rate, max_depth, subsample, gamma)
    ↓
[Train ensemble models]
    ├─ Random Forest (optimized)
    ├─ XGBoost (optimized)
    └─ Voting Ensemble (RF + XGB)
    ↓
[Threshold tuning on validation set]
    ↓
[Compare vs Phase 1 baseline]
    ↓
[Select best model]
```

**Success Criteria**:
- FPR ≤ 2% maintained
- Precision ≥ 90%
- Recall ≥ 85%
- Performance gains documented vs baseline

**Deliverables**:
- Optimized ensemble models (3 variants)
- Cross-validation results
- Hyperparameter configurations
- Feature importance (SHAP analysis)
- Performance comparison report

---

### Phase 3: Optimization & Deployment (Recall Improvement)

**Goal**: Fine-tune model and prepare for production deployment

**Techniques**:

1. **Threshold Optimization**
   - Default threshold = 0.5
   - Adjust to 0.3-0.4 for higher recall
   - Monitor FPR constraint

2. **Class Weighting**
   - Weight attack class higher (minimize missed attacks)
   - Penalize false negatives more than false positives

3. **SMOTE Resampling** (if needed)
   - Synthetic minority oversampling
   - Generate synthetic attack samples
   - Improve recall without threshold manipulation

4. **Cost-Sensitive Learning**
   - Custom loss function: misclassification_cost × error
   - Adjust costs to business priorities

**Approach**:
```
Best Phase 2 Model
    ↓
[Threshold Sweep: 0.1 to 0.9]
    ↓
[For each threshold, calculate FPR, Precision, Recall]
    ↓
[Select threshold maintaining FPR < 2% with max Recall]
    ↓
[Class Weighting Experiments]
    ├─ Try weights: 1:1, 1:2, 1:3, 1:5
    └─ Measure FPR, Recall improvements
    ↓
[If recall still < 85%, apply SMOTE]
    ├─ Generate synthetic attack samples
    └─ Retrain with balanced classes
    ↓
[Final model validation on held-out test set]
```

**Success Criteria**:
- FPR ≤ 2%
- Precision ≥ 90%
- Recall ≥ 85%

**Deliverables**:
- Final production model
- Threshold configuration
- Class weight settings
- Test set evaluation report
- Model card (metadata)

---

## 3. Feature Engineering Pipeline

### Input Features (44 attributes)

The model accepts 44 network flow attributes across 10 categories:

**Category 1: Flow Metadata (5)**
- `id`, `dur`, `proto`, `service`, `state`

**Category 2: Packet/Byte Counts (4)**
- `spkts`, `dpkts`, `sbytes`, `dbytes`

**Category 3: Rates & Loads (4)**
- `rate`, `sload`, `dload`, `sinpkt`, `dinpkt`

**Category 4: TTL & Loss (4)**
- `sttl`, `dttl`, `sloss`, `dloss`

**Category 5: Jitter (2)**
- `sjit`, `djit`

**Category 6: TCP Metrics (6)**
- `swin`, `dwin`, `stcpb`, `dtcpb`, `tcprtt`, `synack`

**Category 7: TCP Response (2)**
- `ackdat`, `response_body_len`

**Category 8: Payload Analysis (3)**
- `smean`, `dmean`, `trans_depth`

**Category 9: Contextual Features (10)**
- `ct_srv_src`, `ct_state_ttl`, `ct_dst_ltm`, `ct_src_dport_ltm`, `ct_dst_sport_ltm`, `ct_dst_src_ltm`, `ct_src_ltm`, `ct_srv_dst`, `ct_ftp_cmd`, `ct_flw_http_mthd`

**Category 10: Flags (2)**
- `is_ftp_login`, `is_sm_ips_ports`

### Feature Preprocessing

#### 1. Handling Missing Values
- Current: Dataset is 100% complete
- Fallback: Mean imputation for numeric, mode for categorical

#### 2. Categorical Encoding
```python
# Drop non-predictive features
DROP: ['id']  # Sequential, provides no info

# One-hot encode low-cardinality
ONE_HOT: proto (5 values), state (8 values)

# Target encoding for high-cardinality
TARGET_ENCODE: service (131 values)
# Use mean attack rate per service as encoding
```

#### 3. Feature Scaling
```python
# Standardization: (x - mean) / std
# Applied to all 40+ numeric features
# Ensures equal feature influence

# Features with extreme ranges (rates, loads):
# Consider log transformation: log(x + 1)
# Reduces outlier influence
```

#### 4. Outlier Handling
```python
# IQR method for detection (not removal)
# Q1 = 25th percentile, Q3 = 75th percentile
# IQR = Q3 - Q1
# Outliers: x < Q1-1.5*IQR or x > Q3+1.5*IQR

# Approach: cap outliers at boundaries rather than remove
# Preserves information while limiting influence
```

#### 5. Multicollinearity Management
```python
# Detected: 17 feature pairs with |correlation| > 0.9
# Examples:
#   - spkts vs dpkts (0.92)
#   - sload vs smean (0.88)
#   - ct_dst_ltm vs ct_src_ltm (0.91)

# Strategies:
# 1. Keep both in baseline (understand relationship)
# 2. Remove lower-importance one in ensemble
# 3. Use PCA if correlation persists post-tuning
```

### Feature Selection Strategy

**Phase 1 (Baseline)**:
- Use all 40 numeric features + encoded categorical
- Let model learn importance

**Phase 2 (Ensemble)**:
- Drop features with < 0.01 importance score
- Remove top correlated pairs (keep higher-importance feature)
- Typical reduction: 40 → 25-30 features

**Phase 3 (Optimization)**:
- SHAP analysis for local feature importance
- Investigate interaction features
- Keep only essential features for production (< 20)

---

## 4. Model Evaluation Framework

### Train/Validation/Test Split

```
Raw Data (82,332 flows)
    ↓
[Stratified Split: 80% train, 20% test]
    ├─ Training: 65,866 flows
    └─ Test: 16,466 flows
    ↓
[Training Data: 80% train, 20% validation]
    ├─ Train: 52,693 flows
    └─ Validation: 13,173 flows
```

**Why stratified?** Maintain 55%-45% class balance in all splits

### Evaluation Metrics

#### Binary Classification Metrics

| Metric | Formula | Target | Why |
|--------|---------|--------|-----|
| **False Positive Rate (FPR)** | FP / (FP + TN) | < 2% | Minimize false alarms |
| **False Negative Rate (FNR)** | FN / (FN + TP) | < 15% | Catch most attacks |
| **Precision** | TP / (TP + FP) | > 90% | Alert confidence |
| **Recall (Sensitivity)** | TP / (TP + FN) | > 85% | Attack catch rate |
| **Specificity** | TN / (TN + FP) | > 98% | Normal traffic acceptance |
| **F1-Score** | 2×(Precision×Recall)/(Precision+Recall) | > 0.87 | Balanced metric |
| **ROC-AUC** | Integral of ROC curve | > 0.95 | Ranking quality |

#### Multi-Class Metrics (Attack Type Classification)

- Macro F1-Score (average across 10 attack types)
- Per-class F1-Score (understanding weak classes)
- Confusion matrix (which attacks are confused with each other?)

#### Operational Metrics

- **Inference latency** (P50, P95, P99)
- **Throughput** (flows/second)
- **Memory footprint** (MB)
- **Model size** (when serialized)

---

## 5. Production Pipeline Architecture

### High-Level System

```
Network Traffic
    ↓
[Flow Extraction (NetFlow)]
    ↓
[Feature Engineering]
    ├─ Scale numeric
    ├─ Encode categorical
    └─ Compute contextual features
    ↓
[Model Inference]
    ├─ Prediction: Attack (1) or Normal (0)
    ├─ Probability: 0.0-1.0
    └─ Attack type: DoS/Exploit/Backdoor/etc
    ↓
[Alert Management]
    ├─ If confidence > threshold:
    │  └─ Generate alert + metadata
    └─ Log to SIEM
    ↓
[Response Actions]
    ├─ Block connection (optional)
    ├─ Ticket creation (SOC)
    └─ Incident playbook trigger
```

### Integration Points

**Option 1: REST API**
```
External System → POST /predict → Model Inference → JSON Response
```

**Option 2: Direct Python Import**
```python
from ids_model import predict_flow
result = predict_flow(flow_dict)  # Returns label, confidence, attack_type
```

**Option 3: Batch Processing**
```
Logs (PCAP/NetFlow) → Feature extraction → Batch inference → Results CSV
```

**Option 4: Real-time Streaming**
```
Kafka Topic → Feature extraction → Model stream → Alert topic → Splunk/SIEM
```

---

## 6. Explainability & Interpretability

### Why Explainability Matters

- Alert operators need to understand "why" the model flagged a flow
- Regulatory compliance (interpretable decisions)
- Model debugging & improvement
- User trust

### Explainability Techniques

#### Phase 1 & 2: Feature Importance
```python
# Logistic Regression
coefficients → Feature importance (linear)

# Decision Tree
Gini/Entropy reduction → Feature importance

# Random Forest
Mean decrease in impurity

# XGBoost
SHAP values (Shapley Additive exPlanations)
```

#### Phase 3: Per-Prediction Explanation
```
Flow: {dur: 0.5, spkts: 10, dload: 500, ct_dst_ltm: 50}
    ↓
[Model predicts: Attack (confidence 0.92)]
    ↓
[Explanation]:
"Attack likely due to:
  - High destination load (dload=500 > baseline 50)
  - High destination connection count (ct_dst_ltm=50 > normal 5)
  - Unusual flow duration (dur=0.5 < typical 2.0)
  Attribution: dload +0.35, ct_dst_ltm +0.30, dur +0.15"
```

---

## 7. Expected Performance

### Baseline Models (Phase 1)

| Model | Best FPR | Precision | Recall | F1-Score | Time |
|-------|----------|-----------|--------|----------|------|
| Logistic Regression | 1.8% | 87% | 82% | 0.84 | Weeks 1-2 |
| Decision Tree | 2.2% | 85% | 79% | 0.82 | Weeks 1-2 |

### Ensemble Models (Phase 2)

| Model | FPR | Precision | Recall | F1-Score | Time |
|-------|-----|-----------|--------|----------|------|
| Random Forest | 1.9% | 91% | 84% | 0.87 | Weeks 3-4 |
| XGBoost | 1.7% | 93% | 87% | 0.90 | Weeks 5-6 |
| Voting Ensemble | 1.8% | 92% | 88% | 0.90 | Weeks 7-8 |

### Optimized Production Model (Phase 3)

| Metric | Target | Expected |
|--------|--------|----------|
| FPR | < 2% | 1.8% ✓ |
| Precision | > 90% | 92.5% ✓ |
| Recall | > 85% | 88% ✓ |
| F1-Score | > 0.87 | 0.90 ✓ |
| Latency (P95) | < 50ms | 25ms ✓ |
| Throughput | 8,500+/sec | 12,000/sec ✓ |

---

## 8. Risk Mitigations

### Risk 1: Model Overfitting

**Mitigation**:
- Stratified K-fold cross-validation (5 folds)
- Regularization (L1/L2 for LR, max_depth for trees)
- Test set held-out (never seen by model during training)
- Cross-dataset validation (test on CICIDS2017, CICIDS2018)

### Risk 2: Domain Shift (Real Network ≠ Dataset)

**Mitigation**:
- Analyze dataset collection period (2015 - modern era)
- Test against external datasets (different network, different attacks)
- Monitor model performance post-deployment
- Retrain quarterly with production data

### Risk 3: Adversarial Attacks

**Mitigation**:
- Attackers modify traffic to evade model
- Solution: Ensemble models (harder to fool multiple models)
- Regular model retraining with evasion examples
- Anomaly detection module for unknown patterns

### Risk 4: Feature Engineering Errors

**Mitigation**:
- Unit tests for feature extraction
- Data validation checks (range, type, null)
- Compare features vs NetFlow standards
- Code review before deployment

### Risk 5: Poor Threshold Selection

**Mitigation**:
- Extensive threshold sweeping (0.1-0.9)
- A/B testing in production (2 models with different thresholds)
- Monitor FPR/Recall continuously
- Easy threshold adjustment without retraining

---

## 9. Success Criteria Checkpoints

### Week 2-4 (Phase 1 Complete)
- ✓ Baseline model FPR < 2%
- ✓ Precision > 85%
- ✓ Feature importance documented
- ✓ Decision: Proceed to Phase 2? (Go/No-Go)

### Week 8-10 (Phase 2 Complete)
- ✓ Ensemble FPR ≤ 2%
- ✓ Precision > 90%
- ✓ Recall > 85%
- ✓ Cross-validation results consistent
- ✓ Decision: Proceed to Phase 3? (Go/No-Go)

### Week 12-14 (Phase 3 Complete)
- ✓ Production model FPR 1.5-2%
- ✓ Precision > 92%
- ✓ Recall > 88%
- ✓ Latency < 50ms (P95)
- ✓ Ready for deployment

---

## 10. Next Steps

**Immediate (This Week)**:
1. Finalize feature engineering pipeline
2. Set up train/validation/test split
3. Prepare training infrastructure

**Short-term (Weeks 1-4)**:
1. Train baseline models (Logistic Regression, Decision Tree)
2. Perform threshold tuning
3. Generate feature importance analysis
4. Document findings

**Medium-term (Weeks 5-10)**:
1. Train ensemble models (Random Forest, XGBoost)
2. Hyperparameter optimization
3. Cross-dataset validation
4. Model comparison report

**Long-term (Weeks 11-14)**:
1. Final optimization & threshold selection
2. Production model serialization
3. Performance documentation
4. Deployment readiness review

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Technical Lead**: ML Engineering Team  
**Status**: Ready for implementation
