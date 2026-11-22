import hashlib, os, socket, ssl, sys, time, json, urllib.parse
import boto3, botocore, requests
from botocore.config import Config
EP = "https://seaweedfs:9000"; CA = "/pki/ca.crt"; B = "picturas"
def c(a, s): return boto3.client("s3", endpoint_url=EP, aws_access_key_id=a, aws_secret_access_key=s, region_name="us-east-1", verify=CA, config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 1}, read_timeout=600))
adm = c("spikeadmin", "spikeadmin-secret-0123456789")
s = c("imgstorage", "imgstorage-secret-0123456789")
u = c("uploader", "uploader-secret-0123456789")
def exists(k):
    try: return adm.head_object(Bucket=B, Key=k)["ContentLength"]
    except botocore.exceptions.ClientError as e: return f"absent({e.response['Error']['Code']})"
def raw_put(url, headers, body_iter, close_early=False):
    p = urllib.parse.urlsplit(url)
    ctx = ssl.create_default_context(cafile=CA)
    sock = ctx.wrap_socket(socket.create_connection((p.hostname, p.port)), server_hostname=p.hostname)
    req = f"PUT {p.path}?{p.query} HTTP/1.1\r\nHost: {p.netloc}\r\n" + "".join(f"{k}: {v}\r\n" for k, v in headers.items()) + "\r\n"
    sock.sendall(req.encode()); sent = 0
    for chunk in body_iter:
        sock.sendall(chunk); sent += len(chunk)
    if close_early:
        sock.close(); return ("closed", sent)
    sock.settimeout(30); resp = b""
    try:
        while b"\r\n\r\n" not in resp:
            d = sock.recv(4096)
            if not d: break
            resp += d
    except Exception as e: resp += f" <{type(e).__name__}>".encode()
    sock.close(); return (resp.split(b"\r\n")[0].decode(errors="replace"), sent)
MiB = 1024 * 1024
print("## 1 signed Content-Length (presigned PUT with ContentLength=1000 by uploader)")
url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/len1", "ContentLength": 1000}, ExpiresIn=120)
print("  signed headers:", urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).get("X-Amz-SignedHeaders"))
print("  exact 1000 bytes ->", requests.put(url, data=b"a" * 1000, verify=CA).status_code, exists("staging/len1"))
url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/len2", "ContentLength": 1000}, ExpiresIn=120)
print("  2000 bytes (CL 2000) ->", requests.put(url, data=b"a" * 2000, verify=CA).status_code, exists("staging/len2"))
print("  500 bytes (CL 500) ->", requests.put(url, data=b"a" * 500, verify=CA).status_code, exists("staging/len2"))
print("  CL header 1000 but chunked body ->", raw_put(url, {"Transfer-Encoding": "chunked"}, [b"3e8\r\n" + b"a" * 1000 + b"\r\n0\r\n\r\n"]), exists("staging/len2"))
url0 = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/len3"}, ExpiresIn=120)
print("  unsigned length: presigned without ContentLength, 2000 bytes ->", requests.put(url0, data=b"a" * 2000, verify=CA).status_code, exists("staging/len3"))
print("## 2 interrupted PUT (CL=100 MiB, 10 MiB sent, socket closed)")
url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/cut1", "ContentLength": 100 * MiB}, ExpiresIn=120)
print("  ", raw_put(url, {"Content-Length": str(100 * MiB)}, (b"x" * MiB for _ in range(10)), close_early=True))
for w in (1, 5, 15):
    time.sleep(w if w == 1 else w - (1 if w == 5 else 5)); print(f"   after ~{w}s visible:", exists("staging/cut1"))
print("  same with an existing object at the key (does the interrupted PUT damage it?)")
s.put_object(Bucket=B, Key="staging/cut2", Body=b"old" * 10) if False else u.put_object(Bucket=B, Key="staging/cut2", Body=b"old" * 10)
url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/cut2", "ContentLength": 100 * MiB}, ExpiresIn=120)
print("  ", raw_put(url, {"Content-Length": str(100 * MiB)}, (b"x" * MiB for _ in range(10)), close_early=True))
time.sleep(3); print("   cut2 after 3s:", exists("staging/cut2"))
print("## 3 chunked bodies")
url0 = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/chunk1"}, ExpiresIn=120)
print("  plain HTTP chunked, presigned without CL ->", raw_put(url0, {"Transfer-Encoding": "chunked"}, [b"400\r\n" + b"c" * 1024 + b"\r\n", b"0\r\n\r\n"]), exists("staging/chunk1"))
url0 = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": "staging/chunk2"}, ExpiresIn=120)
print("  chunked, interrupted mid-body ->", raw_put(url0, {"Transfer-Encoding": "chunked"}, [b"100000\r\n" + b"c" * MiB + b"\r\n"] * 5, close_early=True)); time.sleep(3); print("   chunk2 after 3s:", exists("staging/chunk2"))
print("## 4 CopyObject immutability")
s.put_object(Bucket=B, Key="users/u/projects/p/src/orig", Body=b"ORIGINAL-" * 1000)
s.copy_object(Bucket=B, Key="users/u/projects/p/cand/copy", CopySource=f"{B}/users/u/projects/p/src/orig")
h = lambda k: hashlib.sha256(s.get_object(Bucket=B, Key=k)["Body"].read()).hexdigest()[:16]
print("  copy sha", h("users/u/projects/p/cand/copy"))
s.put_object(Bucket=B, Key="users/u/projects/p/src/orig", Body=b"CHANGED!-" * 1000)
print("  after overwriting source: source", h("users/u/projects/p/src/orig"), "copy", h("users/u/projects/p/cand/copy"))
s.delete_object(Bucket=B, Key="users/u/projects/p/src/orig")
print("  after deleting source: copy", h("users/u/projects/p/cand/copy"), "source", exists("users/u/projects/p/src/orig"))
print("## 5 CopyObject 500 MiB timing")
path = "/tmp/big500"
if not os.path.exists(path):
    with open(path, "wb") as f:
        for _ in range(500): f.write(os.urandom(MiB))
src_sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
for mode in ("single PUT", "multipart 8 MiB"):
    key = f"staging/big-{mode.split()[0]}"
    t0 = time.time()
    if mode == "single PUT":
        url = u.generate_presigned_url("put_object", Params={"Bucket": B, "Key": key, "ContentLength": 500 * MiB}, ExpiresIn=600)
        with open(path, "rb") as f: r = requests.put(url, data=f, headers={"Content-Length": str(500 * MiB)}, verify=CA)
        st = r.status_code
    else:
        from boto3.s3.transfer import TransferConfig
        adm.upload_file(path, B, key, Config=TransferConfig(multipart_threshold=8 * MiB, multipart_chunksize=8 * MiB)); st = "ok"
    print(f"  upload {mode}: {st} in {time.time() - t0:.2f}s")
    for i in range(3):
        dst = f"users/u/projects/p/cand/{key.split('/')[-1]}-{i}"
        t0 = time.time(); s.copy_object(Bucket=B, Key=dst, CopySource=f"{B}/{key}"); dt = time.time() - t0
        print(f"   copy #{i+1}: {dt*1000:.0f} ms")
    t0 = time.time(); d = hashlib.sha256(s.get_object(Bucket=B, Key=dst)["Body"].read()).hexdigest()
    print(f"   copy sha matches: {d == src_sha} (read in {time.time()-t0:.1f}s)")
    adm.delete_object(Bucket=B, Key=key)
    print(f"   after deleting staging source, copy still readable: {hashlib.sha256(s.get_object(Bucket=B, Key=dst)['Body'].read()).hexdigest() == src_sha}")
