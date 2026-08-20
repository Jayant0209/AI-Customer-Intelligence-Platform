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
        ("customers.csv", "customers"),
        ("products.csv", "products"),
        ("orders.csv", "orders"),
        ("payments.csv", "payments"),
    ]

    for file_name, folder_name in datasets:
        local_file = project_root / "data" / "raw" / file_name

        upload_file(
            local_file,
            f"raw/{folder_name}/{file_name}"
        )