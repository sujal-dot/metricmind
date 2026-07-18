
{{ config(materialized='view') }}

SELECT
    employee_key,
    employee_id,
    employee_name,
    department
FROM {{ source('metricmind', 'dim_employee') }}
