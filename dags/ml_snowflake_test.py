from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook


SNOWFLAKE_CONN_ID = "snowflake_default"


def test_rfm_connection():
    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID
    )

    sql = """
    SELECT COUNT(*) AS CUSTOMER_COUNT
    FROM AI_CUSTOMER_DB.ANALYTICS.CUSTOMER_RFM
    """

    result = hook.get_first(sql)

    print("=" * 60)
    print("ML SNOWFLAKE CONNECTION TEST")
    print("=" * 60)
    print(f"Customer count: {result[0]}")

    if result[0] != 10000:
        raise ValueError(
            f"Expected 10,000 customers but found {result[0]}"
        )

    print("RFM table validation: SUCCESS")


with DAG(
    dag_id="ml_snowflake_test",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ml", "snowflake", "rfm"],
) as dag:

    test_connection = PythonOperator(
        task_id="test_rfm_connection",
        python_callable=test_rfm_connection,
    )
