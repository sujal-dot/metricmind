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
from sqlalchemy.orm import sessionmaker

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

def snake_case(s: str) -> str:
    """Convert string to snake_case."""
    s = s.strip()
    s = s.replace(" ", "_").replace("-", "_").replace(".", "_")
    s = s.lower()
    while "__" in s:
        s = s.replace("__", "_")
    return s

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

def log_import(engine: Engine, file_name: str, table_name: str, rows_imported: int, status: str, notes: str = "") -> None:
    """Log import to import_logs table."""
    query = text("""
        INSERT INTO import_logs (file_name, table_name, imported_at, rows_imported, status, notes)
        VALUES (:file_name, :table_name, CURRENT_TIMESTAMP, :rows_imported, :status, :notes)
    """)
    with engine.connect() as conn:
        conn.execute(query, {
            "file_name": file_name,
            "table_name": table_name,
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
    
    # Read CSV
    df = pd.read_csv(file_path, encoding="latin-1")
    logger.info(f"Read {len(df)} rows from {file_name}")
    
    # Standardize column names
    df.columns = [snake_case(col) for col in df.columns]
    
    # Clean and parse dates
    df["order_date"] = pd.to_datetime(df["order_date"], format="%m/%d/%Y").dt.date
    df["ship_date"] = pd.to_datetime(df["ship_date"], format="%m/%d/%Y").dt.date
    
    # Trim strings
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace("nan", pd.NA)
    
    # =====================================
    # Step 1: Import lookup tables
    # =====================================
    
    # 1.1 Regions
    regions_df = df[["region"]].drop_duplicates().reset_index(drop=True)
    regions_df.columns = ["region_name"]
    regions_df.to_sql("regions", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(regions_df)} regions")
    
    # Get region_ids
    with engine.connect() as conn:
        result = conn.execute(text("SELECT region_id, region_name FROM regions"))
        region_map = {row[1]: row[0] for row in result}
    
    # 1.2 States
    states_df = df[["state", "region"]].drop_duplicates().reset_index(drop=True)
    states_df.columns = ["state_name", "region_name"]
    states_df["region_id"] = states_df["region_name"].map(region_map)
    states_df = states_df[["state_name", "region_id"]]
    states_df.to_sql("states", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(states_df)} states")
    
    # Get state_ids
    with engine.connect() as conn:
        result = conn.execute(text("SELECT state_id, state_name FROM states"))
        state_map = {row[1]: row[0] for row in result}
    
    # 1.3 Cities
    cities_df = df[["city", "state", "postal_code"]].drop_duplicates().reset_index(drop=True)
    cities_df.columns = ["city_name", "state_name", "postal_code"]
    cities_df["state_id"] = cities_df["state_name"].map(state_map)
    cities_df = cities_df[["city_name", "state_id", "postal_code"]]
    cities_df.to_sql("cities", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(cities_df)} cities")
    
    # Get city_ids (composite key)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT city_id, city_name, state_id, postal_code FROM cities"))
        city_map = {(row[1], row[2], str(row[3])): row[0] for row in result}
    
    # 1.4 Segments
    segments_df = df[["segment"]].drop_duplicates().reset_index(drop=True)
    segments_df.columns = ["segment_name"]
    segments_df.to_sql("segments", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(segments_df)} segments")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT segment_id, segment_name FROM segments"))
        segment_map = {row[1]: row[0] for row in result}
    
    # 1.5 Categories
    categories_df = df[["category"]].drop_duplicates().reset_index(drop=True)
    categories_df.columns = ["category_name"]
    categories_df.to_sql("categories", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(categories_df)} categories")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT category_id, category_name FROM categories"))
        category_map = {row[1]: row[0] for row in result}
    
    # 1.6 Subcategories
    subcategories_df = df[["sub_category", "category"]].drop_duplicates().reset_index(drop=True)
    subcategories_df.columns = ["subcategory_name", "category_name"]
    subcategories_df["category_id"] = subcategories_df["category_name"].map(category_map)
    subcategories_df = subcategories_df[["subcategory_name", "category_id"]]
    subcategories_df.to_sql("subcategories", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(subcategories_df)} subcategories")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT subcategory_id, subcategory_name, category_id FROM subcategories"))
        subcategory_map = {(row[1], row[2]): row[0] for row in result}
    
    # 1.7 Ship Modes
    ship_modes_df = df[["ship_mode"]].drop_duplicates().reset_index(drop=True)
    ship_modes_df.columns = ["ship_mode_name"]
    ship_modes_df.to_sql("ship_modes", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(ship_modes_df)} ship modes")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT ship_mode_id, ship_mode_name FROM ship_modes"))
        ship_mode_map = {row[1]: row[0] for row in result}
    
    # =====================================
    # Step 2: Import main tables
    # =====================================
    
    # 2.1 Products
    products_df = df[["product_id", "product_name", "sub_category", "category"]].drop_duplicates().reset_index(drop=True)
    products_df["category_id"] = products_df["category"].map(category_map)
    products_df["subcategory_id"] = products_df.apply(
        lambda x: subcategory_map[(x["sub_category"], x["category_id"])], 
        axis=1
    )
    products_df = products_df[["product_id", "product_name", "subcategory_id"]]
    products_df.to_sql("products", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(products_df)} products")
    
    # 2.2 Customers
    customers_df = df[["customer_id", "customer_name", "segment", "city", "state", "postal_code"]].drop_duplicates().reset_index(drop=True)
    customers_df["segment_id"] = customers_df["segment"].map(segment_map)
    customers_df["state_id"] = customers_df["state"].map(state_map)
    customers_df["city_id"] = customers_df.apply(
        lambda x: city_map.get((x["city"], x["state_id"], str(x["postal_code"]))),
        axis=1
    )
    customers_df = customers_df[["customer_id", "customer_name", "segment_id", "city_id"]]
    customers_df.to_sql("customers", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(customers_df)} customers")
    
    # 2.3 Orders
    orders_df = df[["row_id", "order_id", "order_date", "ship_date", "ship_mode", "customer_id"]].drop_duplicates().reset_index(drop=True)
    orders_df["ship_mode_id"] = orders_df["ship_mode"].map(ship_mode_map)
    orders_df = orders_df[["row_id", "order_id", "order_date", "ship_date", "ship_mode_id", "customer_id"]]
    orders_df.to_sql("orders", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(orders_df)} orders")
    
    # 2.4 Order Details (sales line items)
    order_details_df = df[["row_id", "order_id", "product_id", "sales", "quantity", "discount", "profit"]]
    order_details_df.to_sql("order_details", engine, if_exists="append", index=False, method="multi")
    logger.info(f"Imported {len(order_details_df)} order details")
    
    # Log success
    log_import(engine, file_name, "all_tables", len(df), "success", "Full Superstore dataset imported and normalized")
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
