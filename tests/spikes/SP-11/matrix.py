import json, sys, boto3, botocore, requests
from botocore.config import Config
EP = sys.argv[1] if len(sys.argv) > 1 else "https://seaweedfs:9000"
CA = "/pki/ca.crt"
CREDS = {
    "admin": ("spikeadmin", "spikeadmin-secret-0123456789"),
    "img_storage": ("imgstorage", "imgstorage-secret-0123456789"),
    "uploader": ("uploader", "uploader-secret-0123456789"),
    "reader_src": ("readersrc", "readersrc-secret-0123456789"),
    "git_default": ("admin", "admin123"),
    "bad_secret": ("imgstorage", "wrong"),
}
def c(who, verify=CA):
    a, s = CREDS[who]
    return boto3.client("s3", endpoint_url=EP, aws_access_key_id=a, aws_secret_access_key=s, region_name="us-east-1",
                        verify=verify, config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 1},
                                                     signature_version="s3v4"))
def t(label, fn):
    try:
        r = fn(); print(f"ALLOW  {label}"); return r
    except botocore.exceptions.ClientError as e:
        print(f"DENY   {label}  [{e.response['Error']['Code']} {e.response['ResponseMetadata']['HTTPStatusCode']}]")
    except Exception as e:
        print(f"ERROR  {label}  [{type(e).__name__}: {str(e)[:90]}]")
adm = c("admin")
t("admin create_bucket picturas", lambda: adm.create_bucket(Bucket="picturas"))
t("admin create_bucket other", lambda: adm.create_bucket(Bucket="other"))
t("admin put other/x", lambda: adm.put_object(Bucket="other", Key="x", Body=b"x"))
for who in ("git_default", "bad_secret"):
    t(f"{who} list_buckets", lambda: c(who).list_buckets())
    t(f"{who} list picturas", lambda: c(who).list_objects_v2(Bucket="picturas"))
s = c("img_storage")
t("img_storage put users/u/projects/p/src/a.png", lambda: s.put_object(Bucket="picturas", Key="users/u/projects/p/src/a.png", Body=b"A" * 1000))
t("img_storage get", lambda: s.get_object(Bucket="picturas", Key="users/u/projects/p/src/a.png")["Body"].read())
t("img_storage head", lambda: s.head_object(Bucket="picturas", Key="users/u/projects/p/src/a.png"))
t("img_storage list picturas", lambda: s.list_objects_v2(Bucket="picturas", Prefix="users/"))
t("img_storage copy src->out", lambda: s.copy_object(Bucket="picturas", Key="users/u/projects/p/out/a.png", CopySource="picturas/users/u/projects/p/src/a.png"))
t("img_storage delete out", lambda: s.delete_object(Bucket="picturas", Key="users/u/projects/p/out/a.png"))
t("img_storage create_bucket canary (B2)", lambda: s.create_bucket(Bucket="med-canary-x"))
t("img_storage delete_bucket picturas", lambda: s.delete_bucket(Bucket="picturas"))
t("img_storage list_buckets", lambda: s.list_buckets()["Buckets"])
t("img_storage get other/x", lambda: s.get_object(Bucket="other", Key="x"))
t("img_storage put other/y", lambda: s.put_object(Bucket="other", Key="y", Body=b"y"))
t("img_storage put_bucket_policy", lambda: s.put_bucket_policy(Bucket="picturas", Policy=json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::picturas/*"}]})))
t("img_storage put_bucket_acl public-read", lambda: s.put_bucket_acl(Bucket="picturas", ACL="public-read"))
u = c("uploader")
t("uploader put staging/att1", lambda: u.put_object(Bucket="picturas", Key="staging/att1", Body=b"S" * 100))
t("uploader put users/u/projects/p/src/evil", lambda: u.put_object(Bucket="picturas", Key="users/u/projects/p/src/evil", Body=b"E"))
t("uploader get staging/att1", lambda: u.get_object(Bucket="picturas", Key="staging/att1"))
t("uploader delete staging/att1", lambda: u.delete_object(Bucket="picturas", Key="staging/att1"))
t("uploader list picturas", lambda: u.list_objects_v2(Bucket="picturas"))
r = c("reader_src")
t("reader_src get users/.../a.png", lambda: r.get_object(Bucket="picturas", Key="users/u/projects/p/src/a.png"))
t("reader_src get staging/att1", lambda: r.get_object(Bucket="picturas", Key="staging/att1"))
t("reader_src put users/x", lambda: r.put_object(Bucket="picturas", Key="users/x", Body=b"x"))
# presigned URLs over HTTPS
url = s.generate_presigned_url("get_object", Params={"Bucket": "picturas", "Key": "users/u/projects/p/src/a.png"}, ExpiresIn=60)
print("presigned GET (img_storage) ->", requests.get(url, verify=CA).status_code)
url = u.generate_presigned_url("put_object", Params={"Bucket": "picturas", "Key": "staging/att2"}, ExpiresIn=60)
print("presigned PUT staging (uploader) ->", requests.put(url, data=b"P" * 10, verify=CA).status_code)
url = u.generate_presigned_url("put_object", Params={"Bucket": "picturas", "Key": "users/u/projects/p/src/evil2"}, ExpiresIn=60)
print("presigned PUT outside staging (uploader) ->", requests.put(url, data=b"E", verify=CA).status_code)
print("anonymous GET object ->", requests.get(f"{EP}/picturas/users/u/projects/p/src/a.png", verify=CA).status_code)
print("anonymous PUT object ->", requests.put(f"{EP}/picturas/anon", data=b"x", verify=CA).status_code)
t("img_storage with otherca trust", lambda: c("img_storage", verify="/pki/otherca.crt").list_objects_v2(Bucket="picturas"))
t("final admin list", lambda: print("   keys:", [o["Key"] for o in adm.list_objects_v2(Bucket="picturas").get("Contents", [])]))
