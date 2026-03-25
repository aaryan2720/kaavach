# Training Directory

## Purpose
This directory contains scripts for training, evaluating, and optimizing the machine learning models for the UNSW-NB15 network intrusion detection system.

## Directory Structure
```
training/
├── plots/                          # Training visualizations
├── train_baseline.py              # Phase 1: Baseline model training
├── train_ensemble.py              # Phase 2: Ensemble model training
├── train_hyperparameter_tuning.py # Phase 2: Bayesian optimization
├── evaluate_models.py             # Model evaluation and cross-validation
├── feature_selection.py           # Feature engineering and reduction
└── cross_dataset_validation.py    # Phase 2: Validation on multiple datasets
```

## Script Purpose

### Phase 1: Baseline Training
- **train_baseline.py** - Train Logistic Regression and Decision Tree
  - Input: UNSW_NB15.csv
  - Output: Baseline models, performance metrics
  - Target: FPR < 2%, Precision > 85%

### Phase 2: Optimization
- **train_ensemble.py** - Train Random Forest and XGBoost
  - Input: Features selected from baseline phase
  - Output: Ensemble models, hyperparameter configs
- **train_hyperparameter_tuning.py** - Bayesian optimization
  - Optimize for FPR and Precision trade-off
  - Cross-validation with stratified k-fold
- **feature_selection.py** - Handle multicollinearity and reduce features
  - Address 17 high-correlation pairs
  - Reduce from 40 → 25-30 features
- **cross_dataset_validation.py** - Validate on external datasets
  - Test generalization beyond UNSW-NB15
  - Generate cross-dataset performance report

### Monitoring & Evaluation
- **evaluate_models.py** - Comprehensive model evaluation
  - Confusion matrix, ROC, precision-recall curves
  - Generate evaluation reports
  - Save plots to `plots/` directory

## Key Features

### Data Processing
- Load UNSW_NB15.csv (82,332 rows)
- Handle 10 attack types (multi-class + binary)
- Scale features using StandardScaler
- Address class imbalance (55% attack, 45% normal)

### Model Evaluation Metrics
- Accuracy, Precision, Recall, F1-Score
- False Positive Rate (FPR) < 2% (PRIMARY OBJECTIVE)
- ROC-AUC, PR-AUC curves
- Confusion matrix and classification reports

### Cross-Validation
- Stratified K-Fold (5 folds)
- Maintain class distribution in train/test
- Threshold optimization for FPR target

## Workflow
```
1. Run train_baseline.py → Phase 1 models + plots
                ↓
2. Run feature_selection.py → Feature importance + reduced set
                ↓
3. Run train_ensemble.py → Phase 2 models
                ↓
4. Run train_hyperparameter_tuning.py → Optimized models
                ↓
5. Run cross_dataset_validation.py → External validation
                ↓
6. All models saved to ../models/
7. All visualizations saved to plots/
```

## Phase Deliverables

### Phase 1 (Baseline)
- Logistic Regression + Decision Tree models
- Baseline FPR/Precision/Recall metrics
- Feature analysis report
- Decision checkpoint file

### Phase 2 (Optimization)
- Random Forest + XGBoost models
- Hyperparameter tuning report
- Feature importance rankings (top 25-30 features)
- Cross-dataset validation results
- Updated performance targets (FPR, Precision, Recall)

### Phase 3 (Production Readiness)
- Multi-class attack classification (11-way)
- Production model serialization
- Model drift detection baselines
- API integration tests

## Dependencies
- pandas, numpy, scikit-learn
- XGBoost, LightGBM
- Matplotlib, seaborn (for visualization)
- Optuna (for Bayesian optimization)

## Next Steps
- [ ] Create train_baseline.py
- [ ] Create feature_selection.py
- [ ] Create train_ensemble.py
- [ ] Create train_hyperparameter_tuning.py
- [ ] Create cross_dataset_validation.py
- [ ] Create evaluate_models.py
- [ ] Run Phase 1 training
- [ ] Run Phase 2 optimization
