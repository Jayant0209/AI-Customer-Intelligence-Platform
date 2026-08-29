from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


DBT_PATH = "/home/asus/ai_customer_airflow/.venv/bin/dbt"
DBT_PROJECT_DIR = "/home/asus/ai_customer_airflow/ai_customer_dbt"


with DAG(
    dag_id="dbt_transformation_pipeline",
    description="Run dbt transformations and data quality tests in Snowflake",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["dbt", "snowflake", "transformation"],
) as dag:

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"{DBT_PATH} run "
            f"--project-dir {DBT_PROJECT_DIR}"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"{DBT_PATH} test "
            f"--project-dir {DBT_PROJECT_DIR}"
        ),
    )

    dbt_run >> dbt_test
