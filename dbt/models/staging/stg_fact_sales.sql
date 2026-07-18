
{{ config(materialized='view') }}

SELECT
    sales_key,
    order_id,
    customer_key,
    product_key,
    date_key,
    region_key,
    employee_key,
    sales_amount,
    quantity,
    discount,
    profit_amount
FROM {{ source('metricmind', 'fact_sales') }}
