# Future Scope & Roadmap: Phases 2-5 & Vision

## Overview

This document outlines the long-term vision for the UNSW-NB15 ML intrusion detection system, including advanced capabilities, scaling strategies, and integration with broader security operations.

---

## Phase 2: Hyperparameter Optimization & Validation (Months 3-4)

### Objectives
- Deep hyperparameter tuning using Bayesian optimization
- Cross-dataset validation on CICIDS2017 & CICIDS2018
- Feature interaction analysis
- Model interpretability (SHAP deployment)

### Deliverables

#### 2.1 Advanced Hyperparameter Search
```python
# Bayesian Optimization (more efficient than grid search)
from skopt import gp_minimize
from skopt.space import Real, Integer

# Define search space
space = [
    Integer(3, 20, name='max_depth'),
    Real(0.001, 0.5, name='learning_rate'),
    Real(0.5, 1.0, name='subsample'),
    Real(0.5, 1.0, name='colsample_bytree'),
    Integer(50, 500, name='n_estimators'),
]

# Optimization
@use_named_args(space)
def objective(**params):
    model = xgb.XGBClassifier(**params)
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
    return -cv_scores.mean()

result = gp_minimize(objective, space, n_calls=50, random_state=42)
print(f"Best parameters: {result.x}")
```

**Expected Improvements**:
- FPR improvement: 2.0% → 1.5%
- Precision improvement: 92% → 94%
- Recall improvement: 88% → 90%

#### 2.2 Cross-Dataset Validation
```
UNSW-NB15 (training)
├─ 82,332 training flows (55% attack)
├─ 175,000 test flows
└─ FPR: 1.8%, Precision: 92%, Recall: 88%
    ↓
[Feature Alignment]
    • Map UNSW features to CICIDS2017 (44 → 78 features, find overlap)
    • Select common 35-40 features
    • Rename for consistency
    ↓
CICIDS2017 (external validation)
├─ 225,745 flows (test set)
├─ Different attack types (11 types)
├─ Different network environment
└─ Expected: FPR 2.5-3.5%, Precision 89%, Recall 82%
    
[Domain Shift Analysis]
├─ Identify features causing domain shift
├─ Possible: tcp/udp ratio, protocol mix, service distribution
└─ Mitigation: Optional domain adaptation training
```

**Strategy**:
1. Train UNSW → Test UNSW (baseline)
2. Train UNSW → Test CICIDS2017 (measure domain shift)
3. Train UNSW+CICIDS2017 → Test both (joint optimization)
4. Optional: Domain adversarial training (advanced)

#### 2.3 Feature Interaction Analysis
```
Identify interactions through:
├─ SHAP dependence plots (feature interaction visualizations)
├─ PDP (Partial Dependence Plot) + ICE (Individual Conditional Expectation)
├─ Feature engineering: polynomial terms (top 5 features)
└─ Example interactions:
    • ct_dst_ltm × dload (many dests + high load = DDoS pattern)
    • rate × ct_src_ltm (high rate from many sources = flood)
    • tcprtt × synack (latency patterns = tunneling)

[New Engineered Features]
├─ ct_dst_ltm_dload = ct_dst_ltm × dload
├─ rate_ct_src_ltm = rate × ct_src_ltm
├─ tcprtt_synack = tcprtt × synack
└─ Retrain model with interaction terms
    • Expected: +0.5-1% F1 improvement
```

#### 2.4 Model Interpretability Maturity
```
Deploy SHAP at production level:
├─ Pre-compute SHAP values for reference set (1000 samples)
├─ Use kernel method for fast approximation at inference time
├─ Generate per-flow explanations
└─ Integration with alert system:
    
Alert Example:
  Flow: TCP/HTTP, 45.6.7.8 → 192.168.1.5:80
  Label: ATTACK (confidence 0.94)
  
  Top Contributing Factors:
  1. Destination Connection Count (ct_dst_ltm): 87 → +0.32 prob
  2. Destination Load (dload): 45 Mbps → +0.25 prob
  3. Packet Rate (rate): 850 pps → +0.18 prob
  
  Context: Classic DDoS amplification pattern
           Recommend: Block source IP immediately
```

