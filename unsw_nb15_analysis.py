"""
UNSW-NB15 Network Intrusion Detection Dataset - Exploratory Data Analysis

This script performs comprehensive EDA on the UNSW-NB15 dataset including:
- Dataset overview and quality checks
- Class distribution and imbalance analysis
- Feature correlation and multicollinearity detection
- Statistical distributions and outlier detection
- Feature importance hints from variance analysis
- Preprocessing recommendations
- Attack category analysis

Usage:
    python unsw_nb15_analysis.py --data UNSW_NB15.csv --outdir analysis_outputs

Chart index:
    Chart 01 -> analyze_class_distribution()       -> 01_class_distribution.png
    Chart 02 -> analyze_numeric_distributions()    -> 02_numeric_distributions.png
    Chart 03 -> analyze_correlations()             -> 03_correlation_heatmap.png
    Chart 04 -> analyze_attack_categories()        -> 04_attack_categories.png
    Chart 05 -> analyze_categorical_distributions()-> 05_categorical_distributions.png
    Chart 06 -> analyze_features_by_class()        -> 06_features_by_class.png
    Chart 07 -> analyze_boxplots()                 -> 07_boxplots_by_class.png
    Chart 08 -> analyze_flow_duration_and_rate()   -> 08_flow_characteristics.png
    Chart 09 -> analyze_bytes_packets_relationship()-> 09_bytes_packets_analysis.png
    Chart 10 -> analyze_tcp_metrics()              -> 10_tcp_metrics.png
    Chart 11 -> analyze_contextual_features()      -> 11_contextual_features.png
    Chart 12 -> analyze_attack_patterns()          -> 12_attack_patterns.png
"""

import argparse
import json
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

# Configure plotting
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10


def detect_label_column(df: pd.DataFrame) -> str:
    """Detect the label/target column in the dataset."""
    candidates = ["label", "Label", "class", "Class", "target", "Target"]
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError(
        "No label column found. Expected one of: label, Label, class, Class, target, Target"
    )


def analyze_class_distribution(df: pd.DataFrame, label_col: str, outdir: Path) -> dict:
    """[Chart 01] Analyze class distribution and imbalance.

    Output: 01_class_distribution.png
    """
    print("\n" + "=" * 70)
    print("CLASS DISTRIBUTION ANALYSIS")
    print("=" * 70)

    class_counts = df[label_col].value_counts(dropna=False)
    class_pcts = (class_counts / len(df) * 100).round(2)

    print(f"\nClass Counts:")
    for cls, count in class_counts.items():
        pct = class_pcts[cls]
        print(f"  {cls}: {count:,} ({pct}%)")

    # Imbalance ratio
    if len(class_counts) == 2:
        ratio = class_counts.iloc[0] / class_counts.iloc[1]
        print(f"\nImbalance Ratio: {ratio:.2f}:1")
        if ratio > 3 or ratio < 1/3:
            print("⚠️  HIGH IMBALANCE - Consider SMOTE or class weighting")
        elif ratio > 1.5 or ratio < 2/3:
            print("⚠️  MODERATE IMBALANCE - Monitor both classes during training")
        else:
            print("✓ BALANCED - Standard train/validation split acceptable")

    # Visualization
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Bar chart
    class_counts.plot(kind="bar", ax=axes[0], color=["#2ecc71", "#e74c3c"])
    axes[0].set_title(f"Class Distribution (n={len(df):,})", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Class")
    axes[0].set_ylabel("Count")
    axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=0)

    # Pie chart
    axes[1].pie(class_counts, labels=class_counts.index, autopct="%1.1f%%", startangle=90)
    axes[1].set_title("Class Distribution (Percentage)", fontsize=12, fontweight="bold")

    plt.tight_layout()
    chart_path = outdir / "01_class_distribution.png"
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {
        "class_counts": class_counts.to_dict(),
        "imbalance_ratio": ratio if len(class_counts) == 2 else None,
        "chart": str(chart_path),
    }


