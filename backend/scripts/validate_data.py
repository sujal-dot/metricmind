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
ALL_TABLES = ["customers", "products", "orders", "order_details"]

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

def check_duplicates(engine: Engine, table_name: str, primary_key: str) -> int:
    """Check for duplicate primary keys in table."""
    query = text(f"""
        SELECT COUNT(*) FROM (
            SELECT {primary_key} FROM {table_name}
            GROUP BY {primary_key}
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

def check_foreign_keys(engine: Engine) -> Dict[str, int]:
    """Check for missing foreign keys in tables."""
    fk_issues = {}
    # Check orders.customer_id references customers.customer_id
    query1 = text("""
        SELECT COUNT(*) FROM orders
        WHERE customer_id NOT IN (SELECT customer_id FROM customers)
    """)
    with engine.connect() as conn:
        result = conn.execute(query1)
        count = result.scalar()
        if count > 0:
            fk_issues["orders.customer_id"] = count
    # Check order_details.order_id references orders.order_id
    query2 = text("""
        SELECT COUNT(*) FROM order_details
        WHERE order_id NOT IN (SELECT order_id FROM orders)
    """)
    with engine.connect() as conn:
        result = conn.execute(query2)
        count = result.scalar()
        if count > 0:
            fk_issues["order_details.order_id"] = count
    # Check order_details.product_id references products.product_id
    query3 = text("""
        SELECT COUNT(*) FROM order_details
        WHERE product_id NOT IN (SELECT product_id FROM products)
    """)
    with engine.connect() as conn:
        result = conn.execute(query3)
        count = result.scalar()
        if count > 0:
            fk_issues["order_details.product_id"] = count
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
        "customers": "customer_id",
        "products": "product_id",
        "orders": "order_id",
        "order_details": "row_id"
    }
    for table in ALL_TABLES:
        pk = primary_keys[table]
        dup_count = check_duplicates(engine, table, pk)
        validation_results["duplicates"][table] = dup_count
        if dup_count > 0:
            logger.warning(f"{table}: {dup_count} duplicate {pk} found")
        elif dup_count == 0:
            logger.info(f"{table}: No duplicates found for {pk}")
    
    # 3. Check foreign keys
    logger.info("\n--- Foreign Key Validation ---")
    fk_issues = check_foreign_keys(engine)
    validation_results["foreign_keys"] = fk_issues
    if fk_issues:
        for fk, count in fk_issues.items():
            if count > 0:
                logger.warning(f"{fk}: {count} invalid references found")
    else:
        logger.info("All foreign keys are valid")
    
    # 4. Summary
    logger.info("\n" + "=" * 60)
    logger.info("Validation Summary")
    logger.info("=" * 60)
    total_duplicates = sum(v for v in validation_results["duplicates"].values() if v > 0)
    total_fk_issues = sum(validation_results["foreign_keys"].values()) if validation_results["foreign_keys"] else 0
    logger.info(f"Total duplicates: {total_duplicates}")
    logger.info(f"Total foreign key issues: {total_fk_issues}")
    if total_duplicates == 0 and total_fk_issues == 0:
        logger.info("✅ All validation checks passed!")
    else:
        logger.warning("❌ Validation failed!")
    
    logger.info("=" * 60)
    logger.info(f"Log file: {LOG_FILE}")

if __name__ == "__main__":
    main()
