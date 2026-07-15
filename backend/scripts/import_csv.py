#!/usr/bin/env python3
"""
MetricMind CSV Import Script for Superstore Dataset
Normalizes and imports all.csv into PostgreSQL data warehouse
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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

def get_engine() -> Engine:
    """Create and return SQLAlchemy engine."""
    return create_engine(DATABASE_URL)

def create_schema(engine: Engine) -> None:
    """Create database schema from SQL file."""
    schema_path = Path(__file__).parent.parent / "sql" / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    with engine.connect() as conn:
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        conn.commit()
    logger.info("Database schema created successfully")

def check_imported(engine: Engine, file_name: str) -> bool:
    """Check if file has already been imported successfully."""
    query = text("""
        SELECT 1 FROM import_logs 
        WHERE file_name = :file_name AND status = 'success'
        LIMIT 1
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"file_name": file_name})
        return result.fetchone() is not None

def log_import(engine: Engine, file_name: str, rows_imported: int, status: str, notes: str = "") -> None:
    """Log import to import_logs table."""
    query = text("""
        INSERT INTO import_logs (file_name, imported_at, rows_imported, status, notes)
        VALUES (:file_name, CURRENT_TIMESTAMP, :rows_imported, :status, :notes)
    """)
    with engine.connect() as conn:
        conn.execute(query, {
            "file_name": file_name,
            "rows_imported": rows_imported,
            "status": status,
            "notes": notes
        })
        conn.commit()

def normalize_and_import(file_path: Path, engine: Engine) -> None:
    """Normalize and import the Superstore dataset."""
    file_name = file_path.name
    logger.info(f"Processing Superstore dataset: {file_name}")
    
    if check_imported(engine, file_name):
        logger.info(f"File already imported: {file_name}, skipping")
        return
    
    # Load the CSV
    df = pd.read_csv(file_path, encoding="latin-1")
    logger.info(f"Read {len(df)} rows from {file_name}")
    
    # Step 1: Prepare and import customers
    logger.info("Importing customers...")
    customers_df = df[["Customer ID", "Customer Name", "Segment", "Country", "City", "State", "Postal Code", "Region"]].drop_duplicates()
    customers_df.columns = [
        "customer_id", "customer_name", "segment", "country", "city", "state", "postal_code", "region"
    ]
    customers_df.to_sql("customers", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(customers_df)} customers")
    
    # Step 2: Prepare and import products
    logger.info("Importing products...")
    products_df = df[["Product ID", "Product Name", "Category", "Sub-Category"]].drop_duplicates()
    products_df.columns = ["product_id", "product_name", "category", "sub_category"]
    products_df.to_sql("products", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(products_df)} products")
    
    # Step 3: Prepare and import orders (distinct order IDs)
    logger.info("Importing orders...")
    orders_df = df[["Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID"]].drop_duplicates(subset=["Order ID"])
    orders_df["Order Date"] = pd.to_datetime(orders_df["Order Date"], format="%m/%d/%Y").dt.date
    orders_df["Ship Date"] = pd.to_datetime(orders_df["Ship Date"], format="%m/%d/%Y").dt.date
    orders_df.columns = [
        "order_id", "order_date", "ship_date", "ship_mode", "customer_id"
    ]
    orders_df.to_sql("orders", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(orders_df)} orders")
    
    # Step 4: Prepare and import order details
    logger.info("Importing order details...")
    order_details_df = df[["Row ID", "Order ID", "Product ID", "Sales", "Quantity", "Discount", "Profit"]]
    order_details_df.columns = [
        "row_id", "order_id", "product_id", "sales", "quantity", "discount", "profit"
    ]
    order_details_df.to_sql("order_details", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(order_details_df)} order details")
    
    # Log success
    log_import(engine, file_name, len(df), "success", "Full Superstore dataset imported and normalized")
    logger.info("All data imported successfully!")

def main() -> None:
    logger.info("=" * 60)
    logger.info("MetricMind Superstore Import Pipeline Starting")
    logger.info("=" * 60)
    
    engine = get_engine()
    raw_data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    
    create_schema(engine)
    
    # Find all.csv
    all_csv_path = raw_data_dir / "all.csv"
    
    if not all_csv_path.exists():
        logger.error("all.csv not found in data/raw directory!")
        return
    
    normalize_and_import(all_csv_path, engine)
    
    logger.info("=" * 60)
    logger.info("Import Complete")
    logger.info("=" * 60)
    logger.info(f"Log file: {LOG_FILE}")

if __name__ == "__main__":
    main()
