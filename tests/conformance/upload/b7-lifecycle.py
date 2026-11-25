"""B7 lifecycle edges: token lifetime, incomplete/complete bodies, version fence and rejection."""
import http.client
import json
import os
from pathlib import Path
import secrets
import ssl
import subprocess
import time
import uuid

import requests


ROOT = Path(__file__).resolve().parents[3]
CA = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/ca/ca.crt")
SAMPLE = ROOT / "samples/video/sample_10s_720p.mp4"
BASE = "https://localhost:8080/api-gateway/"
HTTP = requests.Session()
HTTP.trust_env = False


def call(method, path, jwt=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if jwt:
        headers["Authorization"] = "Bearer " + jwt
    return HTTP.request(method, BASE + path, headers=headers, verify=CA, timeout=60, **kwargs)


NODE = r"""
const fs = require('fs');
const crypto = require('crypto');
const mongoose = require('mongoose');
const Upload = require('./models/upload');
const Project = require('./models/project');
(async () => {
  const arg = JSON.parse(fs.readFileSync(0, 'utf8'));
  await mongoose.connect(process.env.MONGO_URI);
  const hash = crypto.createHash('sha256').update(arg.token).digest('hex');
  const upload = await Upload.findOne({ tokenHash: hash });
  if (!upload) throw new Error('fixture missing');
  if (arg.op === 'expireToken') await Upload.updateOne({ _id: upload._id },
    { $set: { tokenExpiresAt: new Date(Date.now() - 1000) } });
  if (arg.op === 'expireAttempt') await Upload.updateOne({ _id: upload._id },
    { $set: { deadline: new Date(Date.now() - 1000) } });
  if (arg.op === 'bumpVersion') await Project.updateOne({ _id: upload.projectId },
    { $inc: { version: 1 } });
  if (arg.op === 'simulatePromoting') await Upload.updateOne({ _id: upload._id },
    { $set: { stage: 'src', state: 'promoting' } });
  if (arg.op === 'simulateCommitting') await Upload.updateOne({ _id: upload._id },
    { $set: { state: 'committing', mediaId: null, resultVersion: null } });
  let probeError = null;
  if (arg.op === 'checkProbeUrl') {
    await Upload.updateOne({ _id: upload._id }, { $set: { state: 'received' } });
    const engine = require('./utils/videoUploadEngine');
    try { await engine.finalize({ ...upload.toObject(), probeUrl: arg.probeUrl }, 'free'); }
    catch (e) { probeError = e.message; }
    await engine.fail(upload, 'Probe URL test');
  }
  const updated = await Upload.findById(upload._id);
  let stagingStatus = null;
  if (arg.op === 'inspectStorage') {
    const axios = require('axios');
    const agent = require('./tls/pkiTls').clientAgent({ keepAlive: false });
    const url = `https://img_storage:11000/video-objects/${updated.ownerId}/${updated.projectId}/staging/${updated.objectName}`;
    const response = await axios.head(url, { httpsAgent: agent, timeout: 10000,
      validateStatus: () => true });
    stagingStatus = response.status;
  }
  process.stdout.write(JSON.stringify({ state: updated.state, cleanup: updated.cleanup,
    stage: updated.stage, objectName: updated.objectName, ownerId: String(updated.ownerId),
    projectId: String(updated.projectId), stagingStatus, probeError }) + '\n');
  await mongoose.disconnect();
})().catch(e => { process.stderr.write(e.message + '\n'); process.exit(1); });
"""


def inspect(token, op="inspect", **extra):
    done = subprocess.run(["docker", "compose", "-p", "picturas-dev", "exec", "-T",
                           "projects", "node", "-e", NODE], cwd=ROOT, env=os.environ,
                          input=json.dumps({"token": token, "op": op, **extra}), text=True,
                          capture_output=True, timeout=30, check=True)
    return json.loads(done.stdout.strip().splitlines()[-1])


def request(jwt, project, version, name):
    meta = {"name": name, "size": SAMPLE.stat().st_size, "type": "video/mp4",
            "duration": 10, "width": 1280, "height": 720}
    for _ in range(30):
        response = call("POST", project + "/video/uploads", jwt, json=meta,
                        headers={"X-Project-Version": str(version)})
        if response.status_code != 429:
            break
        time.sleep(1)
    assert response.status_code == 201, (response.status_code, response.text[:100])
    return response.json()["token"], response.json()["uploadUrl"].removeprefix("/api-gateway/")


def put(jwt, path, payload=SAMPLE):
    if isinstance(payload, Path):
        with payload.open("rb") as file:
            return call("PUT", path, jwt, data=file,
                        headers={"Content-Length": str(payload.stat().st_size),
                                 "Content-Type": "video/mp4"})
    return call("PUT", path, jwt, data=payload,
                headers={"Content-Length": str(len(payload)), "Content-Type": "video/mp4"})


def partial_put(jwt, path):
    context = ssl.create_default_context(cafile=CA)
    conn = http.client.HTTPSConnection("localhost", 8080, context=context, timeout=10)
    conn.putrequest("PUT", "/api-gateway/" + path)
    conn.putheader("Authorization", "Bearer " + jwt)
    conn.putheader("Content-Type", "video/mp4")
    conn.putheader("Content-Length", str(SAMPLE.stat().st_size))
    conn.endheaders()
    with SAMPLE.open("rb") as file:
        conn.send(file.read(65536))
    time.sleep(1)
    conn.close()


account = call("POST", "users/", json={
    "name": "B7 lifecycle", "email": f"b7-life-{uuid.uuid4().hex}@example.invalid",
    "password": secrets.token_urlsafe(24), "type": "free",
})
assert account.status_code == 201, account.status_code
owner, jwt = account.json()["user"]["_id"], account.json()["jwt"]
created = call("POST", f"projects/{owner}", jwt, json={"name": "B7 lifecycle"})
assert created.status_code == 201, created.status_code
project = f"projects/{owner}/{created.json()['_id']}"
version = call("GET", project, jwt).json()["version"]

# A token expires without becoming reusable, and no body reaches storage.
token, path = request(jwt, project, version, "expired-token.mp4")
inspect(token, "expireToken")
assert put(jwt, path).status_code == 410
assert inspect(token)["state"] == "created"
assert call("POST", project + f"/video/uploads/{token}/cancel", jwt).status_code == 204
print("PASS UL-04 expired token refused before body")

# The project version is checked again at PUT; a previously granted token cannot
# commit after another edit has won the project document.
token, path = request(jwt, project, version, "stale-version.mp4")
inspect(token, "bumpVersion")
assert put(jwt, path).status_code == 409
assert call("POST", project + f"/video/uploads/{token}/confirm", jwt).status_code == 409
assert call("POST", project + f"/video/uploads/{token}/cancel", jwt).status_code == 204
version += 1
print("PASS UL-05 version change fences direct PUT and confirmation")

# An interrupted request consumes the claim and cannot be resumed; confirmation
# distinguishes it from an object whose response was merely lost.
token, path = request(jwt, project, version, "partial.mp4")
partial_put(jwt, path)
end = time.monotonic() + 10
while inspect(token)["state"] == "created" and time.monotonic() < end:
    time.sleep(.2)
assert inspect(token)["state"] == "receiving"
assert call("POST", project + f"/video/uploads/{token}/confirm", jwt).status_code == 409
assert put(jwt, path).status_code == 409
assert call("POST", project + f"/video/uploads/{token}/cancel", jwt).status_code == 204
inspect(token, "expireAttempt")
end = time.monotonic() + 15
while inspect(token)["cleanup"] != "cleaned" and time.monotonic() < end:
    time.sleep(.5)
assert inspect(token)["cleanup"] == "cleaned"
print("PASS UL-01/03 incomplete PUT claims once and cannot confirm")

token, path = request(jwt, project, version, "lost-response.mp4")
assert put(jwt, path).status_code in (200, 201, 204)
# Discard the PUT response; confirmation must discover the complete S3 object.
assert call("POST", project + f"/video/uploads/{token}/confirm", jwt).status_code == 204
assert call("POST", project + f"/video/uploads/{token}/confirm", jwt).status_code == 204
assert len(call("GET", project, jwt).json()["imgs"]) == 1
print("PASS UL-03 complete PUT remains confirmable and idempotent")

version += 1
token, path = request(jwt, project, version, "invalid-body.mp4")
bad = bytes(SAMPLE.stat().st_size)
assert put(jwt, path, bad).status_code in (200, 201, 204)
staging = inspect(token)
public = HTTP.get("https://localhost:8080/s3/picturas/users/" + owner +
    "/projects/" + staging["projectId"] + "/staging/" + staging["objectName"],
    verify=CA, timeout=10)
assert public.status_code == 403, public.status_code
assert call("POST", project + f"/video/uploads/{token}/confirm", jwt).status_code == 400
assert len(call("GET", project, jwt).json()["imgs"]) == 1
print("PASS UL-06/10 staging is private; invalid video cannot publish")

# Crash after a complete direct PUT, before confirmation: projects can restart
# without discarding the external writer's completed staging object.
token, path = request(jwt, project, version, "restart-before-confirm.mp4")
assert put(jwt, path).status_code in (200, 201, 204)
subprocess.run(["docker", "compose", "-p", "picturas-dev", "restart", "projects", "nginx"],
               cwd=ROOT, env=os.environ, capture_output=True, text=True, timeout=60, check=True)
time.sleep(4)
assert call("POST", project + f"/video/uploads/{token}/confirm", jwt).status_code == 204
assert len(call("GET", project, jwt).json()["imgs"]) == 2
end = time.monotonic() + 20
while inspect(token)["state"] != "ready" and time.monotonic() < end:
    time.sleep(.5)
assert inspect(token)["state"] == "ready"
published_token = token
print("PASS UL-07/09 restart before confirmation and durable hash completion")

# A cleanup that cannot reach storage must remain pending, then retry after
# storage returns. The project must never publish this staged object.
token, path = request(jwt, project, version + 1, "storage-outage.mp4")
assert put(jwt, path).status_code in (200, 201, 204)
subprocess.run(["docker", "compose", "-p", "picturas-dev", "stop", "img_storage"],
               cwd=ROOT, env=os.environ, capture_output=True, text=True, timeout=40, check=True)
try:
    inspect(token, "expireAttempt")
    end = time.monotonic() + 25
    while inspect(token)["cleanup"] != "cleanup_failed" and time.monotonic() < end:
        time.sleep(1)
    assert inspect(token)["cleanup"] == "cleanup_failed"
finally:
    subprocess.run(["docker", "compose", "-p", "picturas-dev", "start", "img_storage"],
                   cwd=ROOT, env=os.environ, capture_output=True, text=True, timeout=40, check=True)
end = time.monotonic() + 25
while inspect(token)["cleanup"] != "cleaned" and time.monotonic() < end:
    time.sleep(1)
assert inspect(token)["cleanup"] == "cleaned"
assert inspect(token, "inspectStorage")["stagingStatus"] == 404
assert len(call("GET", project, jwt).json()["imgs"]) == 2
print("PASS UL-11 storage outage retains cleanup failure, then removes staging on retry")

# Reconstruct two journal boundaries after a process crash. An unpublished copy
# is cleaned, while a project document that already contains the original wins
# over the stale committing marker and is never deleted.
token, path = request(jwt, project, version + 1, "copy-crash.mp4")
assert put(jwt, path).status_code in (200, 201, 204)
inspect(token, "simulatePromoting")
inspect(published_token, "simulateCommitting")
subprocess.run(["docker", "compose", "-p", "picturas-dev", "restart", "projects", "nginx"],
               cwd=ROOT, env=os.environ, capture_output=True, text=True, timeout=60, check=True)
time.sleep(4)
end = time.monotonic() + 20
while (inspect(token)["cleanup"] != "cleaned" or
       inspect(published_token)["state"] != "ready") and time.monotonic() < end:
    time.sleep(.5)
assert inspect(token)["state"] == "failed"
assert inspect(token, "inspectStorage")["stagingStatus"] == 404
assert inspect(published_token)["state"] == "ready"
assert call("POST", project + f"/video/uploads/{token}/confirm", jwt).status_code == 410
assert len(call("GET", project, jwt).json()["imgs"]) == 2
print("PASS UL-07/08 promoting crash cleans unpublished copy; committing marker keeps published media")

for label, probe_url in [
    ("authority confusion", "https://seaweedfs:9000@invalid.example/picturas/users/x"),
    ("wrong object", "https://seaweedfs:9000/picturas/users/another/projects/another/src/video.mp4"),
]:
    token, _ = request(jwt, project, version + 1, f"probe-{label.replace(' ', '-')}.mp4")
    checked = inspect(token, "checkProbeUrl", probeUrl=probe_url)
    assert checked["probeError"] == "Video read URL unavailable", checked
    assert checked["state"] == "failed" and checked["cleanup"] == "cleaned", checked
assert len(call("GET", project, jwt).json()["imgs"]) == 2
print("PASS UL-10 probe rejects foreign authority and wrong S3 object before I/O")
