# Quick Start Guide: Get Running in 10 Minutes

> **Fastest path from zero to running analysis**

---

## Prerequisites

- **OS**: Windows, macOS, or Linux
- **Python**: 3.9+ (3.11+ recommended)
- **Disk**: 2 GB free (dataset + analysis outputs)
- **Internet**: Required for dataset download (first time only)

---

## 5-Minute Setup

### Step 1: Clone/Download Project (1 min)
```bash
# If you have git
git clone <repository-url>
cd unsw-nb15-ids

# OR just navigate to existing folder
cd d:\Documents\ML\ model\

# Check you see these files
ls
# Expected: README.md, unsw_nb15_analysis.py, UNSW_NB15.csv (or not yet)
```

### Step 2: Create Python Environment (2 min)
```bash
# Windows CMD
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux bash
python3 -m venv .venv
source .venv/bin/activate

# Verify activation (should show (.venv) in prompt)
```

### Step 3: Install Dependencies (2 min)
```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install kagglehub pandas numpy seaborn scikit-learn matplotlib

# Verify installation
python -c "import pandas; print(f'✅ Installed pandas {pandas.__version__}')"
```

### Step 4: Download Dataset (Depends on speed)
```bash
# Set Kaggle API credentials first
# 1. Go to https://www.kaggle.com/settings/account
# 2. Click "Create New Token"
# 3. Save to ~/.kaggle/kaggle.json (or create manually)

# Then run download
python download_and_analyze.py

# Output should be:
# ✅ Dataset downloaded: UNSW_NB15.csv (82,332 rows × 45 cols)
# ✅ Metadata saved: dataset_info.json
```

---

## Quick Analysis (5 Minutes)

### Run Complete Analysis
```bash
python unsw_nb15_analysis.py

# Expected output:
# ======================================================================
# ANALYSIS COMPLETE!
# ======================================================================
# 
# Generated 12 visualization files in 'analysis_outputs':
#    1. 01_class_distribution.png
#    2. 02_numeric_distributions.png
#    ... (10 more)
#   12. 12_attack_patterns.png
# 
# 📊 analysis_report.json
# 
# Total: 12 graphs + 1 report
# ✓ Ready for model training!
```

### View Outputs
```bash
# Check generated files
ls analysis_outputs/

# Should show:
# ├─ 01_class_distribution.png
# ├─ 02_numeric_distributions.png
# ├─ 03_correlation_heatmap.png
# ├─ 04_attack_categories.png
# ├─ 05_categorical_distributions.png
# ├─ 06_features_by_class.png
# ├─ 07_boxplots_by_class.png
# ├─ 08_flow_characteristics.png
# ├─ 09_bytes_packets_analysis.png
# ├─ 10_tcp_metrics.png
# ├─ 11_contextual_features.png
# ├─ 12_attack_patterns.png
# └─ analysis_report.json

# View report data
cat analysis_report.json  # Linux/macOS
type analysis_report.json # Windows
```

---

## 10-Minute Full Workflow

```bash
# 1. Activate environment (30 sec)
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 2. Download dataset (depends on speed, 1-5 min)
python download_and_analyze.py

# 3. Run analysis (1-2 min)
python unsw_nb15_analysis.py

# 4. Check outputs (1 min)
ls analysis_outputs/

# Total: ~10 minutes on typical internet
```

---

## Common Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'kagglehub'"

**Solution**:
```bash
# Make sure virtual environment is activated
pip install kagglehub --upgrade

# Verify
python -c "import kagglehub; print(kagglehub.__version__)"
```

### Issue 2: "kaggle.exceptions.ApiHTTPError: Unexpected response"

**Solution**: Set up Kaggle API credentials
```bash
# 1. Go to https://www.kaggle.com/settings/account
# 2. Click "Create New Token" → downloads kaggle.json
# 3. Place in correct location:
#    Windows: C:\Users\<YourUsername>\.kaggle\kaggle.json
#    macOS/Linux: ~/.kaggle/kaggle.json

# 4. Set permissions (macOS/Linux)
chmod 600 ~/.kaggle/kaggle.json

# 5. Retry download
python download_and_analyze.py
```

### Issue 3: "Permission denied" on macOS
```bash
# Solution: Fix script permissions
chmod +x download_and_analyze.py
chmod +x unsw_nb15_analysis.py

# Retry
python unsw_nb15_analysis.py
```

### Issue 4: Out of Memory Error
```bash
# Problem: Low RAM (< 4GB)
# Solution: Load data in chunks

python unsw_nb15_analysis.py --chunk-size 10000

# Or read analysis_report.json for summary without loading all data
```

