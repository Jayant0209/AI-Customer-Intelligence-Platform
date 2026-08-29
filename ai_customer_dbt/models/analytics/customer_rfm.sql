SELECT
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    EMAIL,
    CITY,
    STATE,
    CUSTOMER_SEGMENT,

    DATEDIFF(
        'day',
        LAST_ORDER_DATE,
        (SELECT MAX(LAST_ORDER_DATE)
         FROM {{ ref('customer_metrics') }})
    ) AS RECENCY_DAYS,

    TOTAL_ORDERS AS FREQUENCY,

    TOTAL_REVENUE AS MONETARY_VALUE,

    FIRST_ORDER_DATE,
    LAST_ORDER_DATE

FROM {{ ref('customer_metrics') }}
