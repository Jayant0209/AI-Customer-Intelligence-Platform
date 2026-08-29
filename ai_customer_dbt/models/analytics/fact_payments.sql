SELECT
    PAYMENT_ID,
    ORDER_ID,
    PAYMENT_DATE,
    PAYMENT_METHOD,
    PAYMENT_STATUS,
    AMOUNT
FROM {{ ref('stg_payments') }}