### Issue 5: Disk Space Full
```bash
# Check available space
df -h  # macOS/Linux
dir C:\  # Windows

# Solution 1: Delete old analysis_outputs (safe to delete)
rm -rf analysis_outputs/

# Solution 2: Store UNSW_NB15.csv elsewhere (symlink it)
# ln -s /path/to/large/disk/UNSW_NB15.csv ./UNSW_NB15.csv
```

---

## Next Steps: Learn the Data

### 1. Understand the Dataset (5 min)
→ Read [03_DATASET_ANALYSIS.md](03_DATASET_ANALYSIS.md)
- What are the 44 features?
- What attack types exist?
- What patterns distinguish attacks?

### 2. Understand the Solution (10 min)
→ Read [02_SOLUTION_OVERVIEW.md](02_SOLUTION_OVERVIEW.md)
- What's our ML strategy?
- Why prioritize false positives?
- What models will we build?

### 3. Understand the Problem (10 min)
→ Read [01_PROBLEM_STATEMENT.md](01_PROBLEM_STATEMENT.md)
- Why do we need this system?
- What's the business case?
- What are success criteria?

### 4. Plan Model Development (Read, don't do yet)
→ [04_MODEL_ARCHITECTURE.md](04_MODEL_ARCHITECTURE.md)
- How will we train models?
- What are phase 1, 2, 3?
- When can we deploy?

---

## Inspecting the Analysis

### View Individual Graphs

```python
# Python script to open graphs in viewer
import subprocess
import os
from pathlib import Path

graphs_dir = Path('analysis_outputs')
for graph in sorted(graphs_dir.glob('*.png')):
    print(f"Opening {graph.name}...")
    # Windows
    os.startfile(graph)
    # macOS
    # subprocess.run(['open', graph])
    # Linux
    # subprocess.run(['xdg-open', graph])
```

### Parse JSON Report

```python
import json

with open('analysis_outputs/analysis_report.json', 'r') as f:
    report = json.load(f)

# Explore structure
print("Report Keys:")
for key in report.keys():
    print(f"  - {key}")

# Example: Get class distribution
print("\nClass Distribution:")
print(report['class_distribution'])

# Example: Top correlated features
print("\nTop Correlated Pairs:")
for pair in report['correlations'][:5]:
    print(f"  {pair['feature1']} ↔ {pair['feature2']}: {pair['correlation']:.3f}")

# Example: Attack types
print("\nAttack Types:")
for attack_type, count in report['attack_distribution'].items():
    pct = count / report['total_attack_flows'] * 100
    print(f"  {attack_type}: {count} ({pct:.1f}%)")
```

---

## Project Structure Reference

```
d:\Documents\ML model\
├── README.md                    ← Main hub (navigation)
├── 01_PROBLEM_STATEMENT.md      ← Business case
├── 02_SOLUTION_OVERVIEW.md      ← Technical approach
├── 03_DATASET_ANALYSIS.md       ← Feature explanations
├── 04_MODEL_ARCHITECTURE.md     ← ML strategy
├── 05_INTEGRATION_GUIDE.md      ← Deployment options
├── 06_FUTURE_SCOPE.md           ← Roadmap
├── 07_QUICK_START.md            ← This file
├── MODEL_READING_PLAN.md        ← Strategy document
├── SETUP_SUMMARY.md             ← Setup checklist
│
├── unsw_nb15_analysis.py        ← Main analysis script
├── download_and_analyze.py      ← Download helper
├── UNSW_NB15.csv                ← Dataset (after download)
├── dataset_info.json            ← Dataset metadata
│
├── analysis_outputs/            ← Generated outputs
│   ├── 01_class_distribution.png
│   ├── 02_numeric_distributions.png
│   ├── ... (10 more PNG visualizations)
│   └── analysis_report.json
│
├── .venv/                       ← Virtual environment
│   ├── bin/                     ← (macOS/Linux)
│   └── Scripts/                 ← (Windows)
│
├── models/                      ← (Phase 2+, not yet)
│   ├── baseline_lr.pkl
│   ├── baseline_dt.pkl
│   └── model_metadata.json
│
└── training/                    ← (Phase 2+, not yet)
    ├── train_baseline.py
    ├── train_ensemble.py
    └── optimize_threshold.py
```

---

## Running Python Scripts Directly

### From Command Line
```bash
# Basic run (uses default args)
python unsw_nb15_analysis.py

# With custom arguments (if script supports)
python unsw_nb15_analysis.py --data UNSW_NB15.csv --outdir analysis_outputs

# With environment variable
export DATA_PATH="/path/to/UNSW_NB15.csv"
python unsw_nb15_analysis.py
```

