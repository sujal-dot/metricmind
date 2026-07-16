#!/usr/bin/env python3
"""
MetricMind Data Cleaning Pipeline
Cleans raw sales data into a processed, standardized dataset
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
import re

import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Configure paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
LOG_DIR = BACKEND_DIR / "logs"
REPORTS_DIR = BACKEND_DIR / "reports"
DATA_DIR = BACKEND_DIR.parent / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Create directories if missing
for dir_path in [LOG_DIR, REPORTS_DIR, PROCESSED_DATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Configure logging
LOG_FILE = LOG_DIR / f"cleaning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def standardize_column_name(col: str) -> str:
    """Convert column name to lowercase snake_case."""
    col = col.strip()
    col = col.lower()
    # Replace spaces and special characters with underscores
    col = re.sub(r"[^a-z0-9]+", "_", col)
    # Remove leading/trailing underscores
    col = col.strip("_")
    return col


def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform all data cleaning steps and return cleaned DataFrame with metrics.
    """
    metrics = {
        "total_rows_before": len(df),
        "duplicates_removed": 0,
        "missing_values_before": {},
        "missing_values_after": {},
        "invalid_dates_corrected": 0,
        "invalid_rows_removed": 0,
        "total_rows_after": 0
    }

    df_clean = df.copy()

    # Step 1: Remove duplicates
    logger.info("Step 1: Removing duplicate records...")
    duplicates = df_clean.duplicated().sum()
    metrics["duplicates_removed"] = duplicates
    if duplicates > 0:
        df_clean = df_clean.drop_duplicates(keep="first")
        logger.info(f"Removed {duplicates} duplicate rows")
    else:
        logger.info("No duplicate rows found")

    # Step 3: Standardize column names first (makes subsequent steps easier)
    logger.info("Step 3: Standardizing column names...")
    df_clean.columns = [standardize_column_name(col) for col in df_clean.columns]
    logger.info(f"Column names standardized: {list(df_clean.columns)}")

    # Capture missing values before cleaning
    logger.info("Step 2: Analyzing missing values...")
    metrics["missing_values_before"] = df_clean.isnull().sum().to_dict()

    # Step 5: Standardize text fields
    logger.info("Step 5: Standardizing text fields...")
    text_cols = df_clean.select_dtypes(include=["object"]).columns
    for col in text_cols:
        df_clean[col] = df_clean[col].astype(str).str.strip()
        # Remove invisible characters
        df_clean[col] = df_clean[col].str.replace(r"\s+", " ", regex=True)
        # Normalize encoding
        df_clean[col] = df_clean[col].str.normalize("NFKD")

    # Step 4: Fix date columns
    logger.info("Step 4: Fixing date columns...")
    date_cols = []
    for col in df_clean.columns:
        if "date" in col.lower():
            date_cols.append(col)
    
    for col in date_cols:
        logger.info(f"Processing date column: {col}")
        original_count = len(df_clean)
        df_clean[col] = pd.to_datetime(df_clean[col], errors="coerce")
        invalid_count = df_clean[col].isnull().sum() - metrics["missing_values_before"].get(col, 0)
        metrics["invalid_dates_corrected"] += max(0, invalid_count)
        # Convert to YYYY-MM-DD
        df_clean[col] = df_clean[col].dt.date
        logger.info(f"Standardized {col} to YYYY-MM-DD format")

    # Step 6: Validate numeric columns
    logger.info("Step 6: Validating numeric columns...")
    numeric_cols = ["sales", "profit", "quantity", "discount"]
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")
            # Handle impossible values
            if col in ["quantity", "discount"]:
                df_clean[col] = df_clean[col].clip(lower=0)
            logger.info(f"Validated numeric column: {col}")

    # Step 2 (continued): Handle missing values
    logger.info("Step 2: Handling missing values...")
    required_id_cols = ["row_id", "order_id", "customer_id", "product_id"]
    text_cols_to_replace = ["customer_name", "segment", "country", "city", "state", "region", "category", "sub_category", "product_name", "ship_mode"]
    
    for col in df_clean.columns:
        if col in text_cols_to_replace:
            df_clean[col] = df_clean[col].fillna("Unknown")
        elif pd.api.types.is_numeric_dtype(df_clean[col]):
            if col not in required_id_cols:
                median_val = df_clean[col].median()
                df_clean[col] = df_clean[col].fillna(median_val)
    
    # Step 9: Remove invalid records
    logger.info("Step 9: Removing invalid records...")
    # Identify rows with missing critical IDs
    critical_cols = [col for col in required_id_cols if col in df_clean.columns]
    invalid_mask = df_clean[critical_cols].isnull().any(axis=1)
    # Identify completely empty rows
    empty_mask = df_clean.isnull().all(axis=1)
    # Combine masks
    remove_mask = invalid_mask | empty_mask
    invalid_count = remove_mask.sum()
    metrics["invalid_rows_removed"] = invalid_count
    
    if invalid_count > 0:
        logger.warning(f"Removing {invalid_count} invalid records")
        df_clean = df_clean[~remove_mask]
    
    # Capture missing values after cleaning
    metrics["missing_values_after"] = df_clean.isnull().sum().to_dict()
    
    # Step 8: Validate data types
    logger.info("Step 8: Validating data types...")
    # Ensure numeric columns are correct types
    for col in numeric_cols:
        if col in df_clean.columns:
            if col in ["quantity"]:
                df_clean[col] = df_clean[col].astype(int)
            else:
                df_clean[col] = pd.to_numeric(df_clean[col], downcast="float")
    
    # Final metrics
    metrics["total_rows_after"] = len(df_clean)
    logger.info(f"Cleaning complete: {metrics['total_rows_before']} → {metrics['total_rows_after']} rows")
    
    return df_clean, metrics


def main() -> None:
    logger.info("=" * 80)
    logger.info("MetricMind Data Cleaning Pipeline Starting")
    logger.info("=" * 80)
    
    # Find raw CSV files
    csv_files = list(RAW_DATA_DIR.glob("*.csv"))
    if not csv_files:
        logger.error("No CSV files found in data/raw directory!")
        return
    
    # Process all.csv if available, otherwise process first CSV
    target_file = RAW_DATA_DIR / "all.csv"
    if target_file.exists():
        input_path = target_file
    else:
        input_path = csv_files[0]
    
    logger.info(f"Processing input file: {input_path}")
    
    # Load raw data
    try:
        df = pd.read_csv(input_path, encoding="latin-1")
        logger.info(f"Loaded {len(df)} rows from {input_path.name}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        return
    
    # Clean data
    df_clean, metrics = clean_data(df)
    
    # Save cleaned data
    output_path = PROCESSED_DATA_DIR / "clean_sales.csv"
    df_clean.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Cleaned data saved to: {output_path}")
    
    # Save metrics for report generation
    metrics_path = REPORTS_DIR / "cleaning_metrics.json"
    import json
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"Cleaning metrics saved to: {metrics_path}")
    
    logger.info("=" * 80)
    logger.info("Data Cleaning Pipeline Complete")
    logger.info("=" * 80)
    logger.info(f"Log file: {LOG_FILE}")


if __name__ == "__main__":
    main()
