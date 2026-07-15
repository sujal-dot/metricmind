-- MetricMind Data Warehouse Schema
-- Normalized star schema for Superstore sales dataset

-- Customers dimension: One row per customer
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    segment VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    region VARCHAR(100) NOT NULL
);

-- Products dimension: One row per product
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100) NOT NULL
);

-- Orders fact table: One row per order
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    order_date DATE NOT NULL,
    ship_date DATE,
    ship_mode VARCHAR(100),
    customer_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Order details fact table: One row per order line item
CREATE TABLE IF NOT EXISTS order_details (
    row_id INT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    sales NUMERIC(12,4) NOT NULL,
    quantity INT NOT NULL,
    discount NUMERIC(5,4) NOT NULL,
    profit NUMERIC(12,4) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Import log table to track imports
CREATE TABLE IF NOT EXISTS import_logs (
    import_id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rows_imported INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_details_order_id ON order_details(order_id);
CREATE INDEX IF NOT EXISTS idx_order_details_product_id ON order_details(product_id);
