-- Dimension: DimCustomer
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    segment VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_customer_customer_id ON dim_customer (customer_id);
CREATE INDEX IF NOT EXISTS idx_dim_customer_segment ON dim_customer (segment);
