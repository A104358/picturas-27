"""A direct PUT finishing after first cleanup leaves no staging object after the safety sweep."""
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import secrets
import subprocess
import time
import uuid

import requests


ROOT = Path(__file__).resolve().parents[3]
BASE = "https://localhost:8080/api-gateway/"
CA = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/ca/ca.crt")
SAMPLE = ROOT / "samples/video/sample_10s_720p.mp4"
SESSION = requests.Session()
SESSION.trust_env = False


def call(method, path, jwt=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if jwt:
        headers["Authorization"] = "Bearer " + jwt
    return SESSION.request(method, BASE + path, headers=headers, verify=CA, timeout=60, **kwargs)


NODE = r"""
const fs = require('fs');
const crypto = require('crypto');
const mongoose = require('mongoose');
const axios = require('axios');
const Upload = require('./models/upload');
const agent = require('./tls/pkiTls').clientAgent({ keepAlive: false });
(async () => {
  const args = JSON.parse(fs.readFileSync(0, 'utf8'));
  await mongoose.connect(process.env.MONGO_URI);
  const tokenHash = crypto.createHash('sha256').update(args.token).digest('hex');
  const upload = await Upload.findOne({ tokenHash });
  if (!upload) throw new Error('test attempt missing');
  if (args.offsetSeconds !== undefined) {
    await Upload.updateOne({ _id: upload._id },
      { $set: { deadline: new Date(Date.now() + args.offsetSeconds * 1000) } });
  }
  const url = `https://img_storage:11000/video-objects/${upload.ownerId}/${upload.projectId}/staging/${upload.objectName}`;
  const head = await axios.head(url, { httpsAgent: agent, timeout: 10000,
    validateStatus: () => true });
  const updated = await Upload.findById(upload._id);
  process.stdout.write(JSON.stringify({ state: updated.state, cleanup: updated.cleanup,
    lateCleanupDone: updated.lateCleanupDone, stagingStatus: head.status }) + '\n');
  await mongoose.disconnect();
})().catch((error) => { process.stderr.write(error.message + '\n'); process.exit(1); });
"""


def inspect(token, offset=None):
    args = {"token": token}
    if offset is not None:
        args["offsetSeconds"] = offset
    cmd = ["docker", "compose", "-p", "picturas-dev", "exec", "-T", "projects",
           "node", "-e", NODE]
    done = subprocess.run(cmd, input=json.dumps(args), text=True, capture_output=True,
                          cwd=ROOT, env=os.environ, timeout=30, check=True)
    return json.loads(done.stdout.strip().splitlines()[-1])


def wait_for(token, predicate, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        state = inspect(token)
        if predicate(state):
            return state
        time.sleep(1)
    raise AssertionError(state)


account = call("POST", "users/", json={
    "name": "B7 late cleanup", "email": f"b7-late-{uuid.uuid4().hex}@example.invalid",
    "password": secrets.token_urlsafe(24), "type": "free",
})
assert account.status_code == 201, account.status_code
owner = account.json()["user"]["_id"]
jwt = account.json()["jwt"]
created = call("POST", f"projects/{owner}", jwt, json={"name": "B7 late cleanup"})
assert created.status_code == 201, created.status_code
project = f"projects/{owner}/{created.json()['_id']}"
version = call("GET", project, jwt).json()["version"]
meta = {"name": "late.mp4", "size": SAMPLE.stat().st_size, "type": "video/mp4",
        "duration": 10, "width": 1280, "height": 720}
for _ in range(30):
    requested = call("POST", project + "/video/uploads", jwt, json=meta,
                     headers={"X-Project-Version": str(version)})
    if requested.status_code != 429:
        break
    time.sleep(1)  # Previous successful hashes may still hold the three global slots.
assert requested.status_code == 201, requested.status_code
token = requested.json()["token"]


class SlowReader:
    def __init__(self, file):
        self.file = file
        self.calls = 0

    def read(self, size=-1):
        self.calls += 1
        if self.calls == 2:
            time.sleep(10)
        return self.file.read(min(size, 65536) if size > 0 else 65536)


def send():
    client = requests.Session()
    client.trust_env = False
    with SAMPLE.open("rb") as file:
        return client.put("https://localhost:8080" + requested.json()["uploadUrl"],
                          data=SlowReader(file), verify=CA, timeout=45,
                          headers={"Authorization": "Bearer " + jwt,
                                   "Content-Type": "video/mp4",
                                   "Content-Length": str(meta["size"])}).status_code


with ThreadPoolExecutor(max_workers=1) as pool:
    put = pool.submit(send)
    try:
        wait_for(token, lambda state: state["state"] == "receiving")
    except AssertionError:
        print("PUT status at claim timeout:", put.result(timeout=40))
        raise
    inspect(token, -1)  # First sweep expires and cleans while body is still in flight.
    wait_for(token, lambda state: state["state"] == "expired" and state["cleanup"] == "cleaned")
    status = put.result(timeout=40)
    assert status in (200, 201, 204), status

assert inspect(token)["stagingStatus"] == 200, "slow PUT did not finish after first cleanup"
inspect(token, -1021)  # Accelerate only this fixture's safety deadline.
final = wait_for(token, lambda state: state["lateCleanupDone"])
assert final["stagingStatus"] == 404, final
assert call("POST", project + f"/video/uploads/{token}/confirm", jwt).status_code == 410
assert len(call("GET", project, jwt).json()["imgs"]) == 0
print("PASS late direct PUT: first cleanup, safety sweep, zero staging objects or published media")