def analyze_features(df: pd.DataFrame, label_col: str, outdir: Path) -> dict:
    """Analyze feature types and quality."""
    print("\n" + "=" * 70)
    print("FEATURE ANALYSIS")
    print("=" * 70)

    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

    # Remove label from feature lists if present
    if label_col in numeric_cols:
        numeric_cols.remove(label_col)
    if label_col in categorical_cols:
        categorical_cols.remove(label_col)

    print(f"\nNumeric Features: {len(numeric_cols)}")
    print(f"  {numeric_cols[:5]}{'...' if len(numeric_cols) > 5 else ''}")

    print(f"\nCategorical Features: {len(categorical_cols)}")
    for col in categorical_cols:
        unique_count = df[col].nunique()
        print(f"  {col}: {unique_count} unique values")

    # Missing values analysis
    print(f"\nMissing Values:")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("  ✓ NO MISSING VALUES - Dataset is complete!")
    else:
        print("  ⚠️  Missing values detected:")
        print(missing[missing > 0])

    # Data types
    print(f"\nData Size Stats:")
    print(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    print(f"  Total rows: {len(df):,}")
    print(f"  Total columns: {len(df.columns)}")

    return {
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "missing_count": int(missing.sum()),
        "memory_mb": float(df.memory_usage(deep=True).sum() / 1024**2),
    }


def analyze_numeric_distributions(df: pd.DataFrame, numeric_cols: list, outdir: Path) -> dict:
    """[Chart 02] Analyze distributions and outliers in numeric features.

    Output: 02_numeric_distributions.png
    """
    print("\n" + "=" * 70)
    print("NUMERIC FEATURE DISTRIBUTIONS")
    print("=" * 70)

    # Top 10 features by variance
    variances = df[numeric_cols].var().sort_values(ascending=False)
    high_var_cols = variances.head(10).index.tolist()

    print("\nTop 10 Features by Variance:")
    for col in high_var_cols:
        print(f"  {col}: {variances[col]:.2e}")

    # Outlier detection using IQR
    print("\nOutlier Detection (IQR Method):")
    outlier_summary = {}
    for col in high_var_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_count = outliers.sum()
        outlier_pct = (outlier_count / len(df) * 100)

        outlier_summary[col] = {
            "count": outlier_count,
            "percentage": outlier_pct,
        }

        if outlier_count > 0:
            print(f"  {col}: {outlier_count:,} outliers ({outlier_pct:.1f}%)")

    # Distribution plots
    fig, axes = plt.subplots(2, 5, figsize=(16, 8))
    axes = axes.flatten()

    for idx, col in enumerate(high_var_cols):
        axes[idx].hist(df[col], bins=50, edgecolor="black", alpha=0.7, color="#3498db")
        axes[idx].set_title(f"{col}", fontsize=10, fontweight="bold")
        axes[idx].set_xlabel("Value")
        axes[idx].set_ylabel("Frequency")
        axes[idx].grid(True, alpha=0.3)

    plt.tight_layout()
    dist_path = outdir / "02_numeric_distributions.png"
    plt.savefig(dist_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"outlier_summary": outlier_summary, "high_variance_features": high_var_cols}


def analyze_correlations(df: pd.DataFrame, numeric_cols: list, outdir: Path) -> dict:
    """[Chart 03] Analyze feature correlations and multicollinearity.

    Output: 03_correlation_heatmap.png
    """
    print("\n" + "=" * 70)
    print("CORRELATION & MULTICOLLINEARITY ANALYSIS")
    print("=" * 70)

    corr_matrix = df[numeric_cols].corr()

    # Find highly correlated pairs
    print("\nHighly Correlated Feature Pairs (|r| > 0.9):")
    high_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            if abs(corr_matrix.iloc[i, j]) > 0.9:
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_val = corr_matrix.iloc[i, j]
                high_corr_pairs.append((col1, col2, corr_val))
                print(f"  {col1} ↔ {col2}: {corr_val:.3f}")

    if not high_corr_pairs:
        print("  ✓ No highly correlated pairs found")

    # Heatmap - select top features by variance
    top_features = df[numeric_cols].var().sort_values(ascending=False).head(15).index.tolist()
    corr_subset = df[top_features].corr()

    plt.figure(figsize=(12, 10))
    sns.heatmap(
        corr_subset,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        cbar_kws={"label": "Correlation"},
    )
    plt.title("Feature Correlation Heatmap (Top 15 by Variance)", fontsize=12, fontweight="bold")
    plt.tight_layout()
    heatmap_path = outdir / "03_correlation_heatmap.png"
    plt.savefig(heatmap_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"high_correlation_pairs": high_corr_pairs, "heatmap": str(heatmap_path)}


def analyze_categorical_distributions(df: pd.DataFrame, outdir: Path) -> dict:
    """[Chart 05] Analyze categorical feature distributions.

    Output: 05_categorical_distributions.png
    """
    print("\n" + "=" * 70)
    print("CATEGORICAL FEATURE DISTRIBUTIONS")
    print("=" * 70)

    categorical_cols = ["proto", "service", "state"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))

    for idx, col in enumerate(categorical_cols):
        if col in df.columns:
            counts = df[col].value_counts().head(15)  # Top 15
            print(f"\n{col} (Top 15):")
            print(counts)

            counts.plot(kind="barh", ax=axes[idx], color="#3498db")
            axes[idx].set_title(f"{col.upper()} Distribution", fontsize=11, fontweight="bold")
            axes[idx].set_xlabel("Count")
            axes[idx].invert_yaxis()

    plt.tight_layout()
    cat_path = outdir / "05_categorical_distributions.png"
    plt.savefig(cat_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"chart": str(cat_path)}


