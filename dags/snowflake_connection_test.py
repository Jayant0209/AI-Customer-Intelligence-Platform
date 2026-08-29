from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.providers.standard.operators.python import PythonOperator


SNOWFLAKE_CONN_ID = "snowflake_default"


def test_snowflake_connection():
    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID
    )

    sql = """
    SELECT
        CURRENT_ACCOUNT() AS ACCOUNT_NAME,
        CURRENT_USER() AS USER_NAME,
        CURRENT_ROLE() AS ROLE_NAME,
        CURRENT_WAREHOUSE() AS WAREHOUSE_NAME,
        CURRENT_DATABASE() AS DATABASE_NAME,
        CURRENT_SCHEMA() AS SCHEMA_NAME
    """

    result = hook.get_first(sql)

    print("========================================")
    print("SNOWFLAKE CONNECTION TEST")
    print("========================================")

    print(f"Account    : {result[0]}")
    print(f"User       : {result[1]}")
    print(f"Role       : {result[2]}")
    print(f"Warehouse  : {result[3]}")
    print(f"Database   : {result[4]}")
    print(f"Schema     : {result[5]}")

    print("========================================")
    print("Snowflake connection successful.")
    print("========================================")


with DAG(
    dag_id="snowflake_connection_test",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=[
        "ai_customer_intelligence",
        "snowflake",
        "connectivity",
    ],
) as dag:

    test_connection = PythonOperator(
        task_id="test_snowflake_connection",
        python_callable=test_snowflake_connection,
    )
