"""Shared helpers for the B4 conformance tests (identity and HTTP authorisation).

The harness is trusted: it reads the installation CA, service certificates and, to mint
forged or mismatched identities, the HS256 session secret and the RS256 gateway key from
$PICTURAS_SECRETS_DIR. Nothing read from there, and no JWT, share ID or signed URL, is
ever printed; results carry only case IDs, labels and HTTP statuses.

Direct service calls go to the ports still published on the host (127.0.0.1) with the
Docker service name as TLS server name, so the service certificate is fully verified.
After B3 removes those ports, run the same checks from a container on the stack network.
"""
import json
import os
import secrets
import struct
import sys
import time
import uuid
import zlib
from pathlib import Path

import jwt
import requests
import urllib3

ROOT = Path(os.environ["PICTURAS_SECRETS_DIR"])
CA = str(ROOT / "pki/ca/ca.crt")
BASE = os.environ.get("B4_BASE_URL", "https://localhost:8080").rstrip("/") + "/api-gateway/"
PORTS = {
    "projects": int(os.environ.get("B4_PORT_PROJECTS", "9002")),
    "users": int(os.environ.get("B4_PORT_USERS", "10001")),
    "subscriptions": int(os.environ.get("B4_PORT_SUBSCRIPTIONS", "11001")),
    "img_storage": int(os.environ.get("B4_PORT_IMG_STORAGE", "11000")),
}
SESSION_TYP = "picturas-session+jwt"
INTERNAL_TYP = "picturas-internal+jwt"
TLS = "TLS"  # handshake refused: no HTTP exchange happened


def _value(name):
    return (ROOT / "values" / name).read_text().strip()


ISSUER = _value("jwt_issuer")
AUDIENCE = _value("jwt_audience")
SESSION_SECRET = _value("jwt_hs256")
GATEWAY_KEY = (ROOT / "jwt/rs256-private.pem").read_bytes()
GATEWAY_PUBLIC = (ROOT / "jwt/rs256-public.pem").read_bytes()

http = requests.Session()
http.trust_env = False


# --------------------------------------------------------------------------- results
class Results:
    def __init__(self, title):
        self.title, self.rows = title, []

    def check(self, case, label, got, expected):
        """expected: a status, a set of statuses, or a predicate on the status."""
        if callable(expected):
            ok = bool(expected(got))
        elif isinstance(expected, (set, frozenset, tuple, list)):
            ok = got in expected
        else:
            ok = got == expected
        self.rows.append((case, label, got, ok))
        print(f"{'PASS' if ok else 'FAIL'} {case} {label}: {got}", flush=True)
        return ok

    def note(self, case, label):
        self.rows.append((case, label, "-", True))
        print(f"INFO {case} {label}", flush=True)

    def finish(self, required_ids=()):
        failed = [r for r in self.rows if not r[3]]
        seen = {r[0] for r in self.rows}
        missing = sorted(set(required_ids) - seen)
        print(f"{self.title}: {len(self.rows) - len(failed)}/{len(self.rows)} checks passed"
              + (f"; cases without a check: {missing}" if missing else ""))
        if failed or missing:
            sys.exit(1)


def authorised(status):
    """Authorisation passed: the service answered on the domain, not 401/403, and not 5xx."""
    return isinstance(status, int) and status < 500 and status not in (401, 403)


def ok2xx(status):
    return isinstance(status, int) and 200 <= status < 300


# --------------------------------------------------------------------------- public entry
def call(method, path, token=None, *, body=None, headers=None, files=None, data=None,
         query=None, timeout=60):
    hdr = dict(headers or {})
    if token:
        hdr["Authorization"] = "Bearer " + token
    url = BASE + path
    if query:
        url += ("&" if "?" in url else "?") + query
    return http.request(method, url, json=body, files=files, data=data, headers=hdr,
                        verify=CA, timeout=timeout)


def status(method, path, token=None, **kw):
    return call(method, path, token, **kw).status_code


def register(kind="free"):
    email = f"b4-{uuid.uuid4().hex}@example.invalid"
    password = secrets.token_urlsafe(24)
    body = {"name": "B4 fixture", "email": email, "password": password, "type": kind}
    if kind == "anonymous":
        body = {"type": "anonymous"}
    r = call("POST", "users/", body=body)
    assert r.status_code == 201, ("register", kind, r.status_code)
    data = r.json()
    return {"id": data["user"]["_id"], "token": data["jwt"], "email": email, "password": password}


def project_version(owner, project, query=None):
    r = call("GET", f"projects/{owner['id']}/{project}", owner["token"], query=query)
    assert r.status_code == 200, ("version", r.status_code)
    return str(r.json()["version"])


def png_bytes(seed=0):
    width = height = 8
    raw = b"".join(b"\x00" + bytes(v for x in range(width)
                                   for v in ((x * 31 + y * 17 + seed) % 256, (x * 7 + seed) % 256,
                                             (y * 11 + seed) % 256))
                   for y in range(height))

    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


