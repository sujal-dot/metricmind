-- Dimension: DimProduct
CREATE TABLE IF NOT EXISTS dim_product (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(100) NOT NULL,
    product_name VARCHAR(255),
    category VARCHAR(100),
    sub_category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_product_product_id ON dim_product (product_id);
CREATE INDEX IF NOT EXISTS idx_dim_product_category ON dim_product (category);
CREATE INDEX IF NOT EXISTS idx_dim_product_sub_category ON dim_product (sub_category);
