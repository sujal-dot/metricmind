
{{ config(materialized='table') }}

SELECT * FROM {{ ref('int_customer_sales') }}
