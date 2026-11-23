"""B4 owner, share, account, subscription and direct-service checks.

Only synthetic data is created. Tokens and share identifiers are never printed.
"""
import os
import secrets
import socket
import ssl
import uuid
from pathlib import Path

import requests

base = "https://localhost:8080/api-gateway/"
ca = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/ca/ca.crt")
http = requests.Session()
http.trust_env = False


def call(method, path, token=None, *, body=None, headers=None):
    hdr = dict(headers or {})
    if token:
        hdr["Authorization"] = "Bearer " + token
    return http.request(method, base + path, json=body, headers=hdr, verify=ca, timeout=30)


def account(kind="free"):
    email = f"b4-{uuid.uuid4().hex}@example.invalid"
    password = secrets.token_urlsafe(24)
    response = call("POST", "users/", body={"name": "B4 fixture", "email": email,
                                            "password": password, "type": kind})
    assert response.status_code == 201, ("register", response.status_code)
    data = response.json()
    return data["user"]["_id"], data["jwt"]


owner, owner_token = account()
guest, guest_token = account()
response = call("POST", f"projects/{owner}", owner_token, body={"name": "B4 fixture"})
assert response.status_code == 201, ("project", response.status_code)
project = response.json()["_id"]
path = f"projects/{owner}/{project}"

response = call("GET", path, owner_token)
assert response.status_code == 200, ("owner read", response.status_code)
version = str(response.json()["version"])

assert call("GET", path, guest_token).status_code == 403
assert call("GET", f"{path}?owner={owner}", guest_token).status_code == 403
assert call("GET", f"{path}?owner={guest}", owner_token).status_code == 403
assert call("GET", f"{path}?owner={owner}&owner={owner}", owner_token).status_code == 403
assert call("GET", f"{path}?owner={owner}", owner_token).status_code == 200

response = call("POST", f"{path}/share", owner_token, body={"permission": "edit"},
                headers={"X-Project-Version": version})
assert response.status_code == 201, ("share", response.status_code)
share = response.json()["id"]
shared_path = f"{path}?owner={owner}&share={share}"
assert call("GET", shared_path, guest_token).status_code == 200
assert call("DELETE", shared_path, guest_token,
            headers={"X-Project-Version": str(response.headers["X-Project-Version"])}).status_code == 403
assert call("GET", f"{path}?owner={guest}&share={share}", guest_token).status_code == 403
assert call("GET", f"{path}?owner={owner}&share={share}&share={share}", guest_token).status_code == 403

version = str(response.headers["X-Project-Version"])
response = call("POST", f"{path}/share", owner_token, body={"permission": "read"},
                headers={"X-Project-Version": version})
assert response.status_code == 201, ("read share", response.status_code)
read_share = response.json()["id"]
version = str(response.headers["X-Project-Version"])
tool = {"procedure": "brightness", "params": {"brightness": 1.1}}
assert call("POST", f"{path}/tool?owner={owner}&share={read_share}", guest_token,
            body=tool, headers={"X-Project-Version": version}).status_code == 403
response = call("POST", f"{path}/tool?owner={owner}&share={share}", guest_token,
                body=tool, headers={"X-Project-Version": version})
assert response.status_code == 201, ("edit share mutation", response.status_code)

assert call("GET", f"users/{owner}", guest_token).status_code == 403
assert call("PUT", f"users/{guest}", guest_token, body={"type": "premium"}).status_code == 403
assert call("GET", f"users/{guest}", guest_token).json()["type"] == "free"
assert call("GET", f"subscriptions/{owner}", guest_token).status_code == 403
assert call("POST", "subscriptions/", guest_token,
            body={"subscription": {"user_id": owner}, "card": {}}).status_code == 403
assert call("POST", "users/", body={"type": "premium"}).status_code == 403

card = {"cardHolderName": "B4 Fixture", "cardNumber": "4242424242424242",
        "expiryMonth": "12", "expiryYear": "29", "cvc": 123}
response = call("POST", "subscriptions/", guest_token,
                body={"subscription": {"user_id": guest, "interval": 1}, "card": card})
assert response.status_code == 200, ("subscribe", response.status_code)
assert call("GET", f"users/{guest}", guest_token).json()["type"] == "premium"
response = call("PUT", f"subscriptions/{guest}/cancel", guest_token, body={})
assert response.status_code == 200, ("cancel", response.status_code)
assert call("GET", f"users/{guest}", guest_token).json()["type"] == "free"

context = ssl.create_default_context(cafile=ca)
for name, port in (("projects", 9002), ("users", 10001),
                   ("subscriptions", 11001), ("img_storage", 11000)):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as raw:
        with context.wrap_socket(raw, server_hostname=name) as tls:
            try:
                tls.sendall(b"GET / HTTP/1.1\r\nHost: " + name.encode() + b"\r\n\r\n")
                data = tls.recv(64)
            except ssl.SSLError:
                continue
            assert not data.startswith(b"HTTP/1.1 2"), ("direct service", name)

print("B4: owner/share/D7, profile isolation, premium lifecycle and direct services passed")
