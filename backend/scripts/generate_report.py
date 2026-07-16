#!/usr/bin/env python3
"""
MetricMind Cleaning Report Generator
Generates a comprehensive Markdown report of the data cleaning process
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json

import pandas as pd

# Configure paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
REPORTS_DIR = BACKEND_DIR / "reports"
DATA_DIR = BACKEND_DIR.parent / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

REPORTS_DIR.mkdir(exist_ok=True)
LOG_FILE = REPORTS_DIR / f"report_generator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def calculate_quality_score(metrics: Dict[str, Any]) -> float:
    """Calculate data quality score from 0-100."""
    score = 100.0
    
    total_before = metrics["total_rows_before"]
    if total_before == 0:
        return 0.0
    
    # Penalize for duplicates
    duplicate_penalty = (metrics["duplicates_removed"] / total_before) * 20
    score -= min(duplicate_penalty, 20)
    
    # Penalize for missing values after cleaning
    total_missing_after = sum(metrics["missing_values_after"].values())
    total_cells_after = total_before * len(metrics["missing_values_after"])
    missing_penalty = (total_missing_after / max(total_cells_after, 1)) * 30
    score -= min(missing_penalty, 30)
    
    # Penalize for invalid dates
    date_penalty = (metrics["invalid_dates_corrected"] / max(total_before, 1)) * 20
    score -= min(date_penalty, 20)
    
    # Penalize for invalid rows removed
    invalid_penalty = (metrics["invalid_rows_removed"] / max(total_before, 1)) * 30
    score -= min(invalid_penalty, 30)
    
    return max(score, 0.0)


def generate_report(metrics: Dict[str, Any], df: pd.DataFrame) -> str:
    """Generate Markdown cleaning report."""
    quality_score = calculate_quality_score(metrics)
    
    report = f"""# MetricMind Data Cleaning Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Value |
|--------|-------|
| Total Rows Before Cleaning | {metrics['total_rows_before']:,} |
| Total Rows After Cleaning | {metrics['total_rows_after']:,} |
| Duplicate Rows Removed | {metrics['duplicates_removed']:,} |
| Invalid Dates Corrected | {metrics['invalid_dates_corrected']:,} |
| Invalid Rows Removed | {metrics['invalid_rows_removed']:,} |
| Final Dataset Size | {len(df):,} rows × {len(df.columns)} columns |
| **Data Quality Score** | **{quality_score:.1f} / 100** |

## Missing Values

### Before Cleaning
| Column | Missing Count |
|--------|---------------|
"""
    
    for col, count in metrics["missing_values_before"].items():
        if count > 0:
            report += f"| {col} | {count:,} |\n"
    
    report += """
### After Cleaning
| Column | Missing Count |
|--------|---------------|
"""
    
    for col, count in metrics["missing_values_after"].items():
        if count > 0:
            report += f"| {col} | {count:,} |\n"
    
    report += f"""
## Column Summary

| Column | Data Type | Non-Null Count | Unique Values |
|--------|-----------|----------------|---------------|
"""
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].notnull().sum()
        unique = df[col].nunique()
        report += f"| {col} | {dtype} | {non_null:,} | {unique:,} |\n"
    
    report += """
## Notes

- Data cleaning process completed successfully
- Duplicate records were removed (first valid record preserved)
- Missing values were handled appropriately (text → "Unknown", numeric → median)
- Date columns standardized to YYYY-MM-DD format
- Text fields trimmed and normalized
- Numeric columns validated and corrected
- Invalid records removed only when unrecoverable
"""
    
    return report


def main() -> None:
    logger.info("=" * 80)
    logger.info("MetricMind Cleaning Report Generator Starting")
    logger.info("=" * 80)

    metrics_path = REPORTS_DIR / "cleaning_metrics.json"
    data_path = PROCESSED_DATA_DIR / "clean_sales.csv"

    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        return
    if not data_path.exists():
        logger.error(f"Clean data file not found: {data_path}")
        return

    try:
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
        
        df = pd.read_csv(data_path, encoding="utf-8")
        logger.info(f"Loaded metrics and data for {len(df)} rows")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    report = generate_report(metrics, df)
    report_path = REPORTS_DIR / "cleaning_report.md"
    with open(report_path, "w") as f:
        f.write(report)

    logger.info(f"Cleaning report generated: {report_path}")
    logger.info("=" * 80)
    logger.info("Report Generation Complete")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
