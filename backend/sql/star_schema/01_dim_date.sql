-- Dimension: DimDate
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    day_of_month INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    year INT NOT NULL,
    quarter VARCHAR(5) NOT NULL,
    day_of_week INT NOT NULL,
    week_number INT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_date_full_date ON dim_date (full_date);
CREATE INDEX IF NOT EXISTS idx_dim_date_year ON dim_date (year);
CREATE INDEX IF NOT EXISTS idx_dim_date_month ON dim_date (month);
