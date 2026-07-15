#!/usr/bin/env python3
"""
MetricMind Data Validation Script for Superstore Dataset
Validates imported data and checks referential integrity
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"validate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://metricmind:metricmind@localhost:5432/metricmind")

# List of all tables in our schema
ALL_TABLES = [
    "regions", "states", "cities", "segments",
    "categories", "subcategories", "products",
    "ship_modes", "customers", "orders", "order_details"
]

# Define foreign key relationships for validation
FOREIGN_KEYS = {
    "states": [("region_id", "regions", "region_id")],
    "cities": [("state_id", "states", "state_id")],
    "customers": [("segment_id", "segments", "segment_id"), ("city_id", "cities", "city_id")],
    "subcategories": [("category_id", "categories", "category_id")],
    "products": [("subcategory_id", "subcategories", "subcategory_id")],
    "orders": [("ship_mode_id", "ship_modes", "ship_mode_id"), ("customer_id", "customers", "customer_id")],
    "order_details": [("order_id", "orders", "order_id"), ("product_id", "products", "product_id")]
}

def get_engine() -> Engine:
    return create_engine(DATABASE_URL)

def count_db_rows(engine: Engine, table_name: str) -> int:
    """Count rows in database table."""
    try:
        query = text(f"SELECT COUNT(*) FROM {table_name}")
        with engine.connect() as conn:
            result = conn.execute(query)
            return result.scalar()
    except Exception as e:
        logger.error(f"Failed to count rows in {table_name}: {e}")
        return -1

def check_duplicates(engine: Engine, table_name: str, primary_keys: List[str]) -> int:
    """Check for duplicate primary keys in table."""
    if not primary_keys:
        return 0
    pk_str = ", ".join(primary_keys)
    query = text(f"""
        SELECT COUNT(*) FROM (
            SELECT {pk_str} FROM {table_name}
            GROUP BY {pk_str}
            HAVING COUNT(*) > 1
        ) AS duplicates
    """)
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            return result.scalar()
    except Exception as e:
        logger.error(f"Failed to check duplicates in {table_name}: {e}")
        return -1

def check_foreign_keys(engine: Engine, table_name: str) -> Dict[str, int]:
    """Check for missing foreign keys in table."""
    fk_issues = {}
    if table_name not in FOREIGN_KEYS:
        return fk_issues
    for fk_col, ref_table, ref_col in FOREIGN_KEYS[table_name]:
        query = text(f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE {fk_col} IS NOT NULL
            AND {fk_col} NOT IN (SELECT {ref_col} FROM {ref_table})
        """)
        try:
            with engine.connect() as conn:
                result = conn.execute(query)
                count = result.scalar()
                if count > 0:
                    fk_issues[f"{fk_col} -> {ref_table}.{ref_col}"] = count
        except Exception as e:
            logger.error(f"Failed to check FK {fk_col} in {table_name}: {e}")
            fk_issues[f"{fk_col} -> {ref_table}.{ref_col}"] = -1
    return fk_issues

def main() -> None:
    logger.info("=" * 60)
    logger.info("MetricMind Superstore Data Validation Starting")
    logger.info("=" * 60)
    
    engine = get_engine()
    
    validation_results = {
        "row_counts": {},
        "duplicates": {},
        "foreign_keys": {}
    }
    
    # 1. Count rows per table in DB
    logger.info("\n--- Database Row Counts ---")
    for table in ALL_TABLES:
        count = count_db_rows(engine, table)
        validation_results["row_counts"][table] = count
        logger.info(f"{table}: {count} rows")
    
    # 2. Check duplicates
    logger.info("\n--- Duplicate Check ---")
    primary_keys = {
        "regions": ["region_id"],
        "states": ["state_id"],
        "cities": ["city_id"],
        "segments": ["segment_id"],
        "categories": ["category_id"],
        "subcategories": ["subcategory_id"],
        "products": ["product_id"],
        "ship_modes": ["ship_mode_id"],
        "customers": ["customer_id"],
        "orders": ["row_id"],
        "order_details": ["row_id"]
    }
    for table in ALL_TABLES:
        pks = primary_keys.get(table, [])
        dup_count = check_duplicates(engine, table, pks)
        validation_results["duplicates"][table] = dup_count
        if dup_count > 0:
            logger.warning(f"{table}: {dup_count} duplicate record(s) found")
        elif dup_count == 0:
            logger.info(f"{table}: No duplicates found")
    
    # 3. Check foreign keys
    logger.info("\n--- Foreign Key Validation ---")
    for table in ALL_TABLES:
        issues = check_foreign_keys(engine, table)
        validation_results["foreign_keys"][table] = issues
        if issues:
            for fk, count in issues.items():
                if count > 0:
                    logger.warning(f"{table}: {count} invalid {fk} reference(s)")
        else:
            logger.info(f"{table}: All foreign keys valid")
    
    # 4. Summary
    logger.info("\n" + "=" * 60)
    logger.info("Validation Summary")
    logger.info("=" * 60)
    total_duplicates = sum(v for v in validation_results["duplicates"].values() if v > 0)
    logger.info(f"Total duplicate records: {total_duplicates}")
    total_fk_issues = sum(sum(v for v in table_issues.values() if v > 0) for table_issues in validation_results["foreign_keys"].values())
    logger.info(f"Total foreign key issues: {total_fk_issues}")
    logger.info("=" * 60)
    logger.info(f"Log file: {LOG_FILE}")

if __name__ == "__main__":
    main()
