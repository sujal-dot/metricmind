
{{ config(materialized='view') }}

SELECT
    product_key,
    product_id,
    product_name,
    category,
    sub_category
FROM {{ source('metricmind', 'dim_product') }}
