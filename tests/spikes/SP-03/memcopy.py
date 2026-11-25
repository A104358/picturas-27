import boto3, time, sys
from botocore.config import Config
s = boto3.client("s3", endpoint_url="https://seaweedfs:9000", aws_access_key_id="imgstorage", aws_secret_access_key="imgstorage-secret-0123456789", region_name="us-east-1", verify="/pki/ca.crt", config=Config(s3={"addressing_style": "path"}, read_timeout=600))
if sys.argv[1] == "prep":
    s.upload_file("/tmp/big500", "picturas", "users/u/projects/p/src/mem-src"); print("uploaded")
else:
    t0 = time.time(); s.copy_object(Bucket="picturas", Key="users/u/projects/p/cand/mem-dst-" + sys.argv[2], CopySource="picturas/users/u/projects/p/src/mem-src"); print(f"COPY {1000*(time.time()-t0):.0f} ms")
