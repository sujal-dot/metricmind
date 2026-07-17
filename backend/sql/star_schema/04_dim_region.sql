-- Dimension: DimRegion
CREATE TABLE IF NOT EXISTS dim_region (
    region_key SERIAL PRIMARY KEY,
    country VARCHAR(100),
    state VARCHAR(100),
    city VARCHAR(255),
    region VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dim_region_region ON dim_region (region);
CREATE INDEX IF NOT EXISTS idx_dim_region_state ON dim_region (state);
