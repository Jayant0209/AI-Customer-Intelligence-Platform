from datetime import datetime

import os
import sys

# ---------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------
# AIRFLOW IMPORTS
# ---------------------------------------------------------

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator


# ---------------------------------------------------------
# PROJECT IMPORTS
# ---------------------------------------------------------

from ml.snowflake_writer import (
    write_customer_segments,
    verify_customer_segments,
)


# ---------------------------------------------------------
# TASK FUNCTIONS
# ---------------------------------------------------------

def write_segments():

    print("=" * 60)
    print("WRITING CUSTOMER SEGMENTATION TO SNOWFLAKE")
    print("=" * 60)

    rows = write_customer_segments()

    print(f"\nRows written to Snowflake: {rows:,}")


def verify_segments():

    print("=" * 60)
    print("VERIFYING CUSTOMER SEGMENTATION IN SNOWFLAKE")
    print("=" * 60)

    result = verify_customer_segments()

    print("\nSnowflake verification result:")
    print(result)


# ---------------------------------------------------------
# DAG
# ---------------------------------------------------------

with DAG(
    dag_id="ml_customer_segmentation_snowflake",
    start_date=datetime(2026, 8, 24),
    schedule=None,
    catchup=False,
    tags=[
        "ml",
        "snowflake",
        "customer-segmentation",
    ],
    description=(
        "Write and verify ML customer segmentation "
        "results in Snowflake"
    ),
) as dag:

    write_task = PythonOperator(
        task_id="write_customer_segments",
        python_callable=write_segments,
    )

    verify_task = PythonOperator(
        task_id="verify_customer_segments",
        python_callable=verify_segments,
    )

    write_task >> verify_task
