"""B2 public /s3/ signed URL and method checks; never prints a URL or credential."""
import os
import time
import uuid
from pathlib import Path

import boto3
import requests
from botocore.config import Config

root = Path(os.environ["PICTURAS_SECRETS_DIR"])
ca = str(root / "pki/services/seaweedfs/ca.crt")
public_ca = str(root / "pki/services/nginx/ca.crt")
value = lambda name: (root / "values" / name).read_text().strip()
access, secret = value("s3_img_storage_access"), value("s3_img_storage_secret")
config = Config(signature_version="s3v4", s3={"addressing_style": "path"})
host = boto3.client("s3", endpoint_url="https://localhost:9000", aws_access_key_id=access,
                    aws_secret_access_key=secret, verify=ca, region_name="us-east-1", config=config)
signer = boto3.client("s3", endpoint_url="https://seaweedfs:9000", aws_access_key_id=access,
                      aws_secret_access_key=secret, verify=ca, region_name="us-east-1", config=config)
http = requests.Session()
http.trust_env = False
bucket = "picturas"
key = f"b2/signed-url-{uuid.uuid4().hex}"
body = b"B2 signed URL and Range fixture"

def public_url(op, ttl=60):
    internal = signer.generate_presigned_url(op, Params={"Bucket": bucket, "Key": key}, ExpiresIn=ttl)
    assert internal.startswith("https://seaweedfs:9000/")
    return internal.replace("https://seaweedfs:9000/", "https://localhost:8080/s3/", 1)

host.put_object(Bucket=bucket, Key=key, Body=body)
try:
    get_url = public_url("get_object")
    r = http.get(get_url, verify=public_ca, timeout=15)
    assert r.status_code == 200 and r.content == body, r.status_code
    r = http.get(get_url, headers={"Range": "bytes=0-5"}, verify=public_ca, timeout=15)
    assert r.status_code == 206 and r.content == body[:6], r.status_code
    r = http.head(public_url("head_object"), verify=public_ca, timeout=15)
    assert r.status_code == 200 and int(r.headers["content-length"]) == len(body), r.status_code
    for method in ("put", "post", "delete"):
        r = http.request(method, get_url, data=b"denied", verify=public_ca, timeout=15)
        assert r.status_code in (401, 403, 405), (method, r.status_code)
    expired = public_url("get_object", 1)
    time.sleep(3)
    r = http.get(expired, verify=public_ca, timeout=15)
    assert r.status_code in (401, 403), r.status_code
    r = http.get("https://localhost:8080/s3-console/", verify=public_ca, timeout=15)
    assert r.status_code == 404, r.status_code
    print("B2 signed URLs: GET, HEAD, Range passed; expired and unsafe methods denied; console 404")
finally:
    host.delete_object(Bucket=bucket, Key=key)