def analyze_features_by_class(df: pd.DataFrame, label_col: str, outdir: Path) -> dict:
    """[Chart 06] Compare feature distributions between Normal and Attack.

    Output: 06_features_by_class.png
    """
    print("\n" + "=" * 70)
    print("FEATURE DISTRIBUTIONS BY CLASS (Normal vs Attack)")
    print("=" * 70)

    # Select top 6 features by variance
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    if label_col in numeric_cols:
        numeric_cols.remove(label_col)
    if "id" in numeric_cols:
        numeric_cols.remove("id")

    top_features = df[numeric_cols].var().sort_values(ascending=False).head(6).index.tolist()

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    for idx, feature in enumerate(top_features):
        label_0 = df[df[label_col] == 0][feature]
        label_1 = df[df[label_col] == 1][feature]

        axes[idx].hist([label_0, label_1], bins=40, alpha=0.6, label=["Normal", "Attack"], color=["#2ecc71", "#e74c3c"])
        axes[idx].set_title(f"{feature} by Class", fontsize=10, fontweight="bold")
        axes[idx].set_xlabel(feature)
        axes[idx].set_ylabel("Frequency")
        axes[idx].legend()
        axes[idx].set_yscale("log")  # Log scale for better visibility

    plt.tight_layout()
    class_path = outdir / "06_features_by_class.png"
    plt.savefig(class_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"chart": str(class_path)}


def analyze_boxplots(df: pd.DataFrame, label_col: str, outdir: Path) -> dict:
    """[Chart 07] Create box plots for outlier detection by class.

    Output: 07_boxplots_by_class.png
    """
    print("\n" + "=" * 70)
    print("BOX PLOTS - OUTLIER DETECTION BY CLASS")
    print("=" * 70)

    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    if label_col in numeric_cols:
        numeric_cols.remove(label_col)
    if "id" in numeric_cols:
        numeric_cols.remove("id")

    # Top 8 features by variance
    top_features = df[numeric_cols].var().sort_values(ascending=False).head(8).index.tolist()

    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()

    for idx, feature in enumerate(top_features):
        data_to_plot = [df[df[label_col] == 0][feature], df[df[label_col] == 1][feature]]
        bp = axes[idx].boxplot(data_to_plot, labels=["Normal", "Attack"], patch_artist=True)

        for patch, color in zip(bp["boxes"], ["#2ecc71", "#e74c3c"]):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)

        axes[idx].set_title(f"{feature}", fontsize=10, fontweight="bold")
        axes[idx].set_ylabel("Value")
        axes[idx].grid(True, alpha=0.3)

    plt.tight_layout()
    box_path = outdir / "07_boxplots_by_class.png"
    plt.savefig(box_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"chart": str(box_path)}


