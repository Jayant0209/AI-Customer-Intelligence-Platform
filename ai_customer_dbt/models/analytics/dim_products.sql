SELECT
    PRODUCT_ID,
    PRODUCT_NAME,
    CATEGORY,
    SUBCATEGORY,
    BRAND,
    PRICE,
    COST
FROM {{ ref('stg_products') }}