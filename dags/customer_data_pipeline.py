from datetime import datetime, timedelta

import pandas as pd

from airflow.sdk import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.standard.operators.python import PythonOperator


PROJECT_BUCKET = (
    "ai-customer-intelligence-jayant-2026-311051752069-ap-south-1-an"
)

AWS_CONN_ID = "aws_default"

DATASETS = {
    "customers": {
        "raw_key": "raw/customers/customers.csv",
        "validated_key": "validated/customers/customers.csv",
        "quarantine_key": "quarantine/customers/customers.csv",
        "required_columns": [
            "CUSTOMER_ID",
            "FIRST_NAME",
            "LAST_NAME",
            "EMAIL",
            "GENDER",
            "CITY",
            "STATE",
            "SIGNUP_DATE",
            "CUSTOMER_SEGMENT",
        ],
    },
    "products": {
        "raw_key": "raw/products/products.csv",
        "validated_key": "validated/products/products.csv",
        "quarantine_key": "quarantine/products/products.csv",
        "required_columns": [
            "PRODUCT_ID",
            "PRODUCT_NAME",
            "CATEGORY",
            "SUBCATEGORY",
            "BRAND",
            "PRICE",
            "COST",
        ],
    },
    "orders": {
        "raw_key": "raw/orders/orders.csv",
        "validated_key": "validated/orders/orders.csv",
        "quarantine_key": "quarantine/orders/orders.csv",
        "required_columns": [
            "ORDER_ID",
            "CUSTOMER_ID",
            "PRODUCT_ID",
            "ORDER_DATE",
            "QUANTITY",
            "UNIT_PRICE",
            "DISCOUNT",
            "TOTAL_AMOUNT",
            "ORDER_STATUS",
            "REGION",
        ],
    },
    "payments": {
        "raw_key": "raw/payments/payments.csv",
        "validated_key": "validated/payments/payments.csv",
        "quarantine_key": "quarantine/payments/payments.csv",
        "required_columns": [
            "PAYMENT_ID",
            "ORDER_ID",
            "PAYMENT_DATE",
            "PAYMENT_METHOD",
            "PAYMENT_STATUS",
            "AMOUNT",
        ],
    },
}


def get_s3_hook():
    return S3Hook(aws_conn_id=AWS_CONN_ID)


def check_s3_raw_files():
    """
    Verify that all expected RAW files exist in S3.
    """

    hook = get_s3_hook()

    print("=" * 80)
    print("S3 RAW FILE AVAILABILITY CHECK")
    print("=" * 80)

    for dataset_name, config in DATASETS.items():

        raw_key = config["raw_key"]

        obj = hook.get_key(
            key=raw_key,
            bucket_name=PROJECT_BUCKET,
        )

        if obj is None:
            raise FileNotFoundError(
                f"RAW file not found: s3://{PROJECT_BUCKET}/{raw_key}"
            )

        size = obj.content_length

        if size is None or size <= 0:
            raise ValueError(
                f"RAW file is empty: s3://{PROJECT_BUCKET}/{raw_key}"
            )

        print(
            f"{dataset_name.upper():12} "
            f"FOUND | {size:,} bytes | {raw_key}"
        )

    print("=" * 80)
    print("ALL RAW FILES ARE AVAILABLE")
    print("=" * 80)


def validate_customers(df):
    errors = []

    if df["CUSTOMER_ID"].isna().any():
        errors.append("CUSTOMER_ID contains NULL values")

    if df["CUSTOMER_ID"].astype(str).str.strip().eq("").any():
        errors.append("CUSTOMER_ID contains blank values")

    if df["EMAIL"].isna().any():
        errors.append("EMAIL contains NULL values")

    if df["EMAIL"].astype(str).str.strip().eq("").any():
        errors.append("EMAIL contains blank values")

    if df["CUSTOMER_ID"].duplicated().any():
        errors.append("Duplicate CUSTOMER_ID values found")

    signup_dates = pd.to_datetime(
        df["SIGNUP_DATE"],
        errors="coerce",
    )

    if signup_dates.isna().any():
        errors.append("Invalid SIGNUP_DATE values found")

    return errors


