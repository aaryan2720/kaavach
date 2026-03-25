# Models Directory

## Purpose
This directory stores trained machine learning models and associated artifacts for the UNSW-NB15 network intrusion detection system.

## Contents

### Phase 1: Baseline Models
- `baseline_logistic_regression.pkl` - Logistic Regression baseline model
- `baseline_decision_tree.pkl` - Decision Tree baseline model
- Baseline model performance reports and validation metrics

### Phase 2: Ensemble Models
- `ensemble_random_forest.pkl` - Random Forest ensemble model
- `ensemble_xgboost.pkl` - XGBoost gradient boosting model
- Hyperparameter tuning results and cross-validation reports

### Model Metadata
- `model_metadata.json` - Training date, feature count, performance metrics
- `feature_scaler.pkl` - Standard scaler for feature normalization
- `label_encoder.pkl` - Encoder for categorical variables (if applicable)

### Supporting Files
- `feature_importance.json` - SHAP and model-based feature importance rankings
- `confusion_matrix.png` - Visualization of model predictions
- `roc_curve.png` - ROC/AUC curves for performance evaluation

## Workflow
1. Train models using scripts in `../training/`
2. Evaluate models and select best performer
3. Save trained model and scalers to this directory
4. Use saved models for inference in API server (`../api/`)

## Model Naming Convention
- Format: `{phase}_{model_type}_{timestamp}.pkl`
- Example: `phase1_logistic_regression_20260325.pkl`

## Next Steps
- [ ] Train baseline models (Phase 1)
- [ ] Tune hyperparameters (Phase 2)
- [ ] Evaluate on cross-dataset validation
- [ ] Select production model
- [ ] Archive old models
