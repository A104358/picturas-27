"""F08: recovery of each Node service after its process is killed (B3, D-04).

For each service, SIGKILL the `node` process inside the container (what an OOM kill does)
and measure, from the kill:
  t_restart  the container is running again (Docker restart policy),
  t_healthy  its healthcheck passes again,
  t_served   a request through nginx that needs the service answers below 500
             (api_gateway, users, projects, subscriptions, ws_gateway; img_storage is
             only reachable from projects, so its healthy time stands for it).
Minimum: recovery <= 30 s; target <= 10 s.

Usage: python3 f08-restart.py [compose-project] [base-url]
       (defaults: picturas-dev, https://localhost:8080). Only synthetic accounts are created;
       no token is printed.
"""
import json
import os
import secrets
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests

PROJECT = sys.argv[1] if len(sys.argv) > 1 else "picturas-dev"
BASE = (sys.argv[2] if len(sys.argv) > 2 else "https://localhost:8080").rstrip("/")
CA = str(Path(os.environ["PICTURAS_SECRETS_DIR"]) / "pki/ca/ca.crt")
LIMIT_S, TARGET_S, DEADLINE_S = 30, 10, 90
if PROJECT == "picturas-nfr":
    sys.exit("refusing the official MF stack")

http = requests.Session()
http.trust_env = False


def docker(*args):
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=60)


def container(service):
    return f"{PROJECT}-{service}-1"


def restarts(service):
    return docker("inspect", container(service), "--format", "{{.RestartCount}}").stdout.strip()


def state(service):
    out = docker("inspect", container(service), "--format", "{{json .State}}").stdout
    return json.loads(out) if out.strip() else {}


def api(method, path, token=None, body=None):
    hdr = {"Authorization": "Bearer " + token} if token else {}
    try:
        return http.request(method, f"{BASE}/api-gateway/{path}", json=body, headers=hdr,
                            verify=CA, timeout=5).status_code
    except requests.RequestException:
        return None


def socket_io():
    try:
        return http.get(f"{BASE}/socket.io/?EIO=4&transport=polling", verify=CA, timeout=5).status_code
    except requests.RequestException:
        return None


r = http.post(f"{BASE}/api-gateway/users/", verify=CA, timeout=30,
              json={"name": "F08 fixture", "email": f"f08-{uuid.uuid4().hex}@example.invalid",
                    "password": secrets.token_urlsafe(24), "type": "free"})
assert r.status_code == 201, ("register", r.status_code)
uid, token = r.json()["user"]["_id"], r.json()["jwt"]

SERVED = {
    "api_gateway": lambda: api("GET", f"users/{uid}", token) == 200,
    "users": lambda: api("GET", f"users/{uid}", token) == 200,
    "projects": lambda: api("GET", f"projects/{uid}", token) == 200,
    "subscriptions": lambda: (api("GET", f"subscriptions/{uid}", token) or 599) < 500,
    "ws_gateway": lambda: socket_io() == 200,
    "img_storage": None,
}
# The node main thread is named "node" (Node 18) or "MainThread" (Node 26), as in med.py.
KILL_NODE = ('for d in /proc/[0-9]*; do case "$(cat $d/comm 2>/dev/null)" in node*|MainThread) '
             'kill -9 "${d#/proc/}" && echo killed;; esac; done')

rows, failed = [], False
for service, served in SERVED.items():
    before = state(service)
    if served and not served():
        print(f"SKIP {service}: not served before the kill")
        failed = True
        continue
    started_before, count_before = before.get("StartedAt"), restarts(service)
    t0 = time.monotonic()
    out = docker("exec", container(service), "sh", "-c", KILL_NODE).stdout
    if "killed" not in out:
        print(f"FAIL {service}: no node process found")
        failed = True
        continue
    t_restart = t_healthy = t_served = None
    while time.monotonic() - t0 < DEADLINE_S:
        now = time.monotonic() - t0
        st = state(service)
        if t_restart is None and st.get("Running") and st.get("StartedAt") != started_before:
            t_restart = now
        if t_restart is not None and t_healthy is None and \
                st.get("Health", {}).get("Status") == "healthy":
            t_healthy = now
        if t_restart is not None and t_served is None and served and served():
            t_served = now
        if t_healthy is not None and (t_served is not None or not served):
            break
        time.sleep(0.25)
    recovered = t_served if served else t_healthy
    ok = recovered is not None and recovered <= LIMIT_S
    failed |= not ok
    fmt = lambda v: "-" if v is None else f"{v:.1f}s"
    print(f"{'PASS' if ok else 'FAIL'} {service}: restart {fmt(t_restart)}, healthy {fmt(t_healthy)}, "
          f"served {fmt(t_served) if served else 'n/a'}; recovery {fmt(recovered)} "
          f"({'target met' if recovered is not None and recovered <= TARGET_S else 'target missed'}); "
          f"restart count {count_before}->{restarts(service)}")
    rows.append((service, recovered))

print(f"F08: {sum(1 for _, v in rows if v is not None and v <= LIMIT_S)}/{len(SERVED)} services "
      f"recovered within {LIMIT_S} s; {sum(1 for _, v in rows if v is not None and v <= TARGET_S)} "
      f"within the {TARGET_S} s target")
sys.exit(1 if failed else 0)
