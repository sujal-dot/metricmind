
{{ config(materialized='view') }}

SELECT
    product_key,
    product_name,
    category,
    sub_category,
    SUM(quantity) AS total_quantity,
    SUM(sales_amount) AS total_sales,
    SUM(profit_amount) AS total_profit
FROM {{ ref('int_sales') }}
GROUP BY product_key, product_name, category, sub_category
