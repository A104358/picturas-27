"""B7 public video upload: early refusal, one-use PUT, confirmation and replay."""
import os
from concurrent.futures import ThreadPoolExecutor
import secrets
import time
import uuid
from pathlib import Path

import requests

root = Path(__file__).resolve().parents[3]
base = os.environ.get("B4_BASE_URL", "https://localhost:8080").rstrip("/") + "/api-gateway/"
ca = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/ca/ca.crt")
sample = root / "samples/video/sample_10s_720p.mp4"
session = requests.Session()
session.trust_env = False


def call(method, path, token=None, **kwargs):
    headers = dict(kwargs.pop("headers", {}))
    if token:
        headers["Authorization"] = "Bearer " + token
    return session.request(method, base + path, headers=headers, verify=ca, timeout=100, **kwargs)


def account():
    response = call("POST", "users/", json={
        "name": "B7 fixture", "email": f"b7-{uuid.uuid4().hex}@example.invalid",
        "password": secrets.token_urlsafe(24), "type": "free",
    })
    assert response.status_code == 201, response.status_code
    return response.json()["user"]["_id"], response.json()["jwt"]


def request_upload(path, token, metadata, version):
    for _ in range(30):
        response = call("POST", path, token, json=metadata,
                        headers={"X-Project-Version": str(version)})
        if response.status_code != 429:
            return response
        time.sleep(1)  # Successful uploads retain a slot until the hash finishes.
    return response


owner, jwt = account()
other, other_jwt = account()
response = call("POST", f"projects/{owner}", jwt, json={"name": "B7 fixture"})
assert response.status_code == 201, response.status_code
project = f"projects/{owner}/{response.json()['_id']}"
version = call("GET", project, jwt).json()["version"]
meta = {"name": "direct.mp4", "size": sample.stat().st_size, "type": "video/mp4",
        "duration": 10, "width": 1280, "height": 720}
start_path = project + "/video/uploads"
assert call("POST", start_path, json=meta, headers={"X-Project-Version": str(version)}).status_code == 401
assert call("POST", start_path, jwt, json={**meta, "size": 101 * 1024 * 1024},
            headers={"X-Project-Version": str(version)}).status_code == 413
assert call("POST", start_path, jwt, json={**meta, "duration": 90},
            headers={"X-Project-Version": str(version)}).status_code == 400
print("PASS request auth and free size limit")

response = request_upload(start_path, jwt, meta, version)
assert response.status_code == 201, (response.status_code, response.text[:120])
ticket = response.json()
assert len(ticket["token"]) == 64
put_path = ticket["uploadUrl"].removeprefix("/api-gateway/")
assert call("PUT", put_path, data=b"x" * 1024, headers={"Content-Type": "video/mp4"}).status_code == 401
assert call("PUT", put_path, other_jwt, data=b"x" * 1024,
            headers={"Content-Type": "video/mp4"}).status_code == 404
assert call("PUT", put_path, jwt, data=b"x" * 1024,
            headers={"Content-Type": "video/mp4"}).status_code == 413
assert call("PUT", put_path, jwt, data=(chunk for chunk in [b"x" * 1024]),
            headers={"Content-Type": "video/mp4"}).status_code == 411
assert call("PUT", put_path, jwt, data=b"x" * meta["size"],
            headers={"Content-Type": "video/webm"}).status_code == 400
assert call("POST", start_path + f"/{ticket['token']}/confirm", jwt).status_code == 409
assert call("POST", f"projects/{other}/{project.rsplit('/', 1)[-1]}/video/uploads/{ticket['token']}/confirm",
            other_jwt).status_code == 404
with sample.open("rb") as file:
    response = call("PUT", put_path, jwt, data=file,
                    headers={"Content-Length": str(meta["size"]), "Content-Type": "video/mp4"})
assert response.status_code in (200, 201, 204), (response.status_code, response.text[:120])
print("PASS early PUT refusal and direct transfer")
with sample.open("rb") as file:
    response = call("PUT", put_path, jwt, data=file,
                    headers={"Content-Length": str(meta["size"]), "Content-Type": "video/mp4"})
assert response.status_code == 409, response.status_code
response = call("POST", start_path + f"/{ticket['token']}/confirm", jwt)
assert response.status_code == 204, (response.status_code, response.text[:120])
assert int(response.headers["X-Project-Version"]) == version + 1
assert call("POST", start_path + f"/{ticket['token']}/confirm", jwt).status_code == 204
assert len(call("GET", project, jwt).json()["imgs"]) == 1
print("PASS one-use token, commit and idempotent confirmation")

version += 1
cancel = request_upload(start_path, jwt, {**meta, "name": "cancel-before-put.mp4"}, version)
assert cancel.status_code == 201, cancel.status_code
cancel_token = cancel.json()["token"]
assert call("POST", start_path + f"/{cancel_token}/cancel", jwt).status_code == 204
assert call("PUT", cancel.json()["uploadUrl"].removeprefix("/api-gateway/"), jwt,
            data=b"x" * 1024, headers={"Content-Type": "video/mp4"}).status_code == 410
print("PASS cancellation before PUT frees the attempt")

cancel = request_upload(start_path, jwt, {**meta, "name": "cancel-after-put.mp4"}, version)
assert cancel.status_code == 201, cancel.status_code
with sample.open("rb") as file:
    put = call("PUT", cancel.json()["uploadUrl"].removeprefix("/api-gateway/"), jwt,
               data=file, headers={"Content-Length": str(meta["size"]), "Content-Type": "video/mp4"})
assert put.status_code in (200, 201, 204), put.status_code
cancel_token = cancel.json()["token"]
assert call("POST", start_path + f"/{cancel_token}/cancel", jwt).status_code == 204
assert call("POST", start_path + f"/{cancel_token}/confirm", jwt).status_code == 410
assert len(call("GET", project, jwt).json()["imgs"]) == 1
print("PASS cancellation after PUT prevents publication")

parallel = request_upload(start_path, jwt, {**meta, "name": "concurrent.mp4"}, version)
assert parallel.status_code == 201, parallel.status_code


def send_parallel(_):
    client = requests.Session()
    client.trust_env = False
    with sample.open("rb") as file:
        return client.put("https://localhost:8080" + parallel.json()["uploadUrl"], data=file,
                          headers={"Authorization": "Bearer " + jwt,
                                   "Content-Length": str(meta["size"]), "Content-Type": "video/mp4"},
                          verify=ca, timeout=90).status_code


with ThreadPoolExecutor(max_workers=2) as pool:
    statuses = sorted(pool.map(send_parallel, range(2)))
assert statuses in ([200, 409], [201, 409], [204, 409]), statuses
parallel_token = parallel.json()["token"]
assert call("POST", start_path + f"/{parallel_token}/confirm", jwt).status_code == 204
assert len(call("GET", project, jwt).json()["imgs"]) == 2
print("PASS concurrent PUT claim has one winner")
