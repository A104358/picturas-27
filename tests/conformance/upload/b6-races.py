"""B6: competing commits and a client disconnect during a streamed upload."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import http.client
import os
import secrets
import ssl
import time
import uuid

import requests

base = os.environ.get("B4_BASE_URL", "https://localhost:8080").rstrip("/") + "/api-gateway/"
ca = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/ca/ca.crt")
sample = Path(__file__).resolve().parents[3] / "samples/video/sample_10s_720p.mp4"
session = requests.Session()
session.trust_env = False


def call(method, path, token=None, **kwargs):
    headers = dict(kwargs.pop("headers", {}))
    if token:
        headers["Authorization"] = "Bearer " + token
    return session.request(method, base + path, headers=headers, verify=ca, timeout=90, **kwargs)


response = call("POST", "users/", json={
    "name": "B6 race fixture", "email": f"race-{uuid.uuid4().hex}@example.invalid",
    "password": secrets.token_urlsafe(24), "type": "free",
})
assert response.status_code == 201
user, token = response.json()["user"]["_id"], response.json()["jwt"]
response = call("POST", f"projects/{user}", token, json={"name": "B6 competing commits"})
assert response.status_code == 201
project_path = f"projects/{user}/{response.json()['_id']}"
version = call("GET", project_path, token).json()["version"]


def upload(name, expected=version):
    with sample.open("rb") as file:
        return call("POST", project_path + "/video", token,
                    headers={"X-Project-Version": str(expected)},
                    files={"video": (name, file, "video/mp4")}).status_code


# The 3 global slots stay held until each upload's background hash ends (UP-C5): let the
# uploads of a suite run just before this one finish, so both racers are admitted.
time.sleep(8)
with ThreadPoolExecutor(max_workers=2) as pool:
    statuses = sorted(pool.map(upload, ("race-one.mp4", "race-two.mp4")))
assert statuses == [204, 409], statuses
project = call("GET", project_path, token).json()
assert len(project["imgs"]) == 1 and project["version"] == version + 1
print("PASS simultaneous uploads publish exactly one media and one version")

# Send a declared multipart body only partway, then disconnect. It must leave no
# visible media and release its working slot after reconciliation.
boundary = "----b6" + uuid.uuid4().hex
name = "interrupted.mp4"
head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"video\"; "
        f"filename=\"{name}\"\r\nContent-Type: video/mp4\r\n\r\n").encode()
body_size = sample.stat().st_size
tail = f"\r\n--{boundary}--\r\n".encode()
ctx = ssl.create_default_context(cafile=ca)
conn = http.client.HTTPSConnection("localhost", 8080, context=ctx, timeout=20)
conn.putrequest("POST", f"/api-gateway/{project_path}/video")
conn.putheader("Authorization", "Bearer " + token)
conn.putheader("X-Project-Version", str(project["version"]))
conn.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
conn.putheader("Content-Length", str(len(head) + body_size + len(tail)))
conn.endheaders()
with sample.open("rb") as file:
    conn.send(head + file.read(65536))
time.sleep(2)
conn.close()
time.sleep(12)
project = call("GET", project_path, token).json()
assert len(project["imgs"]) == 1
assert upload("after-interruption.mp4", project["version"]) == 204
print("PASS interrupted body leaves no media and a later upload succeeds")
