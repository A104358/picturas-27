"""B12 (decision 51): deleting a project or an account while a video hash is pending releases the slot.

Runs on the host against picturas-dev (https://localhost:8080) and reads the dev MongoDB through
`docker compose exec projects`. Each cycle uploads a short video through the legacy POST and
deletes its project (or, in the last cycle, the whole account) at once, before the background
hash (which waits at least one second) can run. Before decision 51 such an attempt stayed
ready_hash_pending for ever: it kept its slot, and the hash pump kept retrying the oldest orphan,
so later videos never got their hash and after three orphans every video upload answered 429.
No token is printed.
"""
import json
import os
import subprocess
import ssl
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = os.environ.get("B12_BASE_URL", "https://localhost:8080") + "/api-gateway/"
TLS = ssl.create_default_context(cafile=str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/ca/ca.crt"))
VIDEO = (ROOT / "samples/video/sample_10s_720p.mp4").read_bytes()
CYCLES = 4  # with the account cycle, more than the 3 global slots
failures = []
NODE = r"""
const mongoose = require('mongoose');
const owners = JSON.parse(require('fs').readFileSync(0, 'utf8'));
(async () => {
  await mongoose.connect(process.env.MONGO_URI);
  const Upload = require('./models/upload');
  const UploadSlot = require('./models/uploadSlot');
  const Project = require('./models/project');
  const attempts = await Upload.find({ ownerId: { $in: owners } }).lean();
  const ids = attempts.map((a) => a._id);
  const held = await UploadSlot.countDocuments({ uploadId: { $in: ids } });
  const projects = await Project.find({ user_id: { $in: owners } }, { 'imgs.hash_state': 1 }).lean();
  process.stdout.write(JSON.stringify({ states: attempts.map((a) => a.state), held,
    hashes: projects.flatMap((p) => (p.imgs || []).map((i) => i.hash_state)) }) + '\n');
  await mongoose.disconnect();
})().catch((e) => { process.stderr.write(e.message + '\n'); process.exit(1); });
"""


def inspect(owners):
    done = subprocess.run(["docker", "compose", "-p", "picturas-dev", "exec", "-T", "projects", "node", "-e", NODE],
                          cwd=ROOT, input=json.dumps(owners), text=True, capture_output=True, timeout=30, check=True)
    return json.loads(done.stdout.strip().splitlines()[-1])


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} {label}{(': ' + str(detail)) if detail != '' else ''}", flush=True)
    if not ok:
        failures.append(label)


def api(method, route, token=None, data=None, raw=None, ctype=None, headers=None):
    h = dict(headers or {})
    if token:
        h["Authorization"] = "Bearer " + token
    body = None
    if data is not None:
        body, h["Content-Type"] = json.dumps(data).encode(), "application/json"
    elif raw is not None:
        body, h["Content-Type"] = raw, ctype
    request = urllib.request.Request(BASE + route, method=method, headers=h, data=body)
    try:
        with urllib.request.urlopen(request, context=TLS, timeout=120) as response:
            content = response.read()
            try:
                return response.status, json.loads(content) if content else None
            except ValueError:
                return response.status, None
    except urllib.error.HTTPError as error:
        error.read()
        return error.code, None


def upload(uid, pid, token):
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"video\"; filename=\"v.mp4\"\r\n"
            "Content-Type: video/mp4\r\n\r\n").encode() + VIDEO + f"\r\n--{boundary}--\r\n".encode()
    version = str(api("GET", f"projects/{uid}/{pid}", token)[1]["version"])
    return api("POST", f"projects/{uid}/{pid}/video", token, raw=body,
               ctype=f"multipart/form-data; boundary={boundary}", headers={"X-Project-Version": version})[0]


def account():
    status, body = api("POST", "users/", data={
        "name": "B12 hash orphan", "email": f"b12-hash-{uuid.uuid4().hex}@example.invalid",
        "password": uuid.uuid4().hex, "type": "free"})
    assert status == 201, status
    return body["user"]["_id"], body["jwt"]


uid, token = account()
for n in range(1, CYCLES + 1):
    pid = api("POST", f"projects/{uid}", token, {"name": f"orphan {n}"})[1]["_id"]
    status = upload(uid, pid, token)
    version = str(api("GET", f"projects/{uid}/{pid}", token)[1]["version"])
    deleted = api("DELETE", f"projects/{uid}/{pid}", token, headers={"X-Project-Version": version})[0]
    check(f"cycle {n}: upload accepted, project deleted before its hash", status == 204 and deleted in (200, 204),
          f"upload {status}, delete {deleted}")
    time.sleep(3)  # the hash pump visits one attempt per second

gone_uid, gone_token = account()
pid = api("POST", f"projects/{gone_uid}", gone_token, {"name": "account orphan"})[1]["_id"]
status = upload(gone_uid, pid, gone_token)
deleted = api("DELETE", f"users/{gone_uid}", gone_token)[0]
check("account cycle: upload accepted, account deleted before its hash", status == 204 and deleted in (200, 204),
      f"upload {status}, delete {deleted}")
time.sleep(3)

pid = api("POST", f"projects/{uid}", token, {"name": "kept"})[1]["_id"]
check("later upload after the orphans (no 429)", upload(uid, pid, token) == 204)
seen = None
end = time.monotonic() + 60
while time.monotonic() < end:
    seen = inspect([uid, gone_uid])
    if seen["hashes"] == ["ready"] and "ready_hash_pending" not in seen["states"] and seen["held"] == 0:
        break
    time.sleep(1)
check("orphaned attempts finished, no slot held", "ready_hash_pending" not in seen["states"] and seen["held"] == 0,
      f"states {sorted(set(seen['states']))}, slots held {seen['held']}")
check("later video gets its hash (pump not blocked by orphans)", seen["hashes"] == ["ready"], seen["hashes"])
api("DELETE", f"users/{uid}", token)
print(f"B12 hash orphan: {'all checks passed' if not failures else 'FAILED ' + ', '.join(failures)}")
raise SystemExit(1 if failures else 0)
