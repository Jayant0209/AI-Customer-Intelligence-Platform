import boto3


def get_s3_client():
    """
    Create and return an S3 client.

    AWS credentials are automatically picked up
    from the AWS CLI configuration.
    """
    return boto3.client("s3", region_name="ap-south-1")