"""B2 image/video batch pipeline and media checks; no tokens or signed URLs in output."""
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import time
import uuid
import zlib
from pathlib import Path

import requests

base = "https://localhost:8080"
api = base + "/api-gateway/"
ca = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/services/nginx/ca.crt")
video_source = Path("samples/video/sample_10s_720p.mp4")
s = requests.Session()
s.trust_env = False
s.verify = ca

def req(method, path, token=None, **kw):
    headers = dict(kw.pop("headers", {}))
    if token:
        headers["Authorization"] = "Bearer " + token
    r = s.request(method, api + path, headers=headers, timeout=120, **kw)
    assert r.status_code < 400, (method, path, r.status_code)
    return r

def png():
    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xffffffff)
    raw = (b"\x00" + bytes((40, 90, 140)) * 64) * 64
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")

def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name:format=duration",
        "-of", "json", str(path)], text=True))

def frame_mean(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"])
    return sum(raw) / len(raw)

email = f"b2-{uuid.uuid4().hex[:12]}@example.invalid"
password = uuid.uuid4().hex
reg = req("POST", "users/", json={"name": "b2", "email": email, "password": password, "type": "free"})
uid = reg.json()["user"]["_id"]
login = req("POST", f"users/{email}/login", json={"password": password})
token = login.json()["jwt"]
pid = req("POST", f"projects/{uid}", token, json={"name": "b2-functional"}).json()["_id"]

def version():
    return str(req("GET", f"projects/{uid}/{pid}", token).json()["version"])

image_source = png()
r = req("POST", f"projects/{uid}/{pid}/img", token,
        files={"image": ("b2.png", image_source, "image/png")},
        headers={"X-Project-Version": version()})
assert r.status_code in (200, 201, 204)
with video_source.open("rb") as f:
    r = req("POST", f"projects/{uid}/{pid}/video", token,
            files={"video": ("b2.mp4", f, "video/mp4")},
            headers={"X-Project-Version": version()})
assert r.status_code in (200, 201, 204)
items = req("GET", f"projects/{uid}/{pid}/imgs", token).json()
assert len(items) == 2
image_id = next(str(x["_id"]) for x in items if x.get("media_type") != "video")
original_url = req("GET", f"projects/{uid}/{pid}/img/{image_id}", token).json()["url"]
assert hashlib.sha256(s.get(original_url, timeout=30).content).digest() == hashlib.sha256(image_source).digest()
req("POST", f"projects/{uid}/{pid}/tool", token,
    json={"procedure": "brightness", "params": {"brightness": 1.4}},
    headers={"X-Project-Version": version()})
req("POST", f"projects/{uid}/{pid}/process", token, json={},
    headers={"X-Project-Version": version()})
results = []
for _ in range(180):
    r = s.get(api + f"projects/{uid}/{pid}/process/url",
              headers={"Authorization": "Bearer " + token}, timeout=30)
    if r.status_code == 200:
        body = r.json()
        results = body if isinstance(body, list) else body.get("imgs") or body.get("results") or []
    if len(results) >= 2:
        break
    time.sleep(2)
assert len(results) >= 2, f"batch produced {len(results)}/2 results"
outputs = [s.get(x["url"], timeout=60).content for x in results[:2]]
image_outputs = [x for x in outputs if x.startswith(b"\x89PNG\r\n\x1a\n")]
video_outputs = [x for x in outputs if b"ftyp" in x[:32]]
assert len(image_outputs) == len(video_outputs) == 1
assert image_outputs[0] != image_source
with tempfile.TemporaryDirectory(prefix="picturas-b2-f02-") as tmp:
    output_path = Path(tmp) / "out.mp4"
    output_path.write_bytes(video_outputs[0])
    info = probe(output_path)
    streams = {(x["codec_type"], x["codec_name"]) for x in info["streams"]}
    assert ("video", "h264") in streams and ("audio", "aac") in streams, streams
    duration = float(info["format"]["duration"])
    assert 9 <= duration <= 11, duration
    assert frame_mean(output_path) > frame_mean(video_source)
print("B2 F02: image and video batch output; PNG changed; MP4/H.264/AAC, duration and brighter frame passed")
