#!/usr/bin/env python3
"""
MetricMind Clean Data Validator
Validates cleaned sales data after cleaning pipeline
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import numpy as np

# Configure paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
LOG_DIR = BACKEND_DIR / "logs"
DATA_DIR = BACKEND_DIR.parent / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def validate_clean_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Perform comprehensive validation on cleaned data."""
    validation_results = {
        "all_checks_passed": True,
        "checks": {}
    }

    def add_check(name: str, passed: bool, message: str) -> None:
        validation_results["checks"][name] = {
            "passed": passed,
            "message": message
        }
        if not passed:
            validation_results["all_checks_passed"] = False

    logger.info("=" * 60)
    logger.info("Starting Clean Data Validation")
    logger.info("=" * 60)

    # Check 1: No duplicate rows
    duplicates = df.duplicated().sum()
    add_check(
        "No duplicate rows",
        duplicates == 0,
        f"Found {duplicates} duplicate rows" if duplicates > 0 else "No duplicates found"
    )

    # Check 2: Required columns exist
    required_columns = [
        "row_id", "order_id", "order_date", "ship_date", "ship_mode",
        "customer_id", "customer_name", "segment", "country", "city",
        "state", "postal_code", "region", "product_id", "category",
        "sub_category", "product_name", "sales", "quantity", "discount", "profit"
    ]
    missing_cols = [col for col in required_columns if col not in df.columns]
    add_check(
        "Required columns exist",
        len(missing_cols) == 0,
        f"Missing required columns: {', '.join(missing_cols)}" if len(missing_cols) > 0 else "All required columns present"
    )

    # Check 3: Date columns are valid
    date_cols = ["order_date", "ship_date"]
    invalid_dates = []
    for col in date_cols:
        if col in df.columns:
            try:
                pd.to_datetime(df[col])
            except Exception as e:
                invalid_dates.append(col)
    add_check(
        "Date columns are valid",
        len(invalid_dates) == 0,
        f"Invalid date columns: {', '.join(invalid_dates)}" if len(invalid_dates) > 0 else "All date columns valid"
    )

    # Check 4: Numeric columns are valid
    numeric_cols = ["sales", "profit", "quantity", "discount"]
    invalid_numeric = []
    for col in numeric_cols:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            invalid_numeric.append(col)
    add_check(
        "Numeric columns are valid",
        len(invalid_numeric) == 0,
        f"Invalid numeric columns: {', '.join(invalid_numeric)}" if len(invalid_numeric) > 0 else "All numeric columns valid"
    )

    # Check 5: No negative quantities or invalid values
    invalid_quantity = (df["quantity"] < 0).sum() if "quantity" in df.columns else 0
    invalid_discount = (df["discount"] < 0).sum() if "discount" in df.columns else 0
    add_check(
        "No negative quantities or invalid values",
        invalid_quantity == 0 and invalid_discount == 0,
        f"Found {invalid_quantity} negative quantities and {invalid_discount} invalid discounts"
    )

    # Check 6: No missing critical IDs
    critical_cols = ["row_id", "order_id", "customer_id", "product_id"]
    missing_ids = {}
    for col in critical_cols:
        if col in df.columns:
            missing = df[col].isnull().sum()
            if missing > 0:
                missing_ids[col] = missing
    add_check(
        "No missing critical identifiers",
        len(missing_ids) == 0,
        f"Missing IDs: {missing_ids}" if len(missing_ids) > 0 else "No missing critical IDs"
    )

    # Summary
    logger.info("\nValidation Results:")
    for check_name, check_result in validation_results["checks"].items():
        status = "✅ PASS" if check_result["passed"] else "❌ FAIL"
        logger.info(f"{status} {check_name}: {check_result['message']}")

    return validation_results


def main() -> None:
    logger.info("=" * 80)
    logger.info("MetricMind Clean Data Validation Starting")
    logger.info("=" * 80)

    input_path = PROCESSED_DATA_DIR / "clean_sales.csv"
    if not input_path.exists():
        logger.error(f"Clean data file not found: {input_path}")
        return

    try:
        df = pd.read_csv(input_path, encoding="utf-8")
        logger.info(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load clean data: {e}")
        return

    results = validate_clean_data(df)

    logger.info("=" * 80)
    if results["all_checks_passed"]:
        logger.info("All validation passed!")
    else:
        logger.warning("Some validation checks failed!")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
