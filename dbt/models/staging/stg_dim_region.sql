
{{ config(materialized='view') }}

SELECT
    region_key,
    country,
    state,
    city,
    region
FROM {{ source('metricmind', 'dim_region') }}
