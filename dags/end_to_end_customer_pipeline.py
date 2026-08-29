from datetime import datetime, timedelta
import os
import sys

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator


# ============================================================
# DAG DIRECTORY / IMPORT PATH
# ============================================================

DAG_DIR = os.path.dirname(os.path.abspath(__file__))

if DAG_DIR not in sys.path:
    sys.path.insert(0, DAG_DIR)


from pipeline_tasks import (
    load_snowflake_tables,
    validate_snowflake_data,
)


# ============================================================
# CONFIGURATION
# ============================================================

DAG_ID = "end_to_end_customer_pipeline"

DBT_PATH = "/home/asus/ai_customer_airflow/.venv/bin/dbt"
DBT_PROJECT_DIR = "/home/asus/ai_customer_airflow/ai_customer_dbt"


# ============================================================
# DEFAULT ARGUMENTS
# ============================================================

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


# ============================================================
# DAG DEFINITION
# ============================================================

with DAG(
    dag_id=DAG_ID,
    description=(
        "End-to-end AI Customer Intelligence pipeline "
        "from Snowflake RAW ingestion through data quality "
        "and dbt transformations."
    ),
    start_date=datetime(2026, 8, 24),
    schedule=None,
    catchup=False,
    default_args=default_args,
    max_active_runs=1,
    tags=[
        "ai_customer_intelligence",
        "end_to_end",
        "snowflake",
        "dbt",
        "data_quality",
    ],
) as dag:

    # ========================================================
    # 1. SNOWFLAKE INGESTION
    # ========================================================

    snowflake_ingestion = PythonOperator(
        task_id="snowflake_ingestion",
        python_callable=load_snowflake_tables,
    )

    # ========================================================
    # 2. SNOWFLAKE DATA QUALITY
    # ========================================================

    snowflake_data_quality = PythonOperator(
        task_id="snowflake_data_quality",
        python_callable=validate_snowflake_data,
    )

    # ========================================================
    # 3. DBT RUN
    # ========================================================

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"{DBT_PATH} run "
            f"--project-dir {DBT_PROJECT_DIR}"
        ),
    )

    # ========================================================
    # 4. DBT TEST
    # ========================================================

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"{DBT_PATH} test "
            f"--project-dir {DBT_PROJECT_DIR}"
        ),
    )

    # ========================================================
    # DEPENDENCY CHAIN
    # ========================================================

    (
        snowflake_ingestion
        >> snowflake_data_quality
        >> dbt_run
        >> dbt_test
    )