import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from backend.config import settings

def get_minio_client():
    return boto3.client(
        's3',
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ROOT_USER,
        aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
        region_name='us-east-1'
    )

def check_bucket_health():
    client = get_minio_client()
    try:
        client.head_bucket(Bucket=settings.MINIO_BUCKET)
        return True
    except ClientError as e:
        import logging
        logging.error(f"MinIO health check failed with ClientError: {e}")
        return False
    except Exception as e:
        import logging
        logging.error(f"MinIO health check failed: {e}")
        return False
