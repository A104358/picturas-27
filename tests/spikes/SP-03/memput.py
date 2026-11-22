import requests, boto3, sys, time
from botocore.config import Config
u = boto3.client("s3", endpoint_url="https://seaweedfs:9000", aws_access_key_id="uploader", aws_secret_access_key="uploader-secret-0123456789", region_name="us-east-1", verify="/pki/ca.crt", config=Config(s3={"addressing_style": "path"}, signature_version="s3v4"))
k = "staging/memput-" + sys.argv[1]
url = u.generate_presigned_url("put_object", Params={"Bucket": "picturas", "Key": k, "ContentLength": 500 << 20}, ExpiresIn=600)
t0 = time.time()
with open("/tmp/big500", "rb") as f: r = requests.put(url, data=f, headers={"Content-Length": str(500 << 20)}, verify="/pki/ca.crt")
print(f"PUT {r.status_code} {1000*(time.time()-t0):.0f} ms", flush=True)
