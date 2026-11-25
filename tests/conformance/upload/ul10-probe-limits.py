"""UL-10: independent injection of the B6 probe relay's byte and time limits.

Runs against the development stack (default project `picturas-dev`).

1. Control with the decided limits: legacy POST and direct flow are accepted.
2. Default 15 s deadline, in the projects container, through the real `probe()` with a
   local upstream that trickles a valid MP4: refused at ~15 s, ffprobe gone, upstream closed.
3. Byte limit alone (VIDEO_PROBE_MAX_BYTES tightened, time untouched) in the real server.
4. Time limit alone (VIDEO_PROBE_TIMEOUT_MS tightened, bytes untouched) in the real server.
   For 3 and 4, both transports: 400, attempt terminal and cleaned, no staging/src object,
   no media, no busy slot, no ffprobe process and no loopback relay listener left.
5. Restore the decided limits and repeat the control.

Prints no JWT, token or signed URL.
"""
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import uuid

import requests


ROOT = Path(__file__).resolve().parents[3]
PROJECT = os.environ.get("UL10_COMPOSE_PROJECT", "picturas-dev")
OVERRIDE = Path(__file__).with_name("ul10-probe.override.yaml")
CA = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/ca/ca.crt")
SAMPLE = ROOT / "samples/video/sample_10s_720p.mp4"
BASE = "https://localhost:8080/api-gateway/"
HTTP = requests.Session()
HTTP.trust_env = False
BYTES_LIMIT = "8192"
TIME_LIMIT_MS = "10"


