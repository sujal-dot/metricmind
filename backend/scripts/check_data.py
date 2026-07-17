import pandas as pd

# Load cleaned dataset
df = pd.read_csv("../data/processed/clean_sales.csv")

print("=" * 50)
print("1. Duplicate Rows")
print(df.duplicated().sum())

print("=" * 50)
print("2. Missing Values")
print(df.isnull().sum())

print("=" * 50)
print("3. Order Date")
print(df["order_date"].head())

print("=" * 50)
print("4. Data Types")
print(df.dtypes)

print("=" * 50)
print("5. Customer ID Missing")
print(df["customer_id"].isnull().sum())

print("=" * 50)
print("6. Product ID Missing")
print(df["product_id"].isnull().sum())