### Timeline
- Weeks 1-2: Bayesian hyperparameter optimization
- Weeks 3-4: CICIDS2017 validation
- Weeks 5-6: Feature interactions + SHAP deployment
- Week 7: Optimization report & decision for Phase 3

### Success Criteria
- ✅ Cross-dataset FPR < 3% (CICIDS2017)
- ✅ Feature interactions documented
- ✅ SHAP explanations generated for 100% of predictions
- ✅ Domain shift analysis completed

---

## Phase 3: Multi-Class Attack Categorization (Months 5-6)

### Objectives
Build **11-way classifier** to identify specific attack types

### Current State (Phase 1)
```
Binary: Attack vs Normal (binary classification)
├─ Outputs: 0 (Normal) or 1 (Attack)
└─ Accuracy sufficient for alert generation
```

### Target State (Phase 3)
```
Multi-class: Attack Type Identification (11-way classification)
├─ 0: Normal
├─ 1: DoS/DDoS
├─ 2: Exploits
├─ 3: Fuzzers
├─ 4: Backdoor
├─ 5: Worms
├─ 6: Reconnaissance
├─ 7: Shellcode
├─ 8: Generic
├─ 9: Analysis
├─ 10: Other
└─ Automatically routes to appropriate response playbook
```

### Implementation Strategy

#### Approach 1: One-vs-Rest (Simple)
```python
from sklearn.multiclass import OneVsRestClassifier

# Train 11 binary classifiers (each attack type vs rest)
multi_model = OneVsRestClassifier(
    xgb.XGBClassifier(max_depth=5, learning_rate=0.1)
)

multi_model.fit(X_train, y_train_multiclass)

# Predict
y_pred_multiclass = multi_model.predict(X_test)  # 0-10
y_pred_proba = multi_model.predict_proba(X_test)  # shape: (n, 11)

# Results
print(f"Predicted attack type: {attack_names[y_pred_multiclass[0]]}")
print(f"Confidence: {y_pred_proba[0].max():.2%}")
```

**Performance Expected**:
- Macro F1: 0.82 (average across 11 classes)
- Rare classes (Analysis 0.5%, Shellcode 3%): Lower recall
- Common classes (Generic 23%): F1 ~0.90

#### Approach 2: Hierarchical Classification (Advanced)
```
Level 1: Attack vs Normal (binary)
    ↓
Level 2: Attack Category (connection vs content vs resource)
    ├─ Connection: DoS, Reconnaissance, Backdoor
    ├─ Content: Exploits, Shellcode, Worms
    └─ Resource: Fuzzers, Generic, Analysis
    ↓
Level 3: Specific Type (single classifier per category)
    ├─ Connection classifier: tells DoS vs Backdoor vs Recon
    └─ Content classifier: tells Exploit vs Shellcode vs Worm
```

**Advantage**: Better performance on rare classes (Shellcode, Analysis)

### Attack-Type Specific Features

```
DoS Detection:
├─ High rate (rate > 500 pps)
├─ High load (sload/dload > 50 Mbps)
├─ Low response_body_len (small replies)
└─ Model: RF achieves 95% precision, 87% recall

Reconnaissance:
├─ Low packet counts (spkts < 5, dpkts < 5)
├─ High destination count (ct_dst_ltm > 50)
├─ Many services probed (ct_srv_dst >> 1)
└─ Model: Easy to identify (98% precision)

Backdoor:
├─ Persistent connections (dur >> 1000 seconds)
├─ Bidirectional (spkts ≈ dpkts)
├─ Unusual ports (service not HTTP/SSH/DNS)
└─ Model: 94% precision, 85% recall

Shellcode/Exploits:
├─ Complex patterns (tcprtt, transdepth important)
├─ Payload anomalies (smean varies + large response_body_len)
├─ Harder to detect (89% precision, 76% recall)
```

### Confusion Matrix (Target)

