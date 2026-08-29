SELECT
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    EMAIL,
    GENDER,
    CITY,
    STATE,
    SIGNUP_DATE,
    CUSTOMER_SEGMENT
FROM {{ source('staging', 'CUSTOMERS_STG') }}