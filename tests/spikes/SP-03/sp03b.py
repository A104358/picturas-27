import urllib.parse, requests, boto3, botocore, socket, ssl, time
from botocore.config import Config
EP = "https://seaweedfs:9000"; CA = "/pki/ca.crt"; B = "picturas"
cfg = Config(s3={"addressing_style": "path"}, signature_version="s3v4")
u = boto3.client("s3", endpoint_url=EP, aws_access_key_id="uploader", aws_secret_access_key="uploader-secret-0123456789", region_name="us-east-1", verify=CA, config=cfg)
adm = boto3.client("s3", endpoint_url=EP, aws_access_key_id="spikeadmin", aws_secret_access_key="spikeadmin-secret-0123456789", region_name="us-east-1", verify=CA, config=cfg)
def exists(k):
    try: return adm.head_object(Bucket=B, Key=k)["ContentLength"]
    except botocore.exceptions.ClientError as e: return f"absent({e.response['Error']['Code']})"
def raw(url, headers, body):
    p = urllib.parse.urlsplit(url); ctx = ssl.create_default_context(cafile=CA)
    s = ctx.wrap_socket(socket.create_connection((p.hostname, p.port)), server_hostname=p.hostname)
    s.sendall((f"PUT {p.path}?{p.query} HTTP/1.1\r\nHost: {p.netloc}\r\n" + "".join(f"{k}: {v}\r\n" for k, v in headers.items()) + "\r\n").encode() + body)
    s.settimeout(10); r = s.recv(4096); s.close(); return r.split(b"\r\n")[0].decode()
for i, (label, body) in enumerate([("exact 1000", b"a" * 1000), ("2000 bytes", b"a" * 2000), ("500 bytes", b"a" * 500)]):
    url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": f"staging/v4len{i}", "ContentLength": 1000}, ExpiresIn=120)
    if i == 0: print("signed headers:", urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).get("X-Amz-SignedHeaders"))
    print(f"presigned v4 CL=1000, {label} ->", requests.put(url, data=body, verify=CA).status_code, exists(f"staging/v4len{i}"))
url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/v4chunk", "ContentLength": 1000}, ExpiresIn=120)
print("presigned v4 CL=1000, chunked body (no CL header) ->", raw(url, {"Transfer-Encoding": "chunked"}, b"3e8\r\n" + b"a" * 1000 + b"\r\n0\r\n\r\n"), exists("staging/v4chunk"))
url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/v4nolen"}, ExpiresIn=120)
print("presigned v4 without CL: signed", urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).get("X-Amz-SignedHeaders"), "; 2000 bytes ->", requests.put(url, data=b"a" * 2000, verify=CA).status_code)
url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/v4exp"}, ExpiresIn=1); time.sleep(3)
print("presigned v4 expired ->", requests.put(url, data=b"a", verify=CA).status_code, exists("staging/v4exp"))
url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/v4tamper"}, ExpiresIn=120)
print("presigned v4 key tampered ->", requests.put(url.replace("v4tamper", "v4other"), data=b"a", verify=CA).status_code, exists("staging/v4other"))
url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/v4meth"}, ExpiresIn=120)
print("presigned PUT used as DELETE ->", requests.delete(url, verify=CA).status_code)
