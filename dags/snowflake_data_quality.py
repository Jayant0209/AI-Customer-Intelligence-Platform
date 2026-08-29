from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from datetime import datetime


SNOWFLAKE_CONN_ID = "snowflake_default"


def validate_snowflake_data():

    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID
    )

    print("========================================")
    print("SNOWFLAKE DATA QUALITY VALIDATION")
    print("========================================")


    # ========================================================
    # 1. ROW COUNT VALIDATION
    # ========================================================

    expected_counts = {
        "CUSTOMERS": 10000,
        "PRODUCTS": 1000,
        "ORDERS": 100000,
        "PAYMENTS": 100000,
    }

    count_sql = """
    SELECT 'CUSTOMERS' AS TABLE_NAME, COUNT(*) AS ROW_COUNT
    FROM AI_CUSTOMER_DB.RAW.CUSTOMERS

    UNION ALL

    SELECT 'PRODUCTS', COUNT(*)
    FROM AI_CUSTOMER_DB.RAW.PRODUCTS

    UNION ALL

    SELECT 'ORDERS', COUNT(*)
    FROM AI_CUSTOMER_DB.RAW.ORDERS

    UNION ALL

    SELECT 'PAYMENTS', COUNT(*)
    FROM AI_CUSTOMER_DB.RAW.PAYMENTS;
    """

    count_results = hook.get_records(count_sql)

    for table_name, row_count in count_results:

        expected = expected_counts[table_name]

        print(
            f"{table_name}: "
            f"actual={row_count}, expected={expected}"
        )

        if row_count != expected:
            raise ValueError(
                f"ROW COUNT FAILED for {table_name}. "
                f"Expected {expected}, found {row_count}."
            )

    print("Row count validation: PASS")


    # ========================================================
    # 2. CUSTOMERS VALIDATION
    # ========================================================

    customers_sql = """
    SELECT
        COUNT_IF(CUSTOMER_ID IS NULL) AS NULL_IDS,
        COUNT(*) - COUNT(DISTINCT CUSTOMER_ID) AS DUPLICATE_IDS
    FROM AI_CUSTOMER_DB.RAW.CUSTOMERS;
    """

    customers_result = hook.get_first(customers_sql)

    null_ids = customers_result[0]
    duplicate_ids = customers_result[1]

    print(
        f"CUSTOMERS -> "
        f"NULL IDs={null_ids}, "
        f"DUPLICATE IDs={duplicate_ids}"
    )

    if null_ids > 0:
        raise ValueError("CUSTOMERS validation failed: NULL CUSTOMER_ID found.")

    if duplicate_ids > 0:
        raise ValueError("CUSTOMERS validation failed: duplicate CUSTOMER_ID found.")

    print("CUSTOMERS validation: PASS")


    # ========================================================
    # 3. PRODUCTS VALIDATION
    # ========================================================

    products_sql = """
    SELECT
        COUNT_IF(PRODUCT_ID IS NULL) AS NULL_IDS,
        COUNT(*) - COUNT(DISTINCT PRODUCT_ID) AS DUPLICATE_IDS,
        COUNT_IF(PRICE < 0) AS NEGATIVE_PRICES,
        COUNT_IF(COST < 0) AS NEGATIVE_COSTS
    FROM AI_CUSTOMER_DB.RAW.PRODUCTS;
    """

    products_result = hook.get_first(products_sql)

    null_ids = products_result[0]
    duplicate_ids = products_result[1]
    negative_prices = products_result[2]
    negative_costs = products_result[3]

    print(
        f"PRODUCTS -> "
        f"NULL IDs={null_ids}, "
        f"DUPLICATE IDs={duplicate_ids}, "
        f"NEGATIVE PRICES={negative_prices}, "
        f"NEGATIVE COSTS={negative_costs}"
    )

    if null_ids > 0:
        raise ValueError("PRODUCTS validation failed: NULL PRODUCT_ID found.")

    if duplicate_ids > 0:
        raise ValueError("PRODUCTS validation failed: duplicate PRODUCT_ID found.")

    if negative_prices > 0:
        raise ValueError("PRODUCTS validation failed: negative PRICE found.")

    if negative_costs > 0:
        raise ValueError("PRODUCTS validation failed: negative COST found.")

    print("PRODUCTS validation: PASS")


    # ========================================================
    # 4. ORDERS VALIDATION
    # ========================================================

    orders_sql = """
    SELECT
        COUNT_IF(ORDER_ID IS NULL) AS NULL_ORDER_IDS,
        COUNT(*) - COUNT(DISTINCT ORDER_ID) AS DUPLICATE_ORDER_IDS,
        COUNT_IF(QUANTITY <= 0) AS INVALID_QUANTITY,
        COUNT_IF(TOTAL_AMOUNT < 0) AS NEGATIVE_TOTAL_AMOUNT
    FROM AI_CUSTOMER_DB.RAW.ORDERS;
    """

    orders_result = hook.get_first(orders_sql)

    null_order_ids = orders_result[0]
    duplicate_order_ids = orders_result[1]
    invalid_quantity = orders_result[2]
    negative_total_amount = orders_result[3]

    print(
        f"ORDERS -> "
        f"NULL IDs={null_order_ids}, "
        f"DUPLICATE IDs={duplicate_order_ids}, "
        f"INVALID QUANTITY={invalid_quantity}, "
        f"NEGATIVE TOTAL={negative_total_amount}"
    )

    if null_order_ids > 0:
        raise ValueError("ORDERS validation failed: NULL ORDER_ID found.")

    if duplicate_order_ids > 0:
        raise ValueError("ORDERS validation failed: duplicate ORDER_ID found.")

    if invalid_quantity > 0:
        raise ValueError("ORDERS validation failed: invalid QUANTITY found.")

    if negative_total_amount > 0:
        raise ValueError("ORDERS validation failed: negative TOTAL_AMOUNT found.")

    print("ORDERS validation: PASS")


    # ========================================================
    # 5. ORDERS → CUSTOMERS REFERENTIAL INTEGRITY
    # ========================================================

    order_customer_sql = """
    SELECT COUNT(*)
    FROM AI_CUSTOMER_DB.RAW.ORDERS o
    LEFT JOIN AI_CUSTOMER_DB.RAW.CUSTOMERS c
        ON o.CUSTOMER_ID = c.CUSTOMER_ID
    WHERE c.CUSTOMER_ID IS NULL;
    """

    missing_customers = hook.get_first(order_customer_sql)[0]

    print(
        f"ORDERS → CUSTOMERS missing references: "
        f"{missing_customers}"
    )

    if missing_customers > 0:
        raise ValueError(
            "Referential integrity failed: "
            "ORDERS contains CUSTOMER_ID values "
            "not found in CUSTOMERS."
        )

    print("ORDERS → CUSTOMERS validation: PASS")


    # ========================================================
    # 6. ORDERS → PRODUCTS REFERENTIAL INTEGRITY
    # ========================================================

    order_product_sql = """
    SELECT COUNT(*)
    FROM AI_CUSTOMER_DB.RAW.ORDERS o
    LEFT JOIN AI_CUSTOMER_DB.RAW.PRODUCTS p
        ON o.PRODUCT_ID = p.PRODUCT_ID
    WHERE p.PRODUCT_ID IS NULL;
    """

    missing_products = hook.get_first(order_product_sql)[0]

    print(
        f"ORDERS → PRODUCTS missing references: "
        f"{missing_products}"
    )

    if missing_products > 0:
        raise ValueError(
            "Referential integrity failed: "
            "ORDERS contains PRODUCT_ID values "
            "not found in PRODUCTS."
        )

    print("ORDERS → PRODUCTS validation: PASS")


    # ========================================================
    # 7. PAYMENTS VALIDATION
    # ========================================================

    payments_sql = """
    SELECT
        COUNT_IF(PAYMENT_ID IS NULL) AS NULL_PAYMENT_IDS,
        COUNT(*) - COUNT(DISTINCT PAYMENT_ID) AS DUPLICATE_PAYMENT_IDS,
        COUNT_IF(PAYMENT_AMOUNT < 0) AS NEGATIVE_PAYMENT_AMOUNT,
        COUNT_IF(
              PAYMENT_STATUS NOT IN ('SUCCESS', 'FAILED', 'PENDING', 'REFUNDED')
              ) AS INVALID_STATUS    FROM AI_CUSTOMER_DB.RAW.PAYMENTS;"""

    payments_result = hook.get_first(payments_sql)

    null_payment_ids = payments_result[0]
    duplicate_payment_ids = payments_result[1]
    negative_payment_amount = payments_result[2]
    invalid_status = payments_result[3]

    print(
        f"PAYMENTS -> "
        f"NULL IDs={null_payment_ids}, "
        f"DUPLICATE IDs={duplicate_payment_ids}, "
        f"NEGATIVE AMOUNT={negative_payment_amount}, "
        f"INVALID STATUS={invalid_status}"
    )

    if null_payment_ids > 0:
        raise ValueError(
            "PAYMENTS validation failed: NULL PAYMENT_ID found."
        )

    if duplicate_payment_ids > 0:
        raise ValueError(
            "PAYMENTS validation failed: duplicate PAYMENT_ID found."
        )

    if negative_payment_amount > 0:
        raise ValueError(
            "PAYMENTS validation failed: negative PAYMENT_AMOUNT found."
        )

    if invalid_status > 0:
        raise ValueError(
            "PAYMENTS validation failed: invalid PAYMENT_STATUS found."
        )

    print("PAYMENTS validation: PASS")


    # ========================================================
    # 8. PAYMENTS → ORDERS REFERENTIAL INTEGRITY
    # ========================================================

    payment_order_sql = """
    SELECT COUNT(*)
    FROM AI_CUSTOMER_DB.RAW.PAYMENTS p
    LEFT JOIN AI_CUSTOMER_DB.RAW.ORDERS o
        ON p.ORDER_ID = o.ORDER_ID
    WHERE o.ORDER_ID IS NULL;
    """

    missing_orders = hook.get_first(payment_order_sql)[0]

    print(
        f"PAYMENTS → ORDERS missing references: "
        f"{missing_orders}"
    )

    if missing_orders > 0:
        raise ValueError(
            "Referential integrity failed: "
            "PAYMENTS contains ORDER_ID values "
            "not found in ORDERS."
        )

    print("PAYMENTS → ORDERS validation: PASS")


    # ========================================================
    # FINAL RESULT
    # ========================================================

    print("========================================")
    print("ALL DATA QUALITY CHECKS PASSED")
    print("========================================")


# ============================================================
# DAG
# ============================================================

with DAG(
    dag_id="snowflake_data_quality",
    start_date=datetime(2026, 8, 24),
    schedule=None,
    catchup=False,
    tags=[
        "snowflake",
        "data_quality",
        "ai_customer_intelligence",
    ],
) as dag:

    validate_data_task = PythonOperator(
        task_id="validate_snowflake_data",
        python_callable=validate_snowflake_data,
    )
