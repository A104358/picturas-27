"""B1 acceptance smoke: the stack works with the mounted secrets, and the old committed secrets do not.

Usage: python3 tests/conformance/mtls-pki/b1-smoke.py [base_url] [ca_file]
  base_url defaults to https://localhost:8080; ca_file is the installation CA
  ($PICTURAS_SECRETS_DIR/pki/ca/ca.crt), used to verify the nginx certificate.
Only the standard library is needed. Tokens and signed URLs are never printed.
"""
import base64
import hashlib
import json
import os
import ssl
import struct
import sys
import time
import urllib.error
import urllib.request
import uuid
import zlib

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://localhost:8080").rstrip("/")
CA = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.environ.get("PICTURAS_SECRETS_DIR", ""), "pki/ca/ca.crt")
CTX = ssl.create_default_context(cafile=CA)  # the nginx certificate must verify against the local CA
API = BASE + "/api-gateway/"
results = []


def call(method, path, token=None, body=None, headers=None, raw=None, ctype=None):
    h = dict(headers or {})
    if token:
        h["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    elif raw is not None:
        data, h["Content-Type"] = raw, ctype
    req = urllib.request.Request(API + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
            payload = r.read()
            return r.status, dict(r.headers), payload
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'ok  ' if ok else 'FAIL'} {name}{(' — ' + detail) if detail else ''}")


def png(w=64, h=64, rgb=(40, 120, 200)):
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def multipart(field, name, data, ctype):
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + data + f"\r\n--{b}--\r\n".encode()
    return body, f"multipart/form-data; boundary={b}"


def version(uid, pid, tok):
    s, _, b = call("GET", f"projects/{uid}/{pid}", tok)
    return str(json.loads(b).get("version", 0)) if s == 200 else "0"


# 1. account and session (HS256 secret from the secrets directory)
email, pw = f"b1-{uuid.uuid4().hex[:10]}@example.invalid", uuid.uuid4().hex
s, _, b = call("POST", "users/", body={"name": "b1", "email": email, "password": pw, "type": "free"})
check("register (users, field encryption key from secrets)", s == 201, f"HTTP {s}")
user = json.loads(b)["user"]; uid = user["_id"]
s, _, b = call("POST", f"users/{email}/login", body={"password": pw})
tok = json.loads(b).get("jwt") if s in (200, 201) else None
check("login returns a session token", bool(tok), f"HTTP {s}")

# 2. a token signed with the formerly committed secret is refused
def hs256(secret, payload):
    enc = lambda d: base64.urlsafe_b64encode(json.dumps(d, separators=(",", ":")).encode()).rstrip(b"=")
    msg = enc({"alg": "HS256", "typ": "JWT"}) + b"." + enc(payload)
    import hmac
    sig = base64.urlsafe_b64encode(hmac.new(secret.encode(), msg, hashlib.sha256).digest()).rstrip(b"=")
    return (msg + b"." + sig).decode()
forged = hs256("lisan_al_gaib", {"_id": uid, "id": uid, "email": email, "type": "premium", "exp": int(time.time()) + 600})
s, _, _ = call("GET", f"projects/{uid}", forged)
check("token signed with the old committed secret is refused", s in (401, 403), f"HTTP {s}")
s, _, _ = call("GET", f"projects/{uid}", tok)
check("token from login is accepted", s == 200, f"HTTP {s}")

# 3. project, image upload (projects -> img_storage -> SeaweedFS with the new S3 credential)
s, _, b = call("POST", f"projects/{uid}", tok, body={"name": "b1-smoke"})
check("create project", s == 201, f"HTTP {s}")
pid = json.loads(b)["_id"]
data = png()
body, ct = multipart("image", "b1.png", data, "image/png")
s, h, _ = call("POST", f"projects/{uid}/{pid}/img", tok, raw=body, ctype=ct, headers={"X-Project-Version": version(uid, pid, tok)})
check("upload image (img_storage uses the S3 credential from secrets)", s in (200, 201, 204), f"HTTP {s}")
s, _, b = call("GET", f"projects/{uid}/{pid}/imgs", tok)
imgs = json.loads(b) if s == 200 else []
img_id = (imgs[0].get("_id") if imgs else None)
check("image listed", bool(img_id), f"HTTP {s}, {len(imgs)} item(s)")
s, _, b = call("GET", f"projects/{uid}/{pid}/img/{img_id}", tok)
url = json.loads(b).get("url") if s == 200 else None
ok = False
if url:
    with urllib.request.urlopen(urllib.request.Request(url), context=CTX, timeout=30) as r:
        ok = hashlib.sha256(r.read()).hexdigest() == hashlib.sha256(data).hexdigest()
check("original downloaded through the signed /s3/ URL with the same SHA-256", ok)

# 4. pipeline: brightness, apply (projects -> RabbitMQ -> brightness_tool with the broker credential)
s, _, _ = call("POST", f"projects/{uid}/{pid}/tool", tok, body={"procedure": "brightness", "params": {"brightness": 1.4}},
               headers={"X-Project-Version": version(uid, pid, tok)})
check("add brightness tool", s in (200, 201, 204), f"HTTP {s}")
s, _, _ = call("POST", f"projects/{uid}/{pid}/process", tok, body={}, headers={"X-Project-Version": version(uid, pid, tok)})
check("apply pipeline", s in (200, 201, 202, 204), f"HTTP {s}")
done, res_url = False, None
for _ in range(60):
    s, _, b = call("GET", f"projects/{uid}/{pid}/process/url", tok)
    if s == 200:
        j = json.loads(b)
        items = j if isinstance(j, list) else j.get("imgs") or j.get("results") or []
        if items:
            res_url = items[0].get("url"); done = True; break
    time.sleep(2)
check("result produced by the worker (broker credential from secrets)", done, f"last HTTP {s}")
if res_url:
    with urllib.request.urlopen(urllib.request.Request(res_url), context=CTX, timeout=30) as r:
        out = r.read()
    check("result differs from the original (brightness applied)", out[:8] == b"\x89PNG\r\n\x1a\n" and out != data)

print(f"B1 smoke: {sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
