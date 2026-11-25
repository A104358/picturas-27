import boto3, time, sys
from botocore.config import Config
s = boto3.client("s3", endpoint_url="https://seaweedfs:9000", aws_access_key_id="imgstorage", aws_secret_access_key="imgstorage-secret-0123456789", region_name="us-east-1", verify="/pki/ca.crt", config=Config(s3={"addressing_style": "path"}, read_timeout=600, signature_version="s3v4"))
t0 = time.time(); s.copy_object(Bucket="picturas", Key="users/u/projects/p/cand/c-" + sys.argv[1], CopySource="picturas/staging/memput-" + sys.argv[1]); print(f"COPY {1000*(time.time()-t0):.0f} ms")
