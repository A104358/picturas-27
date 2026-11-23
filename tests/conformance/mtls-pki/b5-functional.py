"""B5 functional hops (S09: no legitimate failure). Runs on the stack network
(tests/conformance/in-network.sh <project> mtls-pki/b5-functional.py).

  W1  browser -> nginx -> ws_gateway: Socket.IO over the websocket transport (wss) connects
      with a session and receives the processing events of the user's batch;
  E1  projects -> broker -> expand_ai -> generative-mock: an expand_ai step in generative
      mode (outpainting over mTLS, no fallback in the tool) produces a larger PNG;
  D1  api_gateway -> users -> projects: deleting the account through the public API removes
      the account's projects (users -> projects over mTLS, D4 matrix).
Only synthetic data is created. No token or signed URL is printed.
"""
import os
import struct
import sys
import threading
import time
import uuid
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from b4_common import BASE, CA, Results, direct, internal_token, register  # noqa: E402

os.environ["SSL_CERT_FILE"] = CA          # websocket-client (wss) trusts the installation CA
os.environ["REQUESTS_CA_BUNDLE"] = CA
import requests  # noqa: E402
import socketio  # noqa: E402

PUBLIC = BASE[: -len("/api-gateway/")]
res = Results("B5 functional")
http = requests.Session()
http.trust_env = False
http.verify = CA


def api(method, path, token, **kw):
    headers = dict(kw.pop("headers", {}))
    headers["Authorization"] = "Bearer " + token
    return http.request(method, BASE + path, headers=headers, timeout=120, **kw)


def png(w=48, h=32):
    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xffffffff)
    raw = b"".join(b"\x00" + b"".join(bytes(((x * 5) % 256, (y * 7) % 256, 120)) for x in range(w)) for y in range(h))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def png_size(data):
    return struct.unpack(">II", data[16:24]) if data.startswith(b"\x89PNG\r\n\x1a\n") else None


def public_url(url):
    """Signed URLs name the public entry; on the stack network that is nginx itself."""
    for prefix in ("https://localhost:8080", "https://localhost:28080"):
        if url.startswith(prefix):
            return PUBLIC + url[len(prefix):]
    return url


acct = register()
uid, token = acct["id"], acct["token"]

# W1: websocket transport through nginx.
events, connected = [], threading.Event()
sio = socketio.Client(reconnection=False, http_session=http)
sio.on("connect", lambda: connected.set())
for name in ("process-update", "process-error", "project-op", "project-updated"):
    sio.on(name, lambda data=None, _n=name: events.append(_n))
try:
    sio.connect(PUBLIC, transports=["websocket"], auth={"token": token}, wait_timeout=15)
    ws_ok = connected.wait(15)
except Exception as exc:  # noqa: BLE001
    ws_ok = False
    print(f"INFO W1 connect error: {type(exc).__name__}")
res.check("W1", "wss through nginx connects (websocket transport)", ws_ok, True)

# E1: generative expand_ai.
pid = api("POST", f"projects/{uid}", token, json={"name": "b5-functional"}).json()["_id"]
version = lambda: str(api("GET", f"projects/{uid}/{pid}", token).json()["version"])  # noqa: E731
if ws_ok:
    sio.emit("join-project", pid)
source = png()
r = api("POST", f"projects/{uid}/{pid}/img", token, files={"image": ("b5.png", source, "image/png")},
        headers={"X-Project-Version": version()})
res.check("E1", "upload image", r.status_code, {200, 201, 204})
r = api("POST", f"projects/{uid}/{pid}/tool", token,
        json={"procedure": "expand_ai", "params": {"mode": "generative", "left": 8, "right": 8,
                                                   "top": 4, "bottom": 4, "steps": 5}},
        headers={"X-Project-Version": version()})
res.check("E1", "add expand_ai (generative)", r.status_code, {200, 201, 204})
r = api("POST", f"projects/{uid}/{pid}/process", token, json={}, headers={"X-Project-Version": version()})
res.check("E1", "apply (free account, one advanced operation)", r.status_code, {200, 201, 202, 204})
results = []
for _ in range(120):
    r = api("GET", f"projects/{uid}/{pid}/process/url", token)
    if r.status_code == 200:
        body = r.json()
        results = body if isinstance(body, list) else body.get("imgs") or body.get("results") or []
    if results:
        break
    time.sleep(1)
size = None
if results:
    out = http.get(public_url(results[0]["url"]), timeout=60)
    size = png_size(out.content) if out.status_code == 200 else out.status_code
res.check("E1", "generative outpainting result is the padded PNG (48x32 -> 64x40)", size, lambda v: v == (64, 40))
time.sleep(2)
res.check("W1", "processing events received over wss", "process-update" in events, True)
if ws_ok:
    sio.disconnect()

# D1: account deletion through the public API removes the projects.
before = direct("projects", "GET", f"/{uid}", peer="api_gateway",
                token=internal_token("projects", "GET", f"/{uid}", uid), want_body=True)
res.check("D1", "projects listed before deletion", isinstance(before[1], list) and len(before[1]) >= 1, True)
res.check("D1", "holder deletes the account", api("DELETE", f"users/{uid}", token).status_code, 204)
after = direct("projects", "GET", f"/{uid}", peer="api_gateway",
               token=internal_token("projects", "GET", f"/{uid}", uid), want_body=True)
res.check("D1", "no project left for the deleted account", after[1] if after[0] == 200 else after[0], lambda v: v == [])
res.finish()
