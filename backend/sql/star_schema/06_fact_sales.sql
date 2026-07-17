-- Fact: FactSales
CREATE TABLE IF NOT EXISTS fact_sales (
    sales_key SERIAL PRIMARY KEY,
    order_id VARCHAR(100) NOT NULL,
    customer_key INT,
    product_key INT,
    date_key INT,
    region_key INT,
    employee_key INT,
    sales_amount NUMERIC(18, 4) NOT NULL,
    quantity INT NOT NULL,
    discount NUMERIC(10, 4),
    profit_amount NUMERIC(18, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_customer FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    CONSTRAINT fk_product FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    CONSTRAINT fk_date FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    CONSTRAINT fk_region FOREIGN KEY (region_key) REFERENCES dim_region(region_key),
    CONSTRAINT fk_employee FOREIGN KEY (employee_key) REFERENCES dim_employee(employee_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON fact_sales (customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product ON fact_sales (product_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_region ON fact_sales (region_key);