### From Python Interpreter
```python
# Interactive mode (useful for exploration)
python

# In interpreter:
>>> import pandas as pd
>>> df = pd.read_csv('UNSW_NB15.csv')
>>> print(df.shape)
(82332, 45)
>>> print(df.columns)
Index(['id', 'dur', 'proto', ..., 'label', 'attack_cat'], dtype='object')
>>> print(df['label'].value_counts())
1    45332
0    37000
Name: label, dtype: int64
>>> exit()
```

---

## Accessing Documentation Locally

### View Full README
```bash
# macOS/Linux
less README.md  # or: more, cat, nano

# Windows
type README.md  # or open in any text editor

# Better: Open in VS Code
code README.md
```

### Search Documentation
```bash
# Find all mentions of "false positive"
grep -r "false positive" .

# Find all Python files
find . -name "*.py"

# Count lines of code
wc -l *.py

# Windows equivalent
findstr /R "false positive" *.md
```

---

## Next: Model Training (Phase 2)

When you're ready to build the ML model:

1. **Review** [04_MODEL_ARCHITECTURE.md](04_MODEL_ARCHITECTURE.md)
2. **Create** `training/train_baseline.py` with Logistic Regression
3. **Run**: `python training/train_baseline.py`
4. **Evaluate**: Check FPR on validation set
5. **Report**: Document baseline performance

**Estimated Time**: 2-3 weeks for Phase 1 baseline + tuning

---

## Support & Resources

### Documentation Structure
- **Problem & Business**: [01_PROBLEM_STATEMENT.md](01_PROBLEM_STATEMENT.md)
- **Technical Design**: [02_SOLUTION_OVERVIEW.md](02_SOLUTION_OVERVIEW.md)
- **Data Understanding**: [03_DATASET_ANALYSIS.md](03_DATASET_ANALYSIS.md)
- **Model Implementation**: [04_MODEL_ARCHITECTURE.md](04_MODEL_ARCHITECTURE.md)
- **Deployment**: [05_INTEGRATION_GUIDE.md](05_INTEGRATION_GUIDE.md)
- **Future Plans**: [06_FUTURE_SCOPE.md](06_FUTURE_SCOPE.md)
- **This Guide**: 07_QUICK_START.md

### For Questions
1. **Dataset questions** → Check `analysis_report.json` and visualizations
2. **Implementation questions** → See inline comments in `.py` scripts
3. **Architecture questions** → Read solution docs in order (01 → 07)
4. **Stuck?** → Check "Common Issues & Solutions" section (above)

---

## Troubleshooting Checklist

- [ ] Python version >= 3.9? (`python --version`)
- [ ] Virtual environment activated? (`which python` should show `.venv`)
- [ ] All packages installed? (`pip list | grep -E "pandas|kagglehub"`)
- [ ] Kaggle API credentials set up? (`ls ~/.kaggle/kaggle.json`)
- [ ] Dataset downloaded? (`ls UNSW_NB15.csv`)
- [ ] Analysis script runs? (`python unsw_nb15_analysis.py`)
- [ ] Outputs generated? (`ls analysis_outputs/ | wc -l` should show 13)

---

## Performance Baseline

On typical hardware:

| Task | Time | Details |
|------|------|---------|
| Dataset download | 1-3 min | 500 MB from Kaggle |
| Data loading | 5-10 sec | Read 82K rows into pandas |
| Feature engineering | 20-30 sec | Compute all 44 attributes |
| Correlation analysis | 10-15 sec | 82K rows × 44 features matrix |
| Visualization creation | 30-45 sec | Generate 12 PNG plots |
| **Total** | **3-5 min** | Excluding download |

---

## Success Indicators ✅

You're ready to move forward when you see:

✅ Virtual environment created and activated  
✅ All packages installed without errors  
✅ Dataset downloaded (UNSW_NB15.csv exists)  
✅ Analysis script completed successfully  
✅ 12 PNG visualizations in `analysis_outputs/`  
✅ `analysis_report.json` generated  
✅ Console output shows "Ready for model training!"  
✅ You understand the data (read doc 03)  

---

**Quick Start Version**: 1.0  
**Last Updated**: 2024  
**Estimated Setup Time**: 10 minutes (on good internet)  
**Next Phase**: Model development (2-3 weeks)  
**Status**: Ready to begin!

---

### 🚀 You're All Set!

**Next command**: 
```bash
python unsw_nb15_analysis.py
```

**Then explore**: [README.md](README.md) and the generated visualizations.

Welcome to the project! 🎉
