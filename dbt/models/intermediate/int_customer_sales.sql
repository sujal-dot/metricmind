
{{ config(materialized='view') }}

SELECT
    customer_key,
    customer_name,
    segment,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS total_quantity,
    SUM(sales_amount) AS total_sales,
    SUM(profit_amount) AS total_profit,
    AVG(sales_amount) AS avg_order_value
FROM {{ ref('int_sales') }}
GROUP BY customer_key, customer_name, segment