def call(method, path, jwt=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if jwt:
        headers["Authorization"] = "Bearer " + jwt
    return HTTP.request(method, BASE + path, headers=headers, verify=CA, timeout=90, **kwargs)


def compose(*args, env=None, timeout=180, input=None):
    return subprocess.run(["docker", "compose", "-p", PROJECT, *args], cwd=ROOT,
                          env=env or os.environ, input=input, text=True,
                          capture_output=True, timeout=timeout, check=True).stdout


def exec_projects(*args, input=None, timeout=60):
    return compose("exec", "-T", "projects", *args, input=input, timeout=timeout)


def recreate(max_bytes="", timeout_ms=""):
    env = {**os.environ, "UL10_PROBE_MAX_BYTES": max_bytes, "UL10_PROBE_TIMEOUT_MS": timeout_ms}
    compose("-f", "docker-compose.yaml", "-f", str(OVERRIDE), "up", "-d", "--no-deps",
            "--force-recreate", "projects", env=env)
    container = compose("ps", "-q", "projects").strip()
    end = time.monotonic() + 120
    while time.monotonic() < end:
        status = subprocess.run(["docker", "inspect", "-f", "{{.State.Health.Status}}", container],
                                capture_output=True, text=True).stdout.strip()
        if status == "healthy":
            break
        time.sleep(1)
    assert status == "healthy", status
    compose("restart", "nginx")
    seen = exec_projects("sh", "-c", 'printf "%s|%s" "$VIDEO_PROBE_MAX_BYTES" "$VIDEO_PROBE_TIMEOUT_MS"')
    assert seen == f"{max_bytes}|{timeout_ms}", seen
    end = time.monotonic() + 60
    while time.monotonic() < end:
        try:
            if call("GET", f"users/{owner}", jwt).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise AssertionError("gateway did not come back")


def residue():
    """ffprobe processes and loopback listeners (the relay binds 127.0.0.1:<ephemeral>)."""
    script = r"""
n=0; for p in /proc/[0-9]*; do
  if tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q '^ffprobe '; then n=$((n+1)); fi
done
l=$(awk 'NR>1 && $4=="0A" && $2 ~ /^0100007F:/' /proc/net/tcp | wc -l)
echo "$n $l"
"""
    ffprobe, listeners = exec_projects("sh", "-c", script).split()
    return int(ffprobe), int(listeners)


INSPECT = r"""
const fs = require('fs');
const mongoose = require('mongoose');
const axios = require('axios');
const Upload = require('./models/upload');
const Project = require('./models/project');
const UploadSlot = require('./models/uploadSlot');
const agent = require('./tls/pkiTls').clientAgent({ keepAlive: false });
(async () => {
  const arg = JSON.parse(fs.readFileSync(0, 'utf8'));
  await mongoose.connect(process.env.MONGO_URI);
  const uploads = [];
  for (const u of await Upload.find({ projectId: arg.projectId }).sort({ createdAt: 1 }).lean()) {
    const objects = {};
    if (u.objectName) for (const stage of ['staging', 'src']) {
      const r = await axios.head(`https://img_storage:11000/video-objects/${u.ownerId}/${u.projectId}/${stage}/${u.objectName}`,
        { httpsAgent: agent, timeout: 10000, validateStatus: () => true });
      objects[stage] = r.status;
    }
    uploads.push({ name: u.name, transport: u.transport, state: u.state, cleanup: u.cleanup,
      error: u.error || null, objects });
  }
  const project = await Project.findById(arg.projectId, { imgs: 1 }).lean();
  const busy = await UploadSlot.countDocuments({ uploadId: { $ne: null } });
  process.stdout.write(JSON.stringify({ uploads, media: project.imgs.length, busySlots: busy }) + '\n');
  await mongoose.disconnect();
})().catch(e => { process.stderr.write(e.message + '\n'); process.exit(1); });
"""


def inspect():
    out = exec_projects("node", "-e", INSPECT, input=json.dumps({"projectId": project_id}))
    return json.loads(out.strip().splitlines()[-1])


def version():
    return call("GET", project, jwt).json()["version"]


def legacy(name):
    for _ in range(30):
        with SAMPLE.open("rb") as file:
            started = time.monotonic()
            response = call("POST", project + "/video", jwt,
                            headers={"X-Project-Version": str(version())},
                            files={"video": (name, file, "video/mp4")})
        if response.status_code != 429:
            return response.status_code, time.monotonic() - started
        time.sleep(1)
    return response.status_code, 0.0


def direct(name):
    meta = {"name": name, "size": SAMPLE.stat().st_size, "type": "video/mp4",
            "duration": 10, "width": 1280, "height": 720}
    for _ in range(30):
        response = call("POST", project + "/video/uploads", jwt, json=meta,
                        headers={"X-Project-Version": str(version())})
        if response.status_code != 429:
            break
        time.sleep(1)
    assert response.status_code == 201, response.status_code
    token = response.json()["token"]
    path = response.json()["uploadUrl"].removeprefix("/api-gateway/")
    with SAMPLE.open("rb") as file:
        put = call("PUT", path, jwt, data=file, headers={
            "Content-Length": str(SAMPLE.stat().st_size), "Content-Type": "video/mp4"})
    assert put.status_code in (200, 201, 204), put.status_code
    started = time.monotonic()
    confirm = call("POST", project + f"/video/uploads/{token}/confirm", jwt)
    return confirm.status_code, time.monotonic() - started


def settled(names, media_before):
    """Wait for background cleanup and slot release, then check every residue."""
    end = time.monotonic() + 45
    while True:
        state = inspect()
        mine = [u for u in state["uploads"] if u["name"] in names]
        done = (len(mine) == len(names) and all(u["cleanup"] == "cleaned" for u in mine)
                and state["busySlots"] == 0)
        if done or time.monotonic() > end:
            break
        time.sleep(1)
    ffprobe, listeners = residue()
    for u in mine:
        print("  attempt", json.dumps(u, sort_keys=True))
    print(f"  media={state['media']} (before {media_before}) busySlots={state['busySlots']} "
          f"ffprobe={ffprobe} loopbackListeners={listeners} (baseline {baseline_listeners})")
    assert len(mine) == len(names), mine
    for u in mine:
        assert u["state"] in ("failed", "rejected"), u
        assert u["cleanup"] == "cleaned", u
        assert all(code == 404 for code in u["objects"].values()), u
    assert state["media"] == media_before, state["media"]
    assert state["busySlots"] == 0, state["busySlots"]
    assert ffprobe == 0, ffprobe
    assert listeners == baseline_listeners, listeners


TRICKLE = r"""
const http = require('http');
const fs = require('fs');
const sample = fs.readFileSync('/tmp/ul10-sample.mp4');
const engine = require('./utils/videoUploadEngine');
const mode = process.argv[1];
let served = 0, closed = 0, requests = 0;
const upstream = http.createServer((req, res) => {
  requests++;
  const m = /^bytes=(\d+)-(\d+)$/.exec(req.headers.range || '');
  const start = m ? Number(m[1]) : 0;
  const end = m ? Math.min(Number(m[2]), sample.length - 1) : sample.length - 1;
  res.writeHead(m ? 206 : 200, { 'content-length': String(end - start + 1),
    ...(m ? { 'content-range': `bytes ${start}-${end}/${sample.length}` } : {}) });
  res.on('close', () => { closed++; });
  if (mode === 'fast') { served += end - start + 1; res.end(sample.subarray(start, end + 1)); return; }
  let pos = start;   // 256 bytes every 250 ms: data keeps flowing, so ffprobe's 3 s
  const timer = setInterval(() => {   // rw_timeout never fires; only the deadline can.
    if (pos > end || res.destroyed) { clearInterval(timer); if (!res.destroyed) res.end(); return; }
    const chunk = sample.subarray(pos, Math.min(end + 1, pos + 256));
    pos += chunk.length; served += chunk.length; res.write(chunk);
  }, 250);
  res.on('close', () => clearInterval(timer));
});
upstream.listen(0, '127.0.0.1', async () => {
  const url = `http://127.0.0.1:${upstream.address().port}/object`;
  const started = Date.now();
  let result, error = null;
  try { result = await engine.probe(url, sample.length); } catch (e) { error = e.message; }
  const elapsed = Date.now() - started;
  await new Promise((r) => setTimeout(r, 1000));
  upstream.close();
  process.stdout.write(JSON.stringify({ mode, elapsedMs: elapsed, error,
    duration: result ? result.duration : null, width: result ? result.width : null,
    served, requests, upstreamClosed: closed, budget: sample.length * 2 + 16 * 1024 * 1024 }) + '\n');
  process.exit(0);
});
"""


def trickle(mode):
    out = exec_projects("node", "-e", TRICKLE, mode, timeout=90)
    return json.loads(out.strip().splitlines()[-1])


account = call("POST", "users/", json={
    "name": "UL-10 probe", "email": f"ul10-{uuid.uuid4().hex}@example.invalid",
    "password": secrets.token_urlsafe(24), "type": "free"})
assert account.status_code == 201, account.status_code
owner, jwt = account.json()["user"]["_id"], account.json()["jwt"]
created = call("POST", f"projects/{owner}", jwt, json={"name": "UL-10 probe"})
assert created.status_code == 201, created.status_code
project_id = created.json()["_id"]
project = f"projects/{owner}/{project_id}"

# Start from the decided limits, whatever an earlier aborted run left behind.
recreate()
baseline_listeners = residue()[1]
print(f"baseline loopbackListeners={baseline_listeners}")

# 1. Control.
assert legacy("control-legacy.mp4")[0] == 204
assert direct("control-direct.mp4")[0] == 204
assert inspect()["media"] == 2
print("PASS control: decided limits accept a valid video on both transports")

# 2. Default deadline through the real probe(), no environment override.
subprocess.run(["docker", "cp", str(SAMPLE),
                compose("ps", "-q", "projects").strip() + ":/tmp/ul10-sample.mp4"],
               check=True, capture_output=True)
fast = trickle("fast")
print("  fast upstream", json.dumps(fast, sort_keys=True))
assert fast["error"] is None and round(fast["duration"]) == 10 and fast["width"] == 1280
assert fast["served"] < fast["budget"]
print("PASS harness control: same upstream, served quickly, probes the sample")
slow = trickle("slow")
print("  slow upstream", json.dumps(slow, sort_keys=True))
assert slow["error"] == "Unreadable or corrupted video file", slow["error"]
assert 14500 <= slow["elapsedMs"] <= 16500, slow["elapsedMs"]
assert slow["upstreamClosed"] == slow["requests"], slow
ffprobe, listeners = residue()
assert ffprobe == 0 and listeners == baseline_listeners, (ffprobe, listeners)
exec_projects("rm", "-f", "/tmp/ul10-sample.mp4")
print(f"PASS default 15 s deadline: refused at {slow['elapsedMs']} ms, upstream closed, "
      f"{slow['served']} bytes read, no ffprobe or relay left")

# 3. Byte limit alone.
recreate(max_bytes=BYTES_LIMIT)
media = inspect()["media"]
legacy_status, legacy_s = legacy("bytes-legacy.mp4")
direct_status, direct_s = direct("bytes-direct.mp4")
print(f"  bytes: legacy {legacy_status} in {legacy_s:.2f} s, direct confirm {direct_status} "
      f"in {direct_s:.2f} s")
assert (legacy_status, direct_status) == (400, 400)
assert legacy_s < 10 and direct_s < 10   # refused by bytes, not by the 15 s deadline
settled({"bytes-legacy.mp4", "bytes-direct.mp4"}, media)
print(f"PASS byte limit ({BYTES_LIMIT} B) alone: both transports refused, no orphan, "
      "no slot, no process")

# 4. Time limit alone.
recreate(timeout_ms=TIME_LIMIT_MS)
legacy_status, legacy_s = legacy("time-legacy.mp4")
direct_status, direct_s = direct("time-direct.mp4")
print(f"  time: legacy {legacy_status} in {legacy_s:.2f} s, direct confirm {direct_status} "
      f"in {direct_s:.2f} s")
assert (legacy_status, direct_status) == (400, 400)
settled({"time-legacy.mp4", "time-direct.mp4"}, media)
print(f"PASS time limit ({TIME_LIMIT_MS} ms) alone: both transports refused, no orphan, "
      "no slot, no process")

# 5. Restore.
recreate()
assert legacy("restored-legacy.mp4")[0] == 204
assert inspect()["media"] == media + 1
print("PASS restored decided limits: valid video accepted again")
print("UL-10 probe limits: all checks passed")