```
Predicted Attack Type:
                     DoS   Expl  Fuzz  Back  Worm  Recon Shell Gener Anal  Norm
Actual   DoS      [ 1183    78    32    10     8    15     0   148    1   -  ]  (94%)
         Expl     [   45  1318    89    45    34    23    87   275    -   -  ]  (87%)
         Fuzz     [   34    78  1122    12     8    23     0   186    -   -  ]  (86%)
         Back     [    8    29    10   402    15   126    23    12    -   -  ]  (82%)
         Worm     [    9    34     8    16   187    19     0    15    -   -  ]  (77%)
         Recon    [    2    12     3    45     8   681    19     2    -   -  ]  (94%)
         Shell    [    1    64     0    18     1     8   289    10    -   -  ]  (75%)
         Gener    [   98   187   145    28    29    18     5  1743    -   -  ]  (74%)
         Anal     [    0     0     0     0     0     5     0     5    48   -  ]  (73%)
         Norm     [  ****normal class—no misclassification expected****      ] (>99%)

Macro F1: 0.82 (weighted average)
```

### Deployment
```
Alert Example:
  Original: "ATTACK detected"
  Enhanced: "DoS attack detected (confidence 0.94)
            - Source: 45.6.7.8 (botnet)
            - Attack rate: 2,500 pps
            - DDoS amplification pattern identified
            - Recommended action: Block source IP (BGP null-route)"
```

### Timeline
- Weeks 1-2: Multi-class model training (approach comparison)
- Weeks 3-4: Per-class optimization + feature selection
- Weeks 5-6: Integration with response playbooks
- Weeks 7-8: Alert enrichment + analyst testing
- Week 9: Go/No-Go for production

---

## Phase 4: Real-Time Streaming Deployment (Months 7-8)

### Objectives
Deploy to production with 8,500+ flows/sec throughput

### Architecture

#### Kafka-Based Real-Time Pipeline
```
Network TAP (monitoring hardware)
    ├─ 8,500 flows/second
    └─ NetFlow v5 export
         ↓
[Kafka Cluster: 3 brokers]
    ├─ Topic: network-flows (4 partitions)
    ├─ Replication factor: 3
    ├─ Retention: 24 hours
    └─ Throughput: 12,000 msgs/sec (spare capacity)
         ↓
[Stream Processing Application]
    ├─ Consumer group: ids-processor
    ├─ 4 parallel workers (one per Kafka partition)
    ├─ Technology: Kafka Streams or Spark Streaming
    ├─ Stateful processing (contextual features)
    └─ Latency: 10-25ms from NetFlow to alert
         ↓
[Output Topics]
    ├─ alerts (attacks, high confidence)
    ├─ normal-flows (for baseline learning)
    ├─ metrics (model performance, latency)
    └─ audit log (all predictions for compliance)
         ↓
[SIEM Integration]
    ├─ Splunk Kafka Connect
    ├─ ELK Stack Consumer
    ├─ Alert routing to SOC
    └─ Incident playbook automation
```

#### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ids-stream-processor
  namespace: security
spec:
  replicas: 4  # 4 processing pods
  selector:
    matchLabels:
      app: ids-processor
  template:
    metadata:
      labels:
        app: ids-processor
    spec:
      containers:
      - name: processor
        image: ids-processor:2.0
        resources:
          requests:
            cpu: 2
            memory: 4Gi
          limits:
            cpu: 4
            memory: 8Gi
      autoscaling:
        minReplicas: 4
        maxReplicas: 16
        targetCPUUtilizationPercentage: 70
```

### Monitoring & Observability

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

predictions_total = Counter(
    'ids_predictions_total',
    'Total predictions',
    ['label', 'attack_type']
)

prediction_latency = Histogram(
    'ids_prediction_latency_ms',
    'Prediction latency in ms',
    buckets=[5, 10, 25, 50, 100, 250, 500, 1000]
)

false_positive_rate = Gauge(
    'ids_false_positive_rate',
    'Current FPR (sliding 1000 flows)'
)

# Example usage
with prediction_latency.time():
    y_pred = model.predict(X)

predictions_total.labels(
    label='Attack' if y_pred else 'Normal',
    attack_type=attack_type
).inc()
```

