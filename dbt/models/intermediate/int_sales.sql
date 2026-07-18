
{{ config(materialized='view') }}

SELECT
    fs.sales_key,
    fs.order_id,
    fs.sales_amount,
    fs.quantity,
    fs.discount,
    fs.profit_amount,
    dc.customer_key,
    dc.customer_name,
    dc.segment,
    dp.product_key,
    dp.product_name,
    dp.category,
    dp.sub_category,
    dd.date_key,
    dd.full_date,
    dd.year,
    dd.month,
    dd.month_name,
    dd.quarter,
    dr.region_key,
    dr.region,
    dr.state,
    dr.city,
    dr.country
FROM {{ ref('stg_fact_sales') }} fs
LEFT JOIN {{ ref('stg_dim_customer') }} dc ON fs.customer_key = dc.customer_key
LEFT JOIN {{ ref('stg_dim_product') }} dp ON fs.product_key = dp.product_key
LEFT JOIN {{ ref('stg_dim_date') }} dd ON fs.date_key = dd.date_key
LEFT JOIN {{ ref('stg_dim_region') }} dr ON fs.region_key = dr.region_key
