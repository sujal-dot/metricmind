#!/usr/bin/env python3
"""
Validate the MetricMind Star Schema
Checks tables exist, relationships are valid, and data quality is good.
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"star_schema_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).parent.parent / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://metricmind:metricmind@localhost:5433/metricmind")


def get_engine():
    return create_engine(DATABASE_URL)


def validate_star_schema():
    engine = get_engine()
    results = {
        "all_passed": True,
        "checks": []
    }

    def add_check(name: str, passed: bool, message: str):
        logger.info(f"Check: {name} - {'✅ PASS' if passed else '❌ FAIL'}: {message}")
        results["checks"].append({
            "name": name,
            "passed": passed,
            "message": message
        })
        if not passed:
            results["all_passed"] = False

    logger.info("=" * 80)
    logger.info("Starting Star Schema Validation")
    logger.info("=" * 80)

    # 1. Check all tables exist
    tables_to_check = ["dim_customer", "dim_product", "dim_date", "dim_region",
                       "dim_employee", "fact_sales"]
    with engine.connect() as conn:
        existing_tables = pd.read_sql("""
            SELECT tablename FROM pg_tables WHERE schemaname = 'public'
        """, conn)["tablename"].tolist()

    for tbl in tables_to_check:
        add_check(f"Table {tbl} exists", tbl in existing_tables,
                  f"Table {'found' if tbl in existing_tables else 'missing'}")

    # 2. Check tables have data (dim_employee is allowed to be empty)
    table_row_counts = {}
    with engine.connect() as conn:
        for tbl in tables_to_check:
            if tbl in existing_tables:
                count = pd.read_sql(f"SELECT COUNT(*) AS cnt FROM {tbl}", conn).iloc[0]["cnt"]
                table_row_counts[tbl] = count
                if tbl == "dim_employee":
                    add_check(f"{tbl} exists (can be empty)", True, f"{count} rows found (dim_employee is optional)")
                else:
                    add_check(f"{tbl} has rows", count >0, f"{count} rows found")

    # 3. Check foreign keys in fact table are valid
    if "fact_sales" in existing_tables:
        fk_checks = [
            ("customer_key", "dim_customer", "customer_key"),
            ("product_key", "dim_product", "product_key"),
            ("date_key", "dim_date", "date_key"),
            ("region_key", "dim_region", "region_key"),
            ("employee_key", "dim_employee", "employee_key")
        ]

        for fk_col, dim_tbl, dim_col in fk_checks:
            with engine.connect() as conn:
                invalid = pd.read_sql(f"""
                    SELECT COUNT(*) AS cnt FROM fact_sales
                    WHERE {fk_col} NOT IN (SELECT {dim_col} FROM {dim_tbl})
                      AND {fk_col} IS NOT NULL
                """, conn).iloc[0]["cnt"]
            add_check(f"No invalid {fk_col}", invalid ==0, f"{invalid} invalid values found")

    # 4. Check no duplicate surrogate keys
    for dim_tbl, key_col in [
        ("dim_customer", "customer_key"),
        ("dim_product", "product_key"),
        ("dim_date", "date_key"),
        ("dim_region", "region_key"),
        ("dim_employee", "employee_key")
    ]:
        if dim_tbl in existing_tables:
            with engine.connect() as conn:
                dup_count = pd.read_sql(f"""
                    SELECT COUNT(*) AS cnt FROM (
                        SELECT {key_col} FROM {dim_tbl}
                        GROUP BY {key_col}
                        HAVING COUNT(*) > 1
                    ) AS dups
                """, conn).iloc[0]["cnt"]
            add_check(f"No duplicate {key_col} in {dim_tbl}", dup_count ==0, f"{dup_count} duplicates found")

    logger.info("=" *80)
    if results["all_passed"]:
        logger.info("✅ All Star Schema Validation Checks Passed!")
    else:
        logger.warning("❌ Some Star Schema Validation Checks Failed!")
    logger.info("=" *80)
    return results


if __name__ == "__main__":
    validate_star_schema()
