
{{ config(materialized='table') }}

SELECT
    year,
    month,
    month_name,
    SUM(quantity) AS total_quantity,
    SUM(sales_amount) AS total_sales,
    SUM(profit_amount) AS total_profit
FROM {{ ref('int_sales') }}
GROUP BY year, month, month_name
ORDER BY year, month
