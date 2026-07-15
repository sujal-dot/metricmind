-- MetricMind Data Warehouse Schema
-- Normalized schema for Superstore sales data

-- Regions table (contains regions like South, West, etc.)
CREATE TABLE IF NOT EXISTS regions (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_regions_region_name ON regions(region_name);

-- States/Provinces table
CREATE TABLE IF NOT EXISTS states (
    state_id SERIAL PRIMARY KEY,
    state_name VARCHAR(100) NOT NULL,
    region_id INT NOT NULL,
    FOREIGN KEY (region_id) REFERENCES regions(region_id),
    UNIQUE(state_name, region_id)
);

CREATE INDEX IF NOT EXISTS idx_states_region_id ON states(region_id);
CREATE INDEX IF NOT EXISTS idx_states_state_name ON states(state_name);

-- Cities table
CREATE TABLE IF NOT EXISTS cities (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    state_id INT NOT NULL,
    postal_code VARCHAR(20),
    FOREIGN KEY (state_id) REFERENCES states(state_id),
    UNIQUE(city_name, state_id, postal_code)
);

CREATE INDEX IF NOT EXISTS idx_cities_state_id ON cities(state_id);
CREATE INDEX IF NOT EXISTS idx_cities_postal_code ON cities(postal_code);

-- Customer Segments table
CREATE TABLE IF NOT EXISTS segments (
    segment_id SERIAL PRIMARY KEY,
    segment_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_segments_segment_name ON segments(segment_name);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    segment_id INT NOT NULL,
    city_id INT,
    FOREIGN KEY (segment_id) REFERENCES segments(segment_id),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
);

CREATE INDEX IF NOT EXISTS idx_customers_segment_id ON customers(segment_id);
CREATE INDEX IF NOT EXISTS idx_customers_city_id ON customers(city_id);
CREATE INDEX IF NOT EXISTS idx_customers_customer_name ON customers(customer_name);

-- Product Categories table
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_categories_category_name ON categories(category_name);

-- Product Sub-Categories table
CREATE TABLE IF NOT EXISTS subcategories (
    subcategory_id SERIAL PRIMARY KEY,
    subcategory_name VARCHAR(100) NOT NULL,
    category_id INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    UNIQUE(subcategory_name, category_id)
);

CREATE INDEX IF NOT EXISTS idx_subcategories_category_id ON subcategories(category_id);
CREATE INDEX IF NOT EXISTS idx_subcategories_subcategory_name ON subcategories(subcategory_name);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    subcategory_id INT NOT NULL,
    FOREIGN KEY (subcategory_id) REFERENCES subcategories(subcategory_id)
);

CREATE INDEX IF NOT EXISTS idx_products_subcategory_id ON products(subcategory_id);
CREATE INDEX IF NOT EXISTS idx_products_product_name ON products(product_name);

-- Ship Modes table
CREATE TABLE IF NOT EXISTS ship_modes (
    ship_mode_id SERIAL PRIMARY KEY,
    ship_mode_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_ship_modes_name ON ship_modes(ship_mode_name);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    row_id INT PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    order_date DATE NOT NULL,
    ship_date DATE,
    ship_mode_id INT,
    customer_id VARCHAR(20) NOT NULL,
    FOREIGN KEY (ship_mode_id) REFERENCES ship_modes(ship_mode_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);

-- Order Details (sales line items)
CREATE TABLE IF NOT EXISTS order_details (
    row_id INT PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    sales NUMERIC(12,4) NOT NULL,
    quantity INT NOT NULL,
    discount NUMERIC(5,4) NOT NULL,
    profit NUMERIC(12,4) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX IF NOT EXISTS idx_order_details_order_id ON order_details(order_id);
CREATE INDEX IF NOT EXISTS idx_order_details_product_id ON order_details(product_id);

-- Import log table to track imports
CREATE TABLE IF NOT EXISTS import_logs (
    import_id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rows_imported INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_import_logs_file_name ON import_logs(file_name);
CREATE INDEX IF NOT EXISTS idx_import_logs_table_name ON import_logs(table_name);
