
{{ config(materialized='view') }}

SELECT
    customer_key,
    customer_id,
    customer_name,
    segment
FROM {{ source('metricmind', 'dim_customer') }}
