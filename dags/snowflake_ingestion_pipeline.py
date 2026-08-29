from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from datetime import datetime


SNOWFLAKE_CONN_ID = "snowflake_default"


def load_snowflake_tables():

    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID
    )

    # ---------------------------------------------------------
    # 1. TRUNCATE TARGET TABLES
    # ---------------------------------------------------------

    truncate_sql = """
    TRUNCATE TABLE AI_CUSTOMER_DB.RAW.CUSTOMERS;

    TRUNCATE TABLE AI_CUSTOMER_DB.RAW.PRODUCTS;

    TRUNCATE TABLE AI_CUSTOMER_DB.RAW.ORDERS;

    TRUNCATE TABLE AI_CUSTOMER_DB.RAW.PAYMENTS;
    """

    hook.run(truncate_sql)

    print("Target tables truncated successfully.")


    # ---------------------------------------------------------
    # 2. LOAD CUSTOMERS
    # ---------------------------------------------------------

    customers_sql = """
    INSERT INTO AI_CUSTOMER_DB.RAW.CUSTOMERS
    (
        CUSTOMER_ID,
        FIRST_NAME,
        LAST_NAME,
        EMAIL,
        GENDER,
        CITY,
        STATE,
        SIGNUP_DATE,
        CUSTOMER_SEGMENT
    )
    SELECT
        $1,
        $2,
        $3,
        $4,
        $5,
        $6,
        $7,
        $8,
        $9
    FROM AI_CUSTOMER_DB.RAW.CUSTOMERS_RAW;
    """

    hook.run(customers_sql)

    print("CUSTOMERS loaded successfully.")


    # ---------------------------------------------------------
    # 3. LOAD PRODUCTS
    # ---------------------------------------------------------

    products_sql = """
    INSERT INTO AI_CUSTOMER_DB.RAW.PRODUCTS
    (
        PRODUCT_ID,
        PRODUCT_NAME,
        CATEGORY,
        SUB_CATEGORY,
        BRAND,
        PRICE,
        COST
    )
    SELECT
        $1,
        $2,
        $3,
        $4,
        $5,
        $6,
        $7
    FROM AI_CUSTOMER_DB.RAW.PRODUCTS_RAW;
    """

    hook.run(products_sql)

    print("PRODUCTS loaded successfully.")


    # ---------------------------------------------------------
    # 4. LOAD ORDERS
    # ---------------------------------------------------------

    orders_sql = """
    INSERT INTO AI_CUSTOMER_DB.RAW.ORDERS
    (
        ORDER_ID,
        CUSTOMER_ID,
        PRODUCT_ID,
        ORDER_DATE,
        QUANTITY,
        UNIT_PRICE,
        DISCOUNT,
        TOTAL_AMOUNT,
        ORDER_STATUS,
        REGION
    )
    SELECT
        $1,
        $2,
        $3,
        $4,
        $5,
        $6,
        $7,
        $8,
        $9,
        $10
    FROM AI_CUSTOMER_DB.RAW.ORDERS_RAW;
    """

    hook.run(orders_sql)

    print("ORDERS loaded successfully.")


    # ---------------------------------------------------------
    # 5. LOAD PAYMENTS
    # ---------------------------------------------------------

    payments_sql = """
    INSERT INTO AI_CUSTOMER_DB.RAW.PAYMENTS
    (
        PAYMENT_ID,
        ORDER_ID,
        PAYMENT_DATE,
        PAYMENT_METHOD,
        PAYMENT_STATUS,
        PAYMENT_AMOUNT
    )
    SELECT
        $1,
        $2,
        $3,
        $4,
        $5,
        $6
    FROM AI_CUSTOMER_DB.RAW.PAYMENTS_RAW;
    """

    hook.run(payments_sql)

    print("PAYMENTS loaded successfully.")


    # ---------------------------------------------------------
    # 6. VALIDATE ROW COUNTS
    # ---------------------------------------------------------

    validation_sql = """
    SELECT
        'CUSTOMERS' AS TABLE_NAME,
        COUNT(*) AS ROW_COUNT
    FROM AI_CUSTOMER_DB.RAW.CUSTOMERS

    UNION ALL

    SELECT
        'PRODUCTS',
        COUNT(*)
    FROM AI_CUSTOMER_DB.RAW.PRODUCTS

    UNION ALL

    SELECT
        'ORDERS',
        COUNT(*)
    FROM AI_CUSTOMER_DB.RAW.ORDERS

    UNION ALL

    SELECT
        'PAYMENTS',
        COUNT(*)
    FROM AI_CUSTOMER_DB.RAW.PAYMENTS;
    """

    results = hook.get_records(validation_sql)

    print("========================================")
    print("SNOWFLAKE INGESTION VALIDATION")
    print("========================================")

    expected_counts = {
        "CUSTOMERS": 10000,
        "PRODUCTS": 1000,
        "ORDERS": 100000,
        "PAYMENTS": 100000,
    }

    for table_name, row_count in results:

        print(f"{table_name}: {row_count}")

        expected = expected_counts[table_name]

        if row_count != expected:
            raise ValueError(
                f"{table_name} validation failed. "
                f"Expected {expected} rows but found {row_count} rows."
            )

    print("========================================")
    print("ALL TABLES LOADED AND VALIDATED")
    print("========================================")


# -------------------------------------------------------------
# DAG DEFINITION
# -------------------------------------------------------------

with DAG(
    dag_id="snowflake_ingestion_pipeline",
    start_date=datetime(2026, 8, 24),
    schedule=None,
    catchup=False,
    tags=[
        "snowflake",
        "ingestion",
        "ai_customer_intelligence",
    ],
) as dag:

    load_snowflake_tables_task = PythonOperator(
        task_id="load_snowflake_tables",
        python_callable=load_snowflake_tables,
    )
