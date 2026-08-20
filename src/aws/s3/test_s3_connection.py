from s3_utils import get_s3_client


BUCKET_NAME = "ai-customer-intelligence-jayant-2026-311051752069-ap-south-1-an"


def test_s3_connection():
    s3 = get_s3_client()

    response = s3.head_bucket(Bucket=BUCKET_NAME)

    print("S3 connection successful!")
    print(f"Bucket: {BUCKET_NAME}")


if __name__ == "__main__":
    test_s3_connection()