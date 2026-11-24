"""B6 legacy adapter: early authorisation, streamed validation, commit and hash."""
import os
import hashlib
import secrets
import time
import uuid
from pathlib import Path

import requests

base = os.environ.get("B4_BASE_URL", "https://localhost:8080").rstrip("/") + "/api-gateway/"
ca = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/ca/ca.crt")
sample = Path(__file__).resolve().parents[3] / "samples/video/sample_10s_720p.mp4"
http = requests.Session()
http.trust_env = False


def call(method, path, token=None, **kwargs):
    headers = dict(kwargs.pop("headers", {}))
    if token:
        headers["Authorization"] = "Bearer " + token
    return http.request(method, base + path, headers=headers, verify=ca, timeout=90, **kwargs)


def account():
    response = call("POST", "users/", json={
        "name": "B6 fixture", "email": f"b6-{uuid.uuid4().hex}@example.invalid",
        "password": secrets.token_urlsafe(24), "type": "free",
    })
    assert response.status_code == 201, ("register", response.status_code)
    return response.json()["user"]["_id"], response.json()["jwt"]


def upload(path, token, version, file_name, *, content=None, query=""):
    with sample.open("rb") as input_file:
        return call("POST", path + "/video" + query, token,
                    headers={"X-Project-Version": str(version)},
                    files={"video": (file_name, content if content is not None else input_file,
                                     "video/mp4")})


owner, owner_token = account()
editor, editor_token = account()
assert call("GET", f"users/{owner}", owner_token).json()["remaining_operations"] == 5
response = call("POST", f"projects/{owner}", owner_token, json={"name": "B6 fixture"})
assert response.status_code == 201, ("project", response.status_code)
path = f"projects/{owner}/{response.json()['_id']}"
version = call("GET", path, owner_token).json()["version"]

assert upload(path, None, version, "first.mp4").status_code == 401
print("PASS unauthenticated upload refused")
assert upload(path, editor_token, version, "first.mp4").status_code == 403
print("PASS another account refused")
response = upload(path, owner_token, version, "first.mp4", content=b"not a video")
assert response.status_code == 400, ("invalid video", response.status_code)
assert not call("GET", path, owner_token).json()["imgs"]
print("PASS invalid video leaves no media")

response = upload(path, owner_token, version, "first.mp4")
assert response.status_code == 204, ("valid video", response.status_code, response.text[:120])
assert int(response.headers["X-Project-Version"]) == version + 1
project = call("GET", path, owner_token).json()
assert len(project["imgs"]) == 1 and project["imgs"][0]["media_type"] == "video"
print("PASS video committed once with project version")

assert upload(path, owner_token, version, "stale.mp4").status_code == 409
assert len(call("GET", path, owner_token).json()["imgs"]) == 1
print("PASS stale project version refused without a second media")

download_url = project["imgs"][0]["url"]
if base.startswith("https://nginx/"):
    download_url = download_url.replace("https://localhost:8080/", "https://nginx/")
download = http.get(download_url, verify=ca, timeout=30)
assert download.status_code == 200
assert hashlib.sha256(download.content).digest() == hashlib.sha256(sample.read_bytes()).digest()
print("PASS stored original retains its bytes")

version = project["version"]
assert upload(path, owner_token, version, "first.mp4").status_code == 400
print("PASS duplicate name refused")
response = call("POST", path + "/share", owner_token,
                headers={"X-Project-Version": str(version)}, json={"permission": "read"})
assert response.status_code == 201
read_link = response.json()["id"]
version = int(response.headers["X-Project-Version"])
assert upload(path, editor_token, version, "reader.mp4",
              query=f"?owner={owner}&share={read_link}").status_code == 403
print("PASS read share refused")
response = call("POST", path + "/share", owner_token,
                headers={"X-Project-Version": str(version)}, json={"permission": "edit"})
assert response.status_code == 201
edit_link = response.json()["id"]
version = int(response.headers["X-Project-Version"])
response = upload(path, editor_token, version, "editor.mp4",
                  query=f"?owner={owner}&share={edit_link}")
assert response.status_code == 204, ("edit share", response.status_code, response.text[:120])
print("PASS edit share accepted")

quota_user, quota_token = account()
response = call("POST", f"projects/{quota_user}", quota_token, json={"name": "B6 quota fixture"})
assert response.status_code == 201
quota_path = f"projects/{quota_user}/{response.json()['_id']}"
client_cert = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/services/projects/service.crt")
client_key = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/services/projects/service.key")
reserved = http.get(f"https://users:10001/{quota_user}/process/5",
                    cert=(client_cert, client_key), verify=ca, timeout=30)
assert reserved.status_code == 200
assert call("GET", f"users/{quota_user}", quota_token).json()["remaining_operations"] == 0
quota_version = call("GET", quota_path, quota_token).json()["version"]
assert upload(quota_path, quota_token, quota_version, "zero-balance.mp4").status_code == 204
assert call("GET", f"users/{quota_user}", quota_token).json()["remaining_operations"] == 0
print("PASS free upload at zero quota neither refused nor charged")

anonymous = call("POST", "users/", json={"type": "anonymous"})
assert anonymous.status_code == 201
anon_user, anon_token = anonymous.json()["user"]["_id"], anonymous.json()["jwt"]
response = call("POST", f"projects/{anon_user}", anon_token, json={"name": "B6 anonymous"})
assert response.status_code == 201
anon_path = f"projects/{anon_user}/{response.json()['_id']}"
anon_version = call("GET", anon_path, anon_token).json()["version"]
assert upload(anon_path, anon_token, anon_version, "anon.mp4").status_code == 403
print("PASS anonymous video upload refused")

premium_user, premium_token = account()
card = {"cardHolderName": "B6 Fixture", "cardNumber": "4242424242424242",
        "expiryMonth": "12", "expiryYear": "29", "cvc": 123}
response = call("POST", "subscriptions/", premium_token,
                json={"subscription": {"user_id": premium_user, "interval": 1}, "card": card})
assert response.status_code == 200
response = call("POST", f"projects/{premium_user}", premium_token, json={"name": "B6 premium"})
assert response.status_code == 201
premium_path = f"projects/{premium_user}/{response.json()['_id']}"
premium_version = call("GET", premium_path, premium_token).json()["version"]
for _ in range(10):
    premium_upload = upload(premium_path, premium_token, premium_version, "premium.mp4")
    if premium_upload.status_code != 429:
        break
    time.sleep(2)
assert premium_upload.status_code == 204, ("premium upload", premium_upload.status_code)
print("PASS premium video upload accepted")
