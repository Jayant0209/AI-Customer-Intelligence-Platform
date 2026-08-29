from datetime import datetime

import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

from ml.rfm_segmentation import run_segmentation


SNOWFLAKE_CONN_ID = "snowflake_default"


def run_ml_segmentation():

    print("=" * 60)
    print("LOADING RFM DATA FROM SNOWFLAKE")
    print("=" * 60)

    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID
    )

    sql = """
    SELECT
        CUSTOMER_ID,
        FIRST_NAME,
        LAST_NAME,
        EMAIL,
        CITY,
        STATE,
        CUSTOMER_SEGMENT,
        RECENCY_DAYS,
        FREQUENCY,
        MONETARY_VALUE,
        FIRST_ORDER_DATE,
        LAST_ORDER_DATE
    FROM AI_CUSTOMER_DB.ANALYTICS.CUSTOMER_RFM
    """

    df = hook.get_pandas_df(sql)

    print(f"Rows loaded: {len(df):,}")
    print(f"Columns loaded: {len(df.columns)}")

    if len(df) != 10000:
        raise ValueError(
            f"Expected 10,000 customers, found {len(df)}"
        )

    (
        customer_segments,
        cluster_profile,
        model_evaluation,
        model,
        scaler,
    ) = run_segmentation(df)

    print("\nFinal validation")
    print("-" * 60)

    print(
        f"Customers segmented: "
        f"{len(customer_segments):,}"
    )

    print(
        f"Clusters created: "
        f"{len(cluster_profile)}"
    )

    print("\nModel evaluation:")
    print(
        model_evaluation.to_string(index=False)
    )

    print("\nCustomer segment distribution:")

    print(
        customer_segments[
            "SEGMENT_NAME"
        ].value_counts().to_string()
    )

    print("\nML segmentation task: SUCCESS")


with DAG(
    dag_id="ml_customer_segmentation_test",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=[
        "ml",
        "customer-segmentation",
        "rfm",
        "snowflake",
    ],
) as dag:

    segmentation_task = PythonOperator(
        task_id="run_ml_segmentation",
        python_callable=run_ml_segmentation,
    )
