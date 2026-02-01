import pandas as pd
import numpy as np
import math
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

def clean_for_json(obj):
    """
    Recursively clean dictionary/list for JSON serialization.
    Handles:
    - NaN, Infinity, -Infinity -> None
    - Numpy types -> Native Python types
    """
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif isinstance(obj, (float, np.float64, np.float32)):
        if pd.isna(obj) or math.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, np.generic):
        return obj.item()
    return obj

def plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def generate_plots(df: pd.DataFrame):
    plots = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # 1. Correlation Heatmap
    if len(numeric_cols) > 1:
        plt.figure(figsize=(10, 8))
        corr = df[numeric_cols].corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title("Correlation Heatmap")
        plots["heatmap"] = plot_to_base64(plt.gcf())
    
    # 2. Distributions (Top 3 numeric)
    for col in numeric_cols[:3]:
        plt.figure(figsize=(8, 5))
        sns.histplot(df[col].dropna(), kde=True)
        plt.title(f"Distribution of {col}")
        plots[f"dist_{col}"] = plot_to_base64(plt.gcf())
        
    return plots

def auto_eda(df: pd.DataFrame):
    # Separate numeric and categorical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    # Basic Info
    # Calculate true failures for EDA
    failure_count = 0
    possible_cols = ["Machine failure", "Failure", "Target", "failure", "target"]
    found_col = next((c for c in possible_cols if c in df.columns), None)
    
    if found_col:
        failure_count = int(df[found_col].sum())
    else:
        # If no explicit failure column, default to 0 (or rows? User wants failures specifically)
        # For EDA, if we can't find a failure column, saying 0 failures is technically more accurate 
        # than saying "All rows are failures". 
        # But to be consistent with upload endpoint, let's keep the fallback but maybe cleaner.
        # Actually, let's stick to the logic: if no failure col, maybe show 0 or handle in frontend.
        # Current upload endpoint falls back to df.shape[0]. Let's match that to avoid UI glitch.
        failure_count = df.shape[0]

    # Calculate Failure Rate
    failure_rate = 0.0
    if df.shape[0] > 0:
        failure_rate = round((failure_count / df.shape[0]) * 100, 2)

    summary = {
        "shape": df.shape,
        "failure_count": failure_count,
        "failure_rate": failure_rate,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols
    }

    # Descriptive Statistics
    desc = df.describe(include='all')
    summary["statistics"] = desc.to_dict()

    # Correlations (Numeric only)
    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr()
        summary["correlations"] = corr_matrix.to_dict()
    else:
        summary["correlations"] = {}

    # Sample Data (First 5 rows)
    summary["sample"] = df.head(5).to_dict(orient="records")

    # Simple Outlier Analysis (IQR Method) for numeric cols
    outliers = {}
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
        if count > 0:
            outliers[col] = int(count)
            
    summary["outliers"] = outliers
    
    # Categorical Distributions (Top 10 counts)
    distributions = {}
    for col in categorical_cols:
        # Get top 10 values
        counts = df[col].value_counts().head(10).to_dict()
        distributions[col] = counts
    summary["distributions"] = distributions

    # Final Recursive Cleaning
    return clean_for_json(summary)

def get_failure_stats(df: pd.DataFrame):
    """
    Returns raw dictionary of failure statistics.
    """
    possible_cols = ["Machine failure", "Failure", "Target", "failure", "target"]
    target_col = next((c for c in possible_cols if c in df.columns), None)
    
    if not target_col:
        return {"error": "No target column found"}

    total_records = len(df)
    total_failures = int(df[target_col].sum())
    
    modes = []
    # Identify Failure Modes
    for col in df.columns:
        if col == target_col: continue
        if pd.api.types.is_numeric_dtype(df[col]):
            unique_vals = set(df[col].dropna().unique())
            if unique_vals.issubset({0, 1, 0.0, 1.0}):
                count = int(df[col].sum())
                if count > 0:
                    pct = (count / total_failures * 100) if total_failures > 0 else 0
                    modes.append({"name": col, "count": count, "percent": pct})
    
    modes.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "total_records": total_records,
        "total_failures": total_failures,
        "modes": modes
    }