def analyze_flow_duration_and_rate(df: pd.DataFrame, label_col: str, outdir: Path) -> dict:
    """[Chart 08] Analyze flow duration and rate patterns.

    Output: 08_flow_characteristics.png
    """
    print("\n" + "=" * 70)
    print("FLOW CHARACTERISTICS ANALYSIS")
    print("=" * 70)

    fig, axes = plt.subplots(2, 2, figsize=(14, 8))

    # Duration distribution
    axes[0, 0].hist(df["dur"], bins=50, color="#3498db", alpha=0.7, edgecolor="black")
    axes[0, 0].set_title("Flow Duration Distribution", fontsize=11, fontweight="bold")
    axes[0, 0].set_xlabel("Duration (seconds)")
    axes[0, 0].set_ylabel("Frequency")
    axes[0, 0].set_yscale("log")

    # Rate distribution
    axes[0, 1].hist(df["rate"], bins=50, color="#9b59b6", alpha=0.7, edgecolor="black")
    axes[0, 1].set_title("Packet Rate Distribution", fontsize=11, fontweight="bold")
    axes[0, 1].set_xlabel("Rate (packets/sec)")
    axes[0, 1].set_ylabel("Frequency")
    axes[0, 1].set_yscale("log")

    # Scatter: Duration vs Rate (Normal)
    normal_data = df[df[label_col] == 0]
    axes[1, 0].scatter(normal_data["dur"], normal_data["rate"], alpha=0.3, s=20, color="#2ecc71", label="Normal")
    axes[1, 0].set_title("Duration vs Rate (NORMAL)", fontsize=11, fontweight="bold")
    axes[1, 0].set_xlabel("Duration (seconds)")
    axes[1, 0].set_ylabel("Rate (packets/sec)")
    axes[1, 0].set_yscale("log")
    axes[1, 0].grid(True, alpha=0.3)

    # Scatter: Duration vs Rate (Attack)
    attack_data = df[df[label_col] == 1]
    axes[1, 1].scatter(attack_data["dur"], attack_data["rate"], alpha=0.3, s=20, color="#e74c3c", label="Attack")
    axes[1, 1].set_title("Duration vs Rate (ATTACK)", fontsize=11, fontweight="bold")
    axes[1, 1].set_xlabel("Duration (seconds)")
    axes[1, 1].set_ylabel("Rate (packets/sec)")
    axes[1, 1].set_yscale("log")
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    flow_path = outdir / "08_flow_characteristics.png"
    plt.savefig(flow_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"chart": str(flow_path)}


def analyze_bytes_packets_relationship(df: pd.DataFrame, label_col: str, outdir: Path) -> dict:
    """[Chart 09] Analyze bytes vs packets relationships.

    Output: 09_bytes_packets_analysis.png
    """
    print("\n" + "=" * 70)
    print("BYTES vs PACKETS ANALYSIS")
    print("=" * 70)

    fig, axes = plt.subplots(2, 2, figsize=(14, 8))

    # Source packets vs bytes
    axes[0, 0].scatter(df[df[label_col] == 0]["spkts"], df[df[label_col] == 0]["sbytes"], 
                       alpha=0.3, s=15, color="#2ecc71", label="Normal")
    axes[0, 0].scatter(df[df[label_col] == 1]["spkts"], df[df[label_col] == 1]["sbytes"], 
                       alpha=0.3, s=15, color="#e74c3c", label="Attack")
    axes[0, 0].set_title("Source: Packets vs Bytes", fontsize=11, fontweight="bold")
    axes[0, 0].set_xlabel("Packets")
    axes[0, 0].set_ylabel("Bytes")
    axes[0, 0].set_xscale("log")
    axes[0, 0].set_yscale("log")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Dest packets vs bytes
    axes[0, 1].scatter(df[df[label_col] == 0]["dpkts"], df[df[label_col] == 0]["dbytes"], 
                       alpha=0.3, s=15, color="#2ecc71", label="Normal")
    axes[0, 1].scatter(df[df[label_col] == 1]["dpkts"], df[df[label_col] == 1]["dbytes"], 
                       alpha=0.3, s=15, color="#e74c3c", label="Attack")
    axes[0, 1].set_title("Destination: Packets vs Bytes", fontsize=11, fontweight="bold")
    axes[0, 1].set_xlabel("Packets")
    axes[0, 1].set_ylabel("Bytes")
    axes[0, 1].set_xscale("log")
    axes[0, 1].set_yscale("log")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Packet loss rate distribution
    axes[1, 0].hist([df[df[label_col] == 0]["sloss"], df[df[label_col] == 1]["sloss"]], 
                    bins=30, alpha=0.6, label=["Normal", "Attack"], color=["#2ecc71", "#e74c3c"])
    axes[1, 0].set_title("Source Loss Distribution", fontsize=11, fontweight="bold")
    axes[1, 0].set_xlabel("Packet Loss (%)")
    axes[1, 0].set_ylabel("Frequency")
    axes[1, 0].legend()

    # Data load comparison
    axes[1, 1].hist([df[df[label_col] == 0]["sload"], df[df[label_col] == 1]["sload"]], 
                    bins=30, alpha=0.6, label=["Normal", "Attack"], color=["#2ecc71", "#e74c3c"])
    axes[1, 1].set_title("Source Load Distribution", fontsize=11, fontweight="bold")
    axes[1, 1].set_xlabel("Load (bits/sec)")
    axes[1, 1].set_ylabel("Frequency")
    axes[1, 1].set_yscale("log")
    axes[1, 1].legend()

    plt.tight_layout()
    bytes_path = outdir / "09_bytes_packets_analysis.png"
    plt.savefig(bytes_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"chart": str(bytes_path)}


def analyze_tcp_metrics(df: pd.DataFrame, label_col: str, outdir: Path) -> dict:
    """[Chart 10] Analyze TCP-specific metrics.

    Output: 10_tcp_metrics.png
    """
    print("\n" + "=" * 70)
    print("TCP METRICS ANALYSIS")
    print("=" * 70)

    tcp_features = ["sttl", "dttl", "tcprtt", "synack", "ackdat", "swin", "dwin"]
    tcp_features = [f for f in tcp_features if f in df.columns]

    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()

    for idx, feature in enumerate(tcp_features):
        axes[idx].hist([df[df[label_col] == 0][feature], df[df[label_col] == 1][feature]], 
                       bins=40, alpha=0.6, label=["Normal", "Attack"], color=["#2ecc71", "#e74c3c"])
        axes[idx].set_title(f"{feature}", fontsize=10, fontweight="bold")
        axes[idx].set_xlabel(feature)
        axes[idx].set_ylabel("Frequency")
        axes[idx].legend()
        axes[idx].grid(True, alpha=0.3)

    # Hide unused subplot
    axes[-1].set_visible(False)

    plt.tight_layout()
    tcp_path = outdir / "10_tcp_metrics.png"
    plt.savefig(tcp_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"chart": str(tcp_path)}


def analyze_contextual_features(df: pd.DataFrame, label_col: str, outdir: Path) -> dict:
    """[Chart 11] Analyze contextual and count-based features.

    Output: 11_contextual_features.png
    """
    print("\n" + "=" * 70)
    print("CONTEXTUAL FEATURES ANALYSIS")
    print("=" * 70)

    contextual_features = ["ct_srv_src", "ct_state_ttl", "ct_dst_ltm", "ct_src_ltm", 
                          "ct_srv_dst", "ct_dst_src_ltm", "ct_src_dport_ltm"]
    contextual_features = [f for f in contextual_features if f in df.columns][:8]

    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()

    for idx, feature in enumerate(contextual_features):
        axes[idx].hist([df[df[label_col] == 0][feature], df[df[label_col] == 1][feature]], 
                       bins=40, alpha=0.6, label=["Normal", "Attack"], color=["#2ecc71", "#e74c3c"])
        axes[idx].set_title(f"{feature}", fontsize=10, fontweight="bold")
        axes[idx].set_xlabel(feature)
        axes[idx].set_ylabel("Frequency")
        axes[idx].legend()
        axes[idx].set_yscale("log")
        axes[idx].grid(True, alpha=0.3)

    # Hide unused subplot
    axes[-1].set_visible(False)

    plt.tight_layout()
    ctx_path = outdir / "11_contextual_features.png"
    plt.savefig(ctx_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"chart": str(ctx_path)}


