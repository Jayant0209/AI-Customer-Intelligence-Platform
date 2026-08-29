from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator


def test_airflow():
    print("Airflow is working successfully!")
    print("AI Customer Intelligence Platform - Airflow Test")


with DAG(
    dag_id="airflow_test_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test", "ai_customer_intelligence"],
) as dag:

    test_task = PythonOperator(
        task_id="test_airflow_task",
        python_callable=test_airflow,
    )
