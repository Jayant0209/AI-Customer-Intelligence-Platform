from pathlib import Path

from s3_utils import get_s3_client


BUCKET_NAME = "ai-customer-intelligence-jayant-2026-311051752069-ap-south-1-an"


def upload_file(local_file, s3_key):
    s3 = get_s3_client()

    s3.upload_file(
        str(local_file),
        BUCKET_NAME,
        s3_key
    )

    print(f"Uploaded: {local_file.name}")
    print(f"S3 location: s3://{BUCKET_NAME}/{s3_key}")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[3]

    datasets = [
        # Raw data
        ("data/raw/customers.csv", "raw/customers/customers.csv"),
        ("data/raw/products.csv", "raw/products/products.csv"),
        ("data/raw/orders.csv", "raw/orders/orders.csv"),
        ("data/raw/payments.csv", "raw/payments/payments.csv"),

        # Validated data
        ("data/valid/customers_valid.csv", "validated/customers/customers.csv"),
        ("data/valid/orders_valid.csv", "validated/orders/orders.csv"),

        # Quarantine data
        (
            "data/quarantine/customers_invalid.csv",
            "quarantine/customers/customers_invalid.csv"
        ),
        (
            "data/quarantine/orders_invalid.csv",
            "quarantine/orders/orders_invalid.csv"
        ),
    ]

    for local_path, s3_key in datasets:
        local_file = project_root / local_path

        if not local_file.exists():
            print(f"File not found: {local_file}")
            continue

        upload_file(local_file, s3_key)