### Disaster Recovery
```
Primary Region: us-east-1
├─ Model serving: 4 pods
├─ Kafka: 3 brokers
└─ Database: Aurora RDS (3 AZs)

Standby Region: us-west-2
├─ Model serving: 2 pods (warm standby)
├─ Kafka: Cross-region replication
└─ Database: Read replica + replication lag < 1s

Failover RTO: < 5 minutes
Failover RPO: < 30 seconds (Kafka replication)
```

---

## Phase 5: Malware Detection Integration (Months 9-12)

### Objectives
Add malware detection module to complement network IDS

### Vision

```
Current (Phase 1-4): Network Intrusion Detection
├─ Input: Flow records (44 attributes)
├─ Output: Attack classification + confidence
├─ Coverage: 85% of threats (exploits, DoS, backdoor C2, reconnaissance)
└─ Limitation: Cannot detect unknown malware payloads

Extended (Phase 5): Unified Threat Detection
├─ Component 1: Network IDS (existing)
├─ Component 2: Endpoint malware detection (NEW)
├─ Component 3: File integrity monitoring (NEW)
└─ Integration: Correlated alerts (network IDS + malware = confirmed threat)
```

### Malware Detection Module

#### Option 1: Behavioral Analysis
```
On-Endpoint Analysis:
├─ Monitor file executions
├─ Track process memory allocations
├─ Detect code injection (WriteProcessMemory, VirtualAllocEx)
├─ Flag: Unsigned binaries, unexpected services
├─ Signal communication: C2 detection via DNS/IP reputation
```

#### Option 2: Signature-Based + ML
```
Hybrid Approach:
├─ Yara signatures (fast, known malware)
├─ ML malware classifier (unknown samples):
│  ├─ Input: PE headers, import functions, strings from binary
│  ├─ Model: Random Forest (fast, interpretable)
│  └─ Accuracy: 92% on EMBER dataset
└─ Escalation: High-confidence unknown malware → sandbox
```

#### Option 3: Sandbox Integration
```
Detonation Pipeline:
├─ File submission (suspicious from email/download)
├─ Cuckoo/ANY.RUN sandbox execution
├─ Behavioral monitoring (network, registry, files)
├─ ML analysis of detonation results
└─ Verdict: Malicious/Clean/Suspicious
    └─ Correlate with network IDS (suspicious IPs/domains)
```

### Correlation Engine

```
Alert Fusion:
    Network IDS Alert          Malware Alert
    "DoS from 45.6.7.8"        "Emotet trojan detected
                                on endpoint 192.168.1.50
                                Connects to 45.6.7.8"
            ↓                            ↓
    ┌───────────────────────────────────┐
    │ Correlation Engine                │
    │ - Match source/dest IPs           │
    │ - Check timing (within 5 min)     │
    │ - Assess confidence               │
    └───────────────────────────────────┘
            ↓
    Confidence: CRITICAL
    Alert Type: COORDINATED_ATTACK
    Context: DoS from infected botnet
    Action: Block source, quarantine endpoint, escalate to CISO
```

### Deployment Timeline
```
Week 1-4: Design malware detection architecture
Week 5-8: Implement ML malware classifier
Week 9-10: Integrate with network IDS
Week 11-12: Pilot with security team
```

---

## Long-Term Vision (Years 2+)

### 6. Threat Intelligence Integration
```
├─ Subscribe to abuse.io, AbuseIPDB, Shodan
├─ Correlate detected IPs/domains with reputation feeds
├─ Automatic threat scores
├─ Inform model retraining (adversarial robustness)
└─ Example:
    Alert: "Attack from 45.6.7.8"
    + TI lookup: "Known botnet C2, seen in DarkWeb market"
    → Escalation to incident response
```

### 7. Continuous Learning
```
Post-deployment feedback loop:
├─ Collect analyst labels (was alert correct?)
├─ Monthly retraining with new data (prod + verified labels)
├─ A/B testing: Model v2.0 vs v1.5 on 10% traffic
├─ Gradual rollout when v2.0 outperforms
└─ Target: Monotonic improvement of FPR, recall
```

### 8. Threat Hunting Assistant
```
├─ Interactive queries: "Show me all flows similar to attack X"
├─ Anomaly timeline: Visualize deviations from baseline
├─ Pivot analysis: "All flows from this user today"
├─ Reporting: Automated threat assessment reports
└─ Integration: Splunk app, Jupyter notebook templates
```

### 9. Federated Learning (Multi-Org)
```
For multi-site enterprises:
├─ Train local models (privacy-preserving)
├─ Aggregate model updates (not raw data)
├─ Shared threat intelligence
└─ Use case: Detect threats across branches
       Model branch-east + branch-west = better global accuracy
```

### 10. Hardware Acceleration
```
Latency optimization:
├─ FPGA pipeline (< 1ms inference)
├─ ASIC for model. deployment (high-volume, edge devices)
├─ GPU acceleration for hyperparameter search (weeks → days)
└─ Target: 50,000+ flows/sec per machine
```

---

## Capabilty Roadmap Summary

```
Timeline                Phase           Key Deliverables
─────────────────────────────────────────────────────────────
Now           Phase 1: Foundation       ✅ Dataset, EDA, baselines
              (Month 1-2)               ✅ FPR < 2%

Month 3-4     Phase 2: Optimization    → Cross-dataset validation
                                       → SHAP explanations
                                       → Improved metrics

Month 5-6     Phase 3: Multi-class     → 11-way attack classification
                                       → Attack-specific playbooks
                                       → Enhanced alerts

Month 7-8     Phase 4: Real-time       → Kafka streaming pipeline
              Deployment               → 8,500+ flows/sec
                                       → Production SIEM integration

Month 9-12    Phase 5: Malware         → Endpoint detection
              Integration              → Correlated threat detection
                                       → Unified security platform

Year 2        Advanced Features        → Threat intelligence fusion
                                       → Continuous learning
                                       → Federated learning
```

---

## Resource Requirements by Phase

| Phase | Timeline | Team | Infrastructure | Budget |
|-------|----------|------|---|---|
| 1 | 2 months | 2 ML eng | 1 GPU, 8GB RAM | $5K |
| 2 | 2 months | 2 ML eng | 4 GPU, 16GB RAM | $15K |
| 3 | 2 months | 3 ML eng | 8 GPU, 32GB RAM | $25K |
| 4 | 2 months | 5 (ML + DevOps) | Kubernetes, Kafka | $50K |
| 5 | 4 months | 4 ML + security | Sandbox, TI feeds | $40K |
| **Total** | **12 months** | **16 person-months** | **Multi-tier cloud** | **$135K** |

---

## Key Success Metrics (12-Month Horizon)

| Metric | Phase 1 | Phase 5 | Improvement |
|--------|---------|---------|---|
| False Positive Rate | 2.0% | 0.8% | -60% |
| Precision (Attack) | 92% | 96% | +4% |
| Recall (Attack) | 88% | 94% | +6% |
| Attack Classification | Binary | 11-way | New capability |
| Throughput | 1,000/sec | 50,000/sec | 50x |
| Latency | 100ms | 5ms | 20x faster |
| Coverage | Network only | Network + Endpoint | Expanded |
| Analyst Efficiency | 10 alerts/hr | 100 alerts/hr | 10x |

---

## Risk Mitigation

| Risk | Phase | Mitigation |
|------|-------|-----------|
| Model drift (attacks evolve) | 2+ | Continuous retraining, threat intel feedback |
| False positives burnout | 3+ | Confidence calibration, analyst feedback loop |
| Malware polymorphism | 5 | Behavioral analysis + sandbox detonation |
| Performance degradation at scale | 4 | Load testing, horizontal scaling, caching |
| Security vulnerabilities | All | Regular pentesting, code review, supply chain security |

---

**Roadmap Version**: 1.0  
**Last Updated**: 2024  
**Target Customers**: Enterprise security ops, MSPs, government agencies  
**Expected Maturity**: Production-ready Phase 1 + Phase 2/3 by year-end  
**Status**: Approved for execution after Phase 1 go-live