def analyze_failure_modes(df: pd.DataFrame):
    stats = get_failure_stats(df)
    if "error" in stats:
        return "No specific failure label column identified. Cannot categorize failures automatically."
        
    total_failures = stats["total_failures"]
    if total_failures == 0:
        return "No failures found in the dataset."

    report = [f"### Analysis Result"]
    report.append(f"**Total Failures Detected**: {total_failures}")
    
    if stats["modes"]:
        report.append("\n**Breakdown by Failure Mode:**")
        count_sum = 0
        for m in stats["modes"]:
            report.append(f"- **{m['name']}**: {m['count']} ({m['percent']:.1f}%)")
            count_sum += m['count']
            
        if count_sum < total_failures:
            report.append(f"\n> **Warning**: The sum of failure modes ({count_sum}) is less than total failures ({total_failures}). Some failures may be uncategorized or unlabeled.")
    else:
        report.append("\nNo specific binary failure type columns found. Failures may be unlabeled.")

    report.append("\n*This analysis was generated instantly based on dataset statistics.*")
    return "\n".join(report)

def get_correlation_stats(df: pd.DataFrame):
    """
    Returns raw correlation data.
    """
    possible_cols = ["Machine failure", "Failure", "Target", "failure", "target"]
    target_col = next((c for c in possible_cols if c in df.columns), None)
    
    if not target_col:
        return {"error": "No target column"}
        
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    stats = {"top_correlations": [], "shifts": []}
    
    try:
        # 1. Correlations
        corrs = df[numeric_cols].corrwith(df[target_col]).sort_values(ascending=False)
        top_corr = corrs[abs(corrs) > 0.1].drop(target_col, errors='ignore')
        
        for col, val in top_corr.head(5).items():
            stats["top_correlations"].append({"feature": col, "value": val})
            
        # 2. Shifts
        failures = df[df[target_col] == 1]
        normal = df[df[target_col] == 0]
        
        if not failures.empty and not normal.empty:
            for col in numeric_cols:
                if col == target_col or "id" in col.lower(): continue
                fail_mean = failures[col].mean()
                norm_mean = normal[col].mean()
                if norm_mean != 0:
                    pct_diff = ((fail_mean - norm_mean) / norm_mean) * 100
                    if abs(pct_diff) > 5:
                        stats["shifts"].append({
                            "feature": col,
                            "pct_diff": pct_diff,
                            "fail_mean": fail_mean,
                            "norm_mean": norm_mean
                        })
    except Exception as e:
        return {"error": str(e)}
        
    return stats

def analyze_correlations(df: pd.DataFrame):
    stats = get_correlation_stats(df)
    if "error" in stats:
        if stats["error"] == "No target column":
            return "No failure label found (Machine failure/Target). Cannot analyze root cause."
        return f"Could not calculate correlations: {stats['error']}"
        
    summary = ["### Statistical Root Cause Analysis"]
    
    # Corrs
    if stats["top_correlations"]:
        summary.append("**Top Correlated Factors (1.0 = Perfect Cause):**")
        for item in stats["top_correlations"]:
            summary.append(f"- {item['feature']}: {item['value']:.2f}")
    else:
        summary.append("No strong linear correlations found with failure.")
        
    # Shifts
    if stats["shifts"]:
        summary.append("\n**Sensor Behavior During Failure:**")
        for item in stats["shifts"]:
            direction = "HIGHER" if item['pct_diff'] > 0 else "LOWER"
            summary.append(f"- {item['feature']}: {abs(item['pct_diff']):.1f}% {direction} during failure (Avg: {item['fail_mean']:.1f} vs {item['norm_mean']:.1f})")
            
    return "\n".join(summary)