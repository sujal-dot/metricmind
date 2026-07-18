
{{ config(materialized='table') }}

SELECT
    region,
    state,
    city,
    country,
    SUM(quantity) AS total_quantity,
    SUM(sales_amount) AS total_sales,
    SUM(profit_amount) AS total_profit
FROM {{ ref('int_sales') }}
GROUP BY region, state, city, country
