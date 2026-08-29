SELECT
    PRODUCT_ID,
    PRODUCT_NAME,
    CATEGORY,
    SUBCATEGORY,
    BRAND,
    PRICE,
    COST
FROM {{ source('staging', 'PRODUCTS_STG') }}