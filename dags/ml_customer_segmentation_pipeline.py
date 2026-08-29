from datetime import datetime
import os
import sys

# ---------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

from ml.rfm_segmentation import run_segmentation
from ml.snowflake_writer import (
    write_customer_segments,
    verify_customer_segments,
)


SNOWFLAKE_CONN_ID = "snowflake_default"


# ---------------------------------------------------------
# ML TASK
# ---------------------------------------------------------

def run_ml_pipeline():

    print("=" * 60)
    print("AI CUSTOMER INTELLIGENCE")
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

    print("\nML PIPELINE VALIDATION")
    print("-" * 60)

    if len(customer_segments) != 10000:
        raise ValueError(
            "ML segmentation did not produce 10,000 customers."
        )

    if customer_segments["CUSTOMER_ID"].duplicated().any():
        raise ValueError(
            "Duplicate CUSTOMER_ID values found."
        )

    print(f"Customers segmented: {len(customer_segments):,}")
    print(f"Clusters created: {len(cluster_profile)}")

    print("\nSegment distribution:")
    print(
        customer_segments["SEGMENT_NAME"]
        .value_counts()
        .to_string()
    )

    print("\nML segmentation: SUCCESS")


# ---------------------------------------------------------
# SNOWFLAKE WRITE TASK
# ---------------------------------------------------------

def write_ml_results():

    print("=" * 60)
    print("WRITING ML RESULTS TO SNOWFLAKE")
    print("=" * 60)

    rows_written = write_customer_segments()

    print(f"Rows written: {rows_written:,}")

    if rows_written != 10000:
        raise ValueError(
            f"Expected 10,000 rows, wrote {rows_written}"
        )

    print("Snowflake write: SUCCESS")


# ---------------------------------------------------------
# SNOWFLAKE VERIFICATION TASK
# ---------------------------------------------------------

def verify_ml_results():

    print("=" * 60)
    print("VERIFYING ML RESULTS IN SNOWFLAKE")
    print("=" * 60)

    result = verify_customer_segments()

    print("Snowflake verification: SUCCESS")
    print(result)


# ---------------------------------------------------------
# DAG
# ---------------------------------------------------------

with DAG(
    dag_id="ml_customer_segmentation_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=[
        "ml",
        "snowflake",
        "customer-intelligence",
    ],
) as dag:

    ml_task = PythonOperator(
        task_id="run_ml_segmentation",
        python_callable=run_ml_pipeline,
    )

    write_task = PythonOperator(
        task_id="write_ml_results",
        python_callable=write_ml_results,
    )

    verify_task = PythonOperator(
        task_id="verify_ml_results",
        python_callable=verify_ml_results,
    )

    ml_task >> write_task >> verify_task
