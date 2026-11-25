"""B2 S3 TLS and principal-scope checks before bucket bootstrap."""
import os
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

root = Path(os.environ["PICTURAS_SECRETS_DIR"])
ca = str(root / "pki/services/seaweedfs/ca.crt")

def secret(name):
    return (root / "values" / name).read_text().strip()

def client(access, secret_key):
    return boto3.client("s3", endpoint_url="https://localhost:9000",
                        aws_access_key_id=access, aws_secret_access_key=secret_key,
                        verify=ca, region_name="us-east-1",
                        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}))

admin = client(secret("s3_admin_access"), secret("s3_admin_secret"))
admin.list_buckets()
limited = client(secret("s3_img_storage_access"), secret("s3_img_storage_secret"))
limited.list_buckets()
try:
    limited.create_bucket(Bucket="b2-denied-canary")
except ClientError as exc:
    assert exc.response["Error"]["Code"] in ("AccessDenied", "Forbidden")
else:
    raise AssertionError("img_storage can create buckets")
old = client("admin", "admin123")
try:
    old.list_buckets()
except ClientError as exc:
    assert exc.response["Error"]["Code"] in ("InvalidAccessKeyId", "AccessDenied", "SignatureDoesNotMatch")
else:
    raise AssertionError("Git-era S3 credential accepted")
print("B2 S3: HTTPS verified, old login denied, img_storage cannot create buckets")