def validate_products(df):
    errors = []

    if df["PRODUCT_ID"].isna().any():
        errors.append("PRODUCT_ID contains NULL values")

    if df["PRODUCT_ID"].astype(str).str.strip().eq("").any():
        errors.append("PRODUCT_ID contains blank values")

    if df["PRODUCT_ID"].duplicated().any():
        errors.append("Duplicate PRODUCT_ID values found")

    price = pd.to_numeric(
        df["PRICE"],
        errors="coerce",
    )

    cost = pd.to_numeric(
        df["COST"],
        errors="coerce",
    )

    if price.isna().any():
        errors.append("Invalid PRICE values found")

    if cost.isna().any():
        errors.append("Invalid COST values found")

    if (price < 0).any():
        errors.append("Negative PRICE values found")

    if (cost < 0).any():
        errors.append("Negative COST values found")

    return errors


def validate_orders(df):
    errors = []

    for column in [
        "ORDER_ID",
        "CUSTOMER_ID",
        "PRODUCT_ID",
    ]:
        if df[column].isna().any():
            errors.append(
                f"{column} contains NULL values"
            )

        if df[column].astype(str).str.strip().eq("").any():
            errors.append(
                f"{column} contains blank values"
            )

    if df["ORDER_ID"].duplicated().any():
        errors.append(
            "Duplicate ORDER_ID values found"
        )

    order_dates = pd.to_datetime(
        df["ORDER_DATE"],
        errors="coerce",
    )

    if order_dates.isna().any():
        errors.append(
            "Invalid ORDER_DATE values found"
        )

    quantity = pd.to_numeric(
        df["QUANTITY"],
        errors="coerce",
    )

    if quantity.isna().any():
        errors.append(
            "Invalid QUANTITY values found"
        )

    if (quantity <= 0).any():
        errors.append(
            "QUANTITY must be greater than zero"
        )

    for column in [
        "UNIT_PRICE",
        "DISCOUNT",
        "TOTAL_AMOUNT",
    ]:

        values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if values.isna().any():
            errors.append(
                f"Invalid {column} values found"
            )

        if (values < 0).any():
            errors.append(
                f"Negative {column} values found"
            )

    return errors


def validate_payments(df):
    errors = []

    for column in [
        "PAYMENT_ID",
        "ORDER_ID",
    ]:
        if df[column].isna().any():
            errors.append(
                f"{column} contains NULL values"
            )

        if df[column].astype(str).str.strip().eq("").any():
            errors.append(
                f"{column} contains blank values"
            )

    if df["PAYMENT_ID"].duplicated().any():
        errors.append(
            "Duplicate PAYMENT_ID values found"
        )

    payment_dates = pd.to_datetime(
        df["PAYMENT_DATE"],
        errors="coerce",
    )

    if payment_dates.isna().any():
        errors.append(
            "Invalid PAYMENT_DATE values found"
        )

    amount = pd.to_numeric(
        df["AMOUNT"],
        errors="coerce",
    )

    if amount.isna().any():
        errors.append(
            "Invalid AMOUNT values found"
        )

    if (amount < 0).any():
        errors.append(
            "Negative AMOUNT values found"
        )

    return errors


VALIDATORS = {
    "customers": validate_customers,
    "products": validate_products,
    "orders": validate_orders,
    "payments": validate_payments,
}


def validate_and_route_dataset(dataset_name):
    """
    Validate one RAW CSV from S3.

    If validation succeeds:
        RAW → VALIDATED

    If validation fails:
        RAW → QUARANTINE

    RAW is never modified or deleted.
    """

    config = DATASETS[dataset_name]
    hook = get_s3_hook()

    raw_key = config["raw_key"]
    validated_key = config["validated_key"]
    quarantine_key = config["quarantine_key"]

    print("=" * 80)
    print(f"PROCESSING DATASET: {dataset_name.upper()}")
    print("=" * 80)

    print(
        f"Source: "
        f"s3://{PROJECT_BUCKET}/{raw_key}"
    )

    obj = hook.get_key(
        key=raw_key,
        bucket_name=PROJECT_BUCKET,
    )

    if obj is None:
        raise FileNotFoundError(
            f"RAW file not found: {raw_key}"
        )

    file_size = obj.content_length

    print(f"File size: {file_size:,} bytes")

    if file_size is None or file_size <= 0:
        raise ValueError(
            f"RAW file is empty: {raw_key}"
        )

    response = obj.get()

    body = response["Body"]

    chunk_size = 10000

    total_records = 0
    invalid_chunks = 0
    validation_errors = set()

    validator = VALIDATORS[dataset_name]

    first_chunk = True

    try:
        for chunk in pd.read_csv(
            body,
            chunksize=chunk_size,
        ):

            total_records += len(chunk)

            chunk.columns = [
                column.strip().upper()
                for column in chunk.columns
            ]

            if first_chunk:

                missing_columns = [
                    column
                    for column in config["required_columns"]
                    if column not in chunk.columns
                ]

                if missing_columns:
                    raise ValueError(
                        f"{dataset_name.upper()} missing "
                        f"required columns: "
                        f"{missing_columns}"
                    )

                first_chunk = False

            errors = validator(chunk)

            if errors:
                invalid_chunks += 1

                for error in errors:
                    validation_errors.add(error)

    finally:
        body.close()

    print()
    print("VALIDATION SUMMARY")
    print("-" * 80)
    print(f"Dataset         : {dataset_name}")
    print(f"Total records   : {total_records}")
    print(f"Invalid chunks  : {invalid_chunks}")

    if validation_errors:

        print()
        print("VALIDATION ISSUES:")

        for error in sorted(validation_errors):
            print(f" - {error}")

    print("-" * 80)

    if invalid_chunks > 0:

        print(
            "VALIDATION STATUS: FAILED"
        )

        print(
            f"Routing file to quarantine/: "
            f"{quarantine_key}"
        )

        hook.copy_object(
            source_bucket_key=raw_key,
            dest_bucket_key=quarantine_key,
            source_bucket_name=PROJECT_BUCKET,
            dest_bucket_name=PROJECT_BUCKET,
        )

        raise ValueError(
            f"{dataset_name.upper()} failed validation"
        )

    print(
        "VALIDATION STATUS: SUCCESS"
    )

    print(
        f"Routing file to validated/: "
        f"{validated_key}"
    )

    hook.copy_object(
        source_bucket_key=raw_key,
        dest_bucket_key=validated_key,
        source_bucket_name=PROJECT_BUCKET,
        dest_bucket_name=PROJECT_BUCKET,
    )

    print()
    print(
        f"VALIDATED FILE CREATED: "
        f"s3://{PROJECT_BUCKET}/{validated_key}"
    )

    print("=" * 80)


with DAG(
    dag_id="customer_data_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
    tags=[
        "ai_customer_intelligence",
        "s3",
        "validation",
        "data_quality",
    ],
) as dag:

    check_raw_files = PythonOperator(
        task_id="check_s3_raw_files",
        python_callable=check_s3_raw_files,
    )

    validate_customers_task = PythonOperator(
        task_id="validate_customers",
        python_callable=validate_and_route_dataset,
        op_kwargs={
            "dataset_name": "customers",
        },
    )

    validate_products_task = PythonOperator(
        task_id="validate_products",
        python_callable=validate_and_route_dataset,
        op_kwargs={
            "dataset_name": "products",
        },
    )

    validate_orders_task = PythonOperator(
        task_id="validate_orders",
        python_callable=validate_and_route_dataset,
        op_kwargs={
            "dataset_name": "orders",
        },
    )

    validate_payments_task = PythonOperator(
        task_id="validate_payments",
        python_callable=validate_and_route_dataset,
        op_kwargs={
            "dataset_name": "payments",
        },
    )

    check_raw_files >> [
        validate_customers_task,
        validate_products_task,
        validate_orders_task,
        validate_payments_task,
    ]