# --------------------------------------------------------------------------- tokens
def session_token(sub, *, secret=None, algorithm="HS256", typ=SESSION_TYP, iss=None, aud=None,
                  iat=None, exp=None, uid=None, drop=(), key=None):
    now = int(time.time())
    claims = {"id": sub if uid is None else uid, "sub": sub, "iss": iss or ISSUER,
              "aud": aud or AUDIENCE, "iat": now if iat is None else iat,
              "exp": now + 3600 if exp is None else exp}
    for name in drop:
        claims.pop(name, None)
    headers = {"typ": typ} if typ else {}
    if algorithm == "none":
        return _unsigned(claims, headers)
    signing = key if key is not None else (secret if secret is not None else SESSION_SECRET)
    if algorithm == "HS256" and isinstance(signing, (bytes, str)) and "BEGIN" in str(signing):
        return hs256_raw(claims, headers, signing if isinstance(signing, bytes) else signing.encode())
    return jwt.encode(claims, signing, algorithm=algorithm, headers=headers)


def internal_token(aud, method, path, sub=None, *, share="", origin=("GET", "/"), typ=INTERNAL_TYP,
                   kid="gateway-1", iss=None, iat=None, exp=None, algorithm="RS256", key=None,
                   public=None, drop=(), extra=None):
    now = int(time.time())
    claims = {"source": "api_gateway", "method": method, "path": path, "share": share,
              "originMethod": origin[0], "originPath": origin[1],
              "requestId": str(uuid.uuid4()), "iat": now if iat is None else iat,
              "exp": now + 30 if exp is None else exp, "aud": aud,
              "iss": iss or f"{ISSUER}/gateway"}
    if sub is not None:
        claims["sub"] = sub
    if public or (public is None and sub is None):
        claims["public"] = True
    claims.update(extra or {})
    for name in drop:
        claims.pop(name, None)
    headers = {k: v for k, v in (("typ", typ), ("kid", kid)) if v}
    if algorithm == "none":
        return _unsigned(claims, headers)
    signing = key if key is not None else GATEWAY_KEY
    if algorithm == "HS256":
        return hs256_raw(claims, headers, signing if isinstance(signing, bytes) else signing.encode())
    return jwt.encode(claims, signing, algorithm=algorithm, headers=headers)


def hs256_raw(claims, headers, key):
    """HS256 over any key bytes (PyJWT refuses PEM keys as HMAC secrets: algorithm confusion)."""
    import base64
    import hashlib
    import hmac

    def part(obj):
        return base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode()).rstrip(b"=").decode()

    signing = part({"alg": "HS256", **headers}) + "." + part(claims)
    mac = hmac.new(key, signing.encode(), hashlib.sha256).digest()
    return signing + "." + base64.urlsafe_b64encode(mac).rstrip(b"=").decode()


def _unsigned(claims, headers):
    import base64

    def part(obj):
        return base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode()).rstrip(b"=").decode()

    return part({"alg": "none", **headers}) + "." + part(claims) + "."


def other_rsa_key():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption())


# --------------------------------------------------------------------------- direct calls
def direct(service, method, path, *, peer=None, token=None, body=None, headers=None,
           query=None, timeout=15, want_body=False):
    """Call a service directly over TLS; peer = service whose client certificate is presented.

    Returns the HTTP status, TLS when the handshake (or the first read after it, with
    TLS 1.3) is refused, or an error tag. Timeouts and other errors are never refusals.
    """
    kw = dict(server_hostname=service, assert_hostname=service, ca_certs=CA,
              cert_reqs="CERT_REQUIRED", retries=False, timeout=urllib3.Timeout(timeout))
    if peer:
        kw.update(cert_file=str(ROOT / f"pki/services/{peer}/service.crt"),
                  key_file=str(ROOT / f"pki/services/{peer}/service.key"))
    pool = urllib3.HTTPSConnectionPool("127.0.0.1", PORTS[service], **kw)
    hdr = dict(headers or {})
    if token:
        hdr["X-Internal-Identity"] = token
    payload = None
    if body is not None:
        payload = json.dumps(body).encode()
        hdr["Content-Type"] = "application/json"
    url = path + (("?" + query) if query else "")
    try:
        r = pool.request(method, url, body=payload, headers=hdr)
        if want_body:
            try:
                return r.status, json.loads(r.data or b"null")
            except ValueError:
                return r.status, None
        return r.status
    except urllib3.exceptions.SSLError:
        return TLS
    except urllib3.exceptions.ProtocolError as exc:
        text = repr(exc).lower()
        if any(k in text for k in ("ssl", "alert", "certificate", "reset", "eof")):
            return TLS
        return "ERROR"
    except (urllib3.exceptions.TimeoutError, TimeoutError):
        return "TIMEOUT"
    finally:
        pool.close()


def matrix_ids():
    import re

    text = (Path(__file__).resolve().parents[2] / "docs/refactor-matriz-rotas.md").read_text()
    return re.findall(r"^\| (B4-R\d{3}) \|", text, re.M)