def analyze_attack_patterns(df: pd.DataFrame, label_col: str, outdir: Path) -> dict:
    """[Chart 12] Analyze attack patterns by category.

    Output: 12_attack_patterns.png
    """
    print("\n" + "=" * 70)
    print("ATTACK PATTERNS BY CATEGORY")
    print("=" * 70)

    if "attack_cat" not in df.columns:
        return {}

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Get top 5 attack categories (excluding Normal)
    attack_cats = df[df["attack_cat"] != "Normal"]["attack_cat"].value_counts().head(5).index

    # 1. Average duration by attack type
    avg_dur = df[df["attack_cat"] != "Normal"].groupby("attack_cat")["dur"].mean().sort_values(ascending=False)
    avg_dur.plot(kind="barh", ax=axes[0, 0], color="#e74c3c")
    axes[0, 0].set_title("Average Flow Duration by Attack Type", fontsize=11, fontweight="bold")
    axes[0, 0].set_xlabel("Duration (seconds)")

    # 2. Average rate by attack type
    avg_rate = df[df["attack_cat"] != "Normal"].groupby("attack_cat")["rate"].mean().sort_values(ascending=False)
    avg_rate.plot(kind="barh", ax=axes[0, 1], color="#9b59b6")
    axes[0, 1].set_title("Average Packet Rate by Attack Type", fontsize=11, fontweight="bold")
    axes[0, 1].set_xlabel("Rate (packets/sec)")

    # 3. Average bytes by attack type
    avg_bytes = df[df["attack_cat"] != "Normal"].groupby("attack_cat")["sbytes"].mean().sort_values(ascending=False)
    avg_bytes.plot(kind="barh", ax=axes[1, 0], color="#3498db")
    axes[1, 0].set_title("Average Source Bytes by Attack Type", fontsize=11, fontweight="bold")
    axes[1, 0].set_xlabel("Bytes")
    axes[1, 0].set_xscale("log")

    # 4. Attack count by top services
    if "service" in df.columns:
        attack_by_service = df[df[label_col] == 1]["service"].value_counts().head(8)
        attack_by_service.plot(kind="barh", ax=axes[1, 1], color="#f39c12")
        axes[1, 1].set_title("Attack Count by Top Services", fontsize=11, fontweight="bold")
        axes[1, 1].set_xlabel("Count")

    plt.tight_layout()
    attack_path = outdir / "12_attack_patterns.png"
    plt.savefig(attack_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {"chart": str(attack_path)}


def analyze_attack_categories(df: pd.DataFrame, outdir: Path) -> dict:
    """[Chart 04] Analyze attack category distribution if available.

    Output: 04_attack_categories.png
    """
    print("\n" + "=" * 70)
    print("ATTACK CATEGORY ANALYSIS")
    print("=" * 70)

    if "attack_cat" not in df.columns:
        print("⊘ attack_cat column not found in dataset")
        return {}

    attack_counts = df["attack_cat"].value_counts()
    print(f"\nAttack Categories ({len(attack_counts)} types):")
    for cat, count in attack_counts.items():
        pct = (count / len(df) * 100)
        print(f"  {cat}: {count:,} ({pct:.1f}%)")

    # Visualization
    plt.figure(figsize=(12, 6))
    attack_counts.plot(kind="barh", color="#e74c3c")
    plt.title("Attack Category Distribution", fontsize=12, fontweight="bold")
    plt.xlabel("Count")
    plt.ylabel("Attack Type")
    plt.tight_layout()
    attack_path = outdir / "04_attack_categories.png"
    plt.savefig(attack_path, dpi=150, bbox_inches="tight")
    plt.close()

    return {
        "attack_categories": attack_counts.to_dict(),
        "chart": str(attack_path),
    }


def generate_summary_report(
    df: pd.DataFrame,
    label_col: str,
    class_info: dict,
    feature_info: dict,
    dist_info: dict,
    corr_info: dict,
    attack_info: dict,
    outdir: Path,
) -> None:
    """Generate a comprehensive JSON summary report."""
    print("\n" + "=" * 70)
    print("GENERATING SUMMARY REPORT")
    print("=" * 70)

    # Convert numpy/pandas types to native Python types
    def convert_to_native(obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(v) for v in obj]
        return obj

    report = {
        "dataset_info": {
            "name": "UNSW-NB15",
            "rows": len(df),
            "columns": len(df.columns),
            "memory_mb": feature_info["memory_mb"],
        },
        "class_distribution": convert_to_native(class_info),
        "features": convert_to_native(feature_info),
        "distributions": convert_to_native({
            "high_variance_features": dist_info["high_variance_features"],
            "outliers": dist_info["outlier_summary"],
        }),
        "correlations": {
            "high_corr_pairs": [[str(c1), str(c2), float(v)] for c1, c2, v in corr_info.get("high_correlation_pairs", [])],
        },
        "attack_categories": convert_to_native(attack_info),
    }

    report_path = outdir / "analysis_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n✓ Summary report saved to: {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="UNSW-NB15 Network Intrusion Detection - Exploratory Data Analysis"
    )
    parser.add_argument(
        "--data",
        default="UNSW_NB15.csv",
        help="Path to UNSW-NB15 CSV file (default: UNSW_NB15.csv)",
    )
    parser.add_argument(
        "--outdir",
        default="analysis_outputs",
        help="Directory to save generated charts and reports (default: analysis_outputs)",
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    print("\n" + "=" * 70)
    print("UNSW-NB15 EXPLORATORY DATA ANALYSIS")
    print("=" * 70)

    # Load dataset
    print(f"\nLoading dataset from: {data_path}")
    try:
        df = pd.read_csv(data_path, encoding="utf-8")
    except UnicodeDecodeError:
        print("UTF-8 failed, retrying with latin1 encoding...")
        df = pd.read_csv(data_path, encoding="latin1")

    print(f"✓ Loaded {len(df):,} rows × {len(df.columns)} columns")

    # Detect label column
    label_col = detect_label_column(df)
    print(f"✓ Detected label column: '{label_col}'")

    # Run analyses
    class_info = analyze_class_distribution(df, label_col, outdir)
    feature_info = analyze_features(df, label_col, outdir)
    dist_info = analyze_numeric_distributions(df, feature_info["numeric_features"], outdir)
    corr_info = analyze_correlations(df, feature_info["numeric_features"], outdir)
    attack_info = analyze_attack_categories(df, outdir)
    cat_info = analyze_categorical_distributions(df, outdir)
    class_compare_info = analyze_features_by_class(df, label_col, outdir)
    boxplot_info = analyze_boxplots(df, label_col, outdir)
    flow_info = analyze_flow_duration_and_rate(df, label_col, outdir)
    bytes_info = analyze_bytes_packets_relationship(df, label_col, outdir)
    tcp_info = analyze_tcp_metrics(df, label_col, outdir)
    ctx_info = analyze_contextual_features(df, label_col, outdir)
    attack_pattern_info = analyze_attack_patterns(df, label_col, outdir)

    # Generate report
    generate_summary_report(
        df, label_col, class_info, feature_info, dist_info, corr_info, attack_info, outdir
    )

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\nGenerated {len(list(outdir.glob('*.png')))} visualization files in '{outdir}':")
    for i, file in enumerate(sorted(outdir.glob("*.png")), 1):
        print(f"  {i:2d}. {file.name}")
    print(f"\n  📊 analysis_report.json")
    print(f"\nTotal: {len(list(outdir.glob('*.png')))} graphs + 1 report")
    print("\n✓ Ready for model training!")


if __name__ == "__main__":
    main()