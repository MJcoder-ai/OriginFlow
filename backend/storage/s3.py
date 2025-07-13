import boto3
import os
import datetime

s3 = boto3.client("s3")
BUCKET = os.getenv("S3_BUCKET")


def get_presigned_url(key: str, mime: str, expires: int = 900) -> str:
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": key, "ContentType": mime},
        ExpiresIn=expires,
    )
