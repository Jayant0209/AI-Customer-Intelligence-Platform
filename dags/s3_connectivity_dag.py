from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.standard.operators.python import PythonOperator


PROJECT_BUCKET = "ai-customer-intelligence-jayant-2026-311051752069-ap-south-1-an"


def check_s3_connection():
    hook = S3Hook(aws_conn_id="aws_default")

    keys = hook.list_keys(
        bucket_name=PROJECT_BUCKET,
        prefix="raw/"
    )

    print(f"S3 bucket: {PROJECT_BUCKET}")
    print(f"Objects found under raw/: {len(keys or [])}")

    if keys:
        print("Sample objects:")
        for key in keys[:10]:
            print(f" - {key}")
    else:
        print("No objects found under raw/")


with DAG(
    dag_id="s3_connectivity_check",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ai_customer_intelligence", "s3", "connectivity"],
) as dag:

    check_s3 = PythonOperator(
        task_id="check_s3_connection",
        python_callable=check_s3_connection,
    )
