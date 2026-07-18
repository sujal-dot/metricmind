
{{ config(materialized='table') }}

SELECT
    COUNT(DISTINCT sales_key) AS total_sales_transactions,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS total_quantity,
    SUM(sales_amount) AS total_sales,
    SUM(profit_amount) AS total_profit,
    AVG(sales_amount) AS avg_order_value
FROM {{ ref('int_sales') }}
