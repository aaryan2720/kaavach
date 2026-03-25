# Training Plots Directory

## Purpose
This directory stores visualization outputs from the model training and evaluation process. All plots generated during training runs are automatically saved here for analysis and documentation.

## Plot Categories

### Phase 1: Baseline Model Training Plots

#### Model Performance
- `01_baseline_confusion_matrix.png` - Logistic Regression vs Decision Tree confusion matrices
- `02_baseline_roc_curves.png` - ROC/AUC curves for both models
- `03_baseline_precision_recall.png` - Precision-Recall curves
- `04_baseline_threshold_analysis.png` - FPR vs TPR at different thresholds

#### Feature Analysis
- `05_baseline_feature_importance_dt.png` - Decision Tree feature importance
- `06_correlation_heatmap_baseline.png` - Feature correlation matrix

### Phase 2: Ensemble Model Training Plots

#### Ensemble Performance
- `07_ensemble_confusion_matrix.png` - Random Forest vs XGBoost confusion matrices
- `08_ensemble_roc_curves.png` - ROC curves comparing all Phase 2 models
- `09_ensemble_precision_recall.png` - Precision-Recall comparison
- `10_ensemble_threshold_optimization.png` - Optimal threshold selection (FPR < 2%)

#### Hyperparameter Tuning
- `11_hyperparameter_tuning_history.png` - Bayesian optimization convergence
- `12_grid_search_heatmap.png` - Hyperparameter combinations and performance
- `13_xgboost_learning_curve.png` - Training vs validation performance over iterations

#### Feature Analysis
- `14_feature_importance_rf.png` - Random Forest feature importance (top 20)
- `15_feature_importance_xgboost.png` - XGBoost feature importance (SHAP values)
- `16_feature_reduction_impact.png` - Performance impact of feature selection

### Phase 2: Cross-Dataset Validation Plots
- `17_cross_dataset_performance.png` - Generalization across datasets
- `18_cross_dataset_confusion_matrices.png` - Per-dataset performance
- `19_model_robustness_analysis.png` - Consistency across distributions

### Cross-Validation Plots
- `20_cross_validation_fold_performance.png` - Per-fold performance metrics
- `21_cross_validation_fpr_distribution.png` - FPR variance across folds
- `22_cross_validation_stability.png` - Model stability assessment

### Phase 3: Multi-Class Attack Classification
- `23_multiclass_confusion_matrix.png` - 11-way attack type confusion matrix
- `24_multiclass_per_attack_performance.png` - Per-attack-type precision/recall
- `25_multiclass_roc_curves.png` - One-vs-rest ROC curves

## Naming Convention

Format: `{sequence}_{phase}_{plot_type}.png`

- **Sequence**: 01-99 (chronological order)
- **Phase**: baseline, ensemble, multiclass
- **Plot Type**: confusion_matrix, roc_curves, feature_importance, etc.

Example: `15_ensemble_feature_importance_xgboost.png`

## Plot Generation Timeline

| Phase | Stage | When Generated | Count |
|-------|-------|----------------|-------|
| 1 | Baseline Training | After train_baseline.py | 6 plots |
| 1 | Feature Analysis | During feature_selection.py | 4 plots |
| 2 | Ensemble Training | After train_ensemble.py | 8 plots |
| 2 | Hyperparameter Tuning | During optimization | 5 plots |
| 2 | Cross-Validation | During evaluate_models.py | 3 plots |
| 2 | Cross-Dataset Val. | During cross_dataset_validation.py | 3 plots |
| 3 | Multi-Class Classification | After multiclass training | 3 plots |
| **Total** | | | **~35 plots** |

## Viewing & Analysis

### Quick Review
```bash
# Open all plots in sequence
python -c "import glob; import subprocess; [subprocess.Popen(['start', p]) for p in sorted(glob.glob('*.png'))]"
```

### By Phase
1. **Phase 1 Results**: Review plots 01-09 (baseline + feature analysis)
2. **Phase 2 Results**: Review plots 10-22 (ensemble + tuning + validation)
3. **Phase 3 Results**: Review plots 23-25 (multi-class)

## Key Decision Points

### After Phase 1 (Plots 01-09)
- **Decision**: Is baseline FPR < 2%?
- **Action**: If YES → Proceed to Phase 2; If NO → Adjust features/model

### After Phase 2 (Plots 10-22)
- **Decision**: Does ensemble model meet all targets?
  - FPR < 2% ✓
  - Precision > 90% ✓
  - Recall > 85% ✓
  - Cross-dataset performance acceptable ✓
- **Action**: If YES → Proceed to Phase 3; If NO → Re-tune hyperparameters

### After Phase 3 (Plots 23-25)
- **Decision**: Is multi-class attack classification reliable?
- **Action**: If YES → Ready for deployment; If NO → Expand training data

## Archiving

- Move plots from completed phases to `archive/` subdirectory
- Keep most recent plots accessible in root
- Document major milestones with timestamps

## Next Steps
- [ ] Configure plot export settings (DPI, format)
- [ ] Set up matplotlib/seaborn styling
- [ ] Create plot templates for consistency
- [ ] Archive Phase 1 plots after Phase 2 completion
