#!/usr/bin/env python3
"""
MetricMind Star Schema Builder
Populates the Kimball-style star schema optimized for BI and OLAP queries.
"""
import os
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"star_schema_build_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://metricmind:metricmind@localhost:5433/metricmind")


def get_engine() -> "Engine":
    return create_engine(DATABASE_URL)


def generate_date_dimension(dates: list[datetime.date]) -> pd.DataFrame:
    data = []
    for dt in dates:
        dt_obj = pd.Timestamp(dt)
        date_key = int(dt_obj.strftime("%Y%m%d"))
        data.append({
            "date_key": date_key,
            "full_date": dt_obj.date(),
            "day_of_month": dt_obj.day,
            "month": dt_obj.month,
            "month_name": dt_obj.month_name(),
            "year": dt_obj.year,
            "quarter": f"Q{((dt_obj.month -1)//3)+1}",
            "day_of_week": dt_obj.dayofweek +1,
            "week_number": dt_obj.isocalendar()[1],
            "is_weekend": dt_obj.dayofweek >=5
        })
    return pd.DataFrame(data)


def get_or_create_dimension(engine, df_input: pd.DataFrame, table_name: str, id_cols: list[str]) -> pd.DataFrame:
    existing = pd.read_sql(f"SELECT * FROM {table_name}", engine)
    if len(existing) >0:
        merged = df_input.merge(existing[id_cols], on=id_cols, how="left", indicator=True)
        new_rows = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])
    else:
        new_rows = df_input.copy()
        
    if len(new_rows) >0:
        logger.info(f"Inserting {len(new_rows)} new rows into {table_name}")
        new_rows.to_sql(table_name, engine, if_exists="append", index=False, chunksize=100)
        
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)


def build_star_schema():
    logger.info("=" * 80)
    logger.info("Starting Star Schema Build Process")
    logger.info("=" * 80)
    
    engine = get_engine()
    
    # Create tables
    sql_dir = Path(__file__).parent.parent / "sql" / "star_schema"
    for sql_file in sorted(sql_dir.glob("*.sql")):
        logger.info(f"Executing {sql_file.name}")
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
        with engine.connect() as conn:
            for stmt in sql_content.split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()
    
    # Load cleaned data
    data_path = Path(__file__).parent.parent.parent / "data" / "processed" / "clean_sales.csv"
    df = pd.read_csv(data_path, encoding="utf-8")
    df["order_date"] = pd.to_datetime(df["order_date"])
    logger.info(f"Loaded cleaned sales data with {len(df)} rows")
    
    # 1. DimDate
    unique_dates = df["order_date"].dt.date.unique()
    date_dim = generate_date_dimension(unique_dates)
    existing_dates = pd.read_sql("SELECT date_key FROM dim_date", engine)
    new_dates = date_dim[~date_dim["date_key"].isin(existing_dates["date_key"])]
    if len(new_dates) >0:
        new_dates.to_sql("dim_date", engine, if_exists="append", index=False, chunksize=100)
    date_dim = pd.read_sql("SELECT * FROM dim_date", engine)
    date_dim["full_date"] = pd.to_datetime(date_dim["full_date"]).dt.date
    
    # 2. DimCustomer
    customer_df = df[["customer_id", "customer_name", "segment"]].drop_duplicates(subset=["customer_id"])
    customer_dim = get_or_create_dimension(engine, customer_df, "dim_customer", ["customer_id"])
    
    # 3. DimProduct
    product_df = df[["product_id", "product_name", "category", "sub_category"]].drop_duplicates(subset=["product_id"])
    product_dim = get_or_create_dimension(engine, product_df, "dim_product", ["product_id"])
    
    #4. DimRegion
    region_df = df[["country", "state", "city", "region"]].drop_duplicates()
    region_dim = get_or_create_dimension(engine, region_df, "dim_region", ["country", "state", "city", "region"])
    
    # 5. FactSales
    df["full_date"] = df["order_date"].dt.date
    df = df.merge(date_dim[["date_key", "full_date"]], on="full_date", how="left")
    df = df.merge(customer_dim[["customer_id", "customer_key"]], on="customer_id", how="left")
    df = df.merge(product_dim[["product_id", "product_key"]], on="product_id", how="left")
    df = df.merge(region_dim[["country", "state", "city", "region", "region_key"]], on=["country", "state", "city", "region"], how="left")
    
    fact_df = df[["order_id", "customer_key", "product_key", "date_key", "region_key",
                   "sales", "quantity", "discount", "profit"]].rename(
        columns={"sales": "sales_amount", "profit": "profit_amount"})
    fact_df["employee_key"] = None
    
    existing_facts = pd.read_sql("SELECT DISTINCT order_id FROM fact_sales", engine)
    new_facts = fact_df[~fact_df["order_id"].isin(existing_facts["order_id"])]
    if len(new_facts) >0:
        new_facts.to_sql("fact_sales", engine, if_exists="append", index=False, chunksize=100)
        logger.info(f"Inserted {len(new_facts)} new fact rows")
    
    logger.info("=" *80)
    logger.info("Star Schema Build Complete!")
    logger.info("=" *80)


if __name__ == "__main__":
    build_star_schema()
