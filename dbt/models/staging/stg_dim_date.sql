
{{ config(materialized='view') }}

SELECT
    date_key,
    full_date,
    day_of_month,
    month,
    month_name,
    year,
    quarter,
    day_of_week,
    week_number,
    is_weekend
FROM {{ source('metricmind', 'dim_date') }}
