"""B6 capacity: sequential premium 100 MiB uploads (corpus file T), one interrupted mid-body.

Reproduces the premium-100 HTTP 400 of the full EXP (SeaweedFS out of volumes) and proves
that, after the fix (D-22), the storage keeps accepting uploads past the old ~7 GiB ceiling,
that an interrupted upload releases its slot, and that a server-side storage failure is not
answered as a validation error (400).

Usage: B6_CAPACITY_UPLOADS=<n> python b6-capacity.py [state-file]
With a state file, a second run reuses the same premium account and project (to upload again
after restarting services).
"""
import json
import os
import secrets
import sys
import time
import uuid
from pathlib import Path

import requests

base = os.environ.get("B4_BASE_URL", "https://localhost:8080").rstrip("/") + "/api-gateway/"
ca = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/ca/ca.crt")
corpus = Path(__file__).resolve().parents[3] / "evaluation/.corpus"
sample = corpus / os.environ.get("B6_CAPACITY_FILE", "pad_100MiB_T.mp4")
count = int(os.environ.get("B6_CAPACITY_UPLOADS", "10"))
state_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
http = requests.Session()
http.trust_env = False
failures = 0


def call(method, path, token=None, **kwargs):
    headers = dict(kwargs.pop("headers", {}))
    if token:
        headers["Authorization"] = "Bearer " + token
    return http.request(method, base + path, headers=headers, verify=ca,
                        timeout=kwargs.pop("timeout", 300), **kwargs)


def check(name, ok, detail=""):
    global failures
    print(("PASS " if ok else "FAIL ") + name + (f" ({detail})" if detail else ""), flush=True)
    failures += 0 if ok else 1


def premium_project():
    if state_file and state_file.exists():
        state = json.loads(state_file.read_text())
        return state["user"], state["token"], state["path"]
    response = call("POST", "users/", json={
        "name": "B6 capacity", "email": f"b6-cap-{uuid.uuid4().hex}@example.invalid",
        "password": secrets.token_urlsafe(24), "type": "free"})
    assert response.status_code == 201, ("register", response.status_code)
    user, token = response.json()["user"]["_id"], response.json()["jwt"]
    card = {"cardHolderName": "B6 Fixture", "cardNumber": "4242424242424242",
            "expiryMonth": "12", "expiryYear": "29", "cvc": 123}
    response = call("POST", "subscriptions/", token,
                    json={"subscription": {"user_id": user, "interval": 1}, "card": card})
    assert response.status_code == 200, ("subscribe", response.status_code)
    response = call("POST", f"projects/{user}", token, json={"name": "B6 capacity"})
    assert response.status_code == 201, ("project", response.status_code)
    path = f"projects/{user}/{response.json()['_id']}"
    if state_file:
        state_file.write_text(json.dumps({"user": user, "token": token, "path": path}))
    return user, token, path


def body(name, stop_after=None, stall_s=0):
    boundary = "b6cap" + uuid.uuid4().hex
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"video\"; "
            f"filename=\"{name}\"\r\nContent-Type: video/mp4\r\n\r\n").encode()
    tail = f"\r\n--{boundary}--\r\n".encode()

    def chunks():
        yield head
        sent = 0
        with sample.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                yield chunk
                sent += len(chunk)
                if stop_after is not None and sent >= stop_after:
                    if stall_s:
                        time.sleep(stall_s)  # connection open, no data: server idle limit (30 s)
                    raise ConnectionAbortedError("client interrupts the upload")
        yield tail
    length = len(head) + sample.stat().st_size + len(tail)
    return Sized(chunks(), length), length, f"multipart/form-data; boundary={boundary}"


class Sized:
    """Iterable body with a known length, so requests sends Content-Length, not chunked."""

    def __init__(self, iterator, length):
        self.iterator, self.len = iterator, length

    def __iter__(self):
        return self.iterator


def upload(token, path, version, name, stop_after=None, stall_s=0):
    data, length, content_type = body(name, stop_after, stall_s)
    started = time.monotonic()
    response = call("POST", path + "/video", token, data=data, headers={
        "X-Project-Version": str(version), "Content-Type": content_type})
    return response, (time.monotonic() - started) * 1000


user, token, path = premium_project()
version = call("GET", path, token).json()["version"]
run = uuid.uuid4().hex[:6]
accepted = 0
refusals = 0
for n in range(1, count + 1):
    for _ in range(30):  # 3 slots stay held until the background hash (UP-C5): back off on 429
        response, ms = upload(token, path, version, f"cap-{run}-{n}.mp4")
        if response.status_code != 429:
            break
        refusals += 1
        time.sleep(1)
    ok = response.status_code == 204
    check(f"upload {n}/{count} premium 100 MiB T", ok,
          f"HTTP {response.status_code} {ms:.0f} ms" + ("" if ok else f" body={response.text[:80]}"))
    if not ok:
        check("storage failure is not a validation error", response.status_code != 400,
              f"HTTP {response.status_code}")
        break
    accepted += 1
    version = int(response.headers["X-Project-Version"])

if os.environ.get("B6_CAPACITY_INTERRUPT", "1") == "1" and failures == 0:
    # Three aborted bodies and one stalled body (> 30 s without data). With 3 global slots, a
    # leaked slot per interruption would leave none for the upload that follows.
    cases = [("aborted", 0)] * 3 + [("stalled", 40)]
    for k, (kind, stall) in enumerate(cases, 1):
        try:
            response, _ = upload(token, path, version, f"cap-{run}-{kind}-{k}.mp4",
                                 stop_after=40 * 1024 * 1024, stall_s=stall)
            check(f"{kind} upload {k} not accepted", response.status_code != 204,
                  f"HTTP {response.status_code}")
        except requests.exceptions.RequestException as error:
            check(f"{kind} upload {k} ended without a server answer", True, type(error).__name__)
    project = call("GET", path, token).json()
    check("interrupted uploads published nothing",
          not any("-aborted-" in i.get("og_uri", "") or "-stalled-" in i.get("og_uri", "")
                  for i in project["imgs"]) and project["version"] == version)
    # Every interrupted attempt must be failed and its slot released within seconds (cleanup
    # runs every 5 s); then all 3 global slots admit 3 simultaneous uploads, with no retry.
    time.sleep(8)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(3) as pool:
        results = list(pool.map(lambda k: upload(token, path, version, f"cap-{run}-after-{k}.mp4"),
                                range(1, 4)))
    statuses = sorted(r.status_code for r, _ in results)
    # Same expected version for all three: one commits (204), the others conflict (409);
    # a 429 means a slot was still held by an interrupted attempt.
    check("3 simultaneous uploads after the interruptions admitted (all slots free)",
          429 not in statuses and statuses.count(204) == 1, f"HTTP {statuses}")
    accepted += statuses.count(204)

print(f"slot refusals (429, retried): {refusals}")
print(f"accepted {accepted} uploads; project media {len(call('GET', path, token).json()['imgs'])}")
print("RESULT", "PASS" if failures == 0 else f"FAIL ({failures})")
sys.exit(1 if failures else 0)
