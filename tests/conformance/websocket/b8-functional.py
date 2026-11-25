"""B8 network conformance; trusted synthetic fixtures, no credentials in output.

Run with in-network.sh. Optional `outage` mode coordinates stop/start with the
host through READY markers; it never gains access to the Docker socket.
"""
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from b4_common import (AUDIENCE, BASE, CA, ISSUER, ROOT, SESSION_SECRET, SESSION_TYP,
                       TLS, Results, call, direct, project_version, register)
import jwt
import requests
import socketio

os.environ["SSL_CERT_FILE"] = CA
os.environ["REQUESTS_CA_BUNDLE"] = CA
PUBLIC = BASE.removesuffix("/api-gateway/")
res = Results("B8 WebSocket")
sockets = []


def connect(token, auth=None):
    http = requests.Session()
    http.trust_env = False
    http.verify = CA
    stages = []
    class SafeTrace(logging.Handler):
        def emit(self, record):
            if len(stages) >= 16:
                return
            template = str(record.msg)
            if template in ("Sending packet %s data %s", "Received packet %s data %s"):
                kind = record.args[0]
                if kind in ("OPEN", "CLOSE", "PING", "PONG", "MESSAGE", "UPGRADE", "NOOP"):
                    data = record.args[1]
                    stages.append({"stage": "send" if template.startswith("Sending") else "receive",
                                   "packet": kind, "bytes": len(data.encode()) if isinstance(data, str) else None})
            elif "WebSocket connection was closed" in template:
                stages.append({"stage": "write_closed"})
            elif template.startswith("WebSocket connection accepted"):
                stages.append({"stage": "engine_open"})
            elif template.startswith("Namespace") and "connected" in template:
                stages.append({"stage": "namespace_connected"})
    logger = logging.Logger("B8 safe protocol trace", level=logging.INFO)
    logger.propagate = False
    logger.addHandler(SafeTrace())
    client = socketio.Client(reconnection=False, http_session=http, logger=logger, engineio_logger=logger)
    client.safe_trace = stages
    client.received = []
    client.refusal = None
    client.failure_kind = None
    started = time.monotonic()
    client.on("*", lambda event, data=None: client.received.append((time.monotonic(), event, data)))
    @client.on("connect_error")
    def refused(data):
        if isinstance(data, dict):
            candidate = data.get("data", {}).get("status")
            if candidate in ("denied", "session_expired", "rate_limited", "invalid_request"):
                client.refusal = candidate
    try:
        client.connect(PUBLIC, transports=["websocket"], auth=auth if auth is not None else {"token": token}, wait_timeout=5)
    except Exception as error:
        client.failure_kind = type(error).__name__
    client.connect_ms = round((time.monotonic() - started) * 1000, 2)
    sockets.append(client)
    return client


def join(client, project, access):
    try:
        return client.call("join-project", {"projectId": project, "access": access}, timeout=2).get("status")
    except Exception:
        return "no_callback"


def publish(project, user=None, kind="project-op"):
    msg = {"projectId": project, "user": user, "type": kind, "op": {"newVersion": 12345}}
    if kind == "preview-ready":
        msg.update(messageId="update-client-preview-fixture", img_url="fixture-preview", status="success")
    elif kind == "video-progress":
        msg.update(messageId="update-client-video-progress-fixture", percent=50, status="success")
    http = requests.Session()
    http.trust_env = False
    response = http.post("https://rabbitmq:15671/api/exchanges/%2F/picturas/publish", verify=CA,
                         auth=("picturas_admin", (ROOT / "values/rabbit_admin").read_text().strip()),
                         json={"properties": {}, "routing_key": "ws_queue", "payload": json.dumps(msg),
                               "payload_encoding": "string"}, timeout=5)
    assert response.status_code == 200 and response.json().get("routed"), "fixture publish failed"


def token(subject, seconds=300, **changes):
    now = int(time.time())
    payload = {"id": subject, "sub": subject, "iat": now, "exp": now + seconds, "iss": ISSUER, "aud": AUDIENCE}
    payload.update(changes)
    return jwt.encode(payload, SESSION_SECRET, algorithm="HS256", headers={"typ": SESSION_TYP})


owner, outsider, reader = register(), register(), register()
pid = call("POST", f"projects/{owner['id']}", owner["token"], body={"name": "B8 fixture"}).json()["_id"]


def share(permission="read"):
    return call("POST", f"projects/{owner['id']}/{pid}/share", owner["token"], body={"permission": permission},
                headers={"X-Project-Version": project_version(owner, pid)}).json()["id"]


def revoke(link):
    response = call("DELETE", f"projects/{owner['id']}/{pid}/share/{link}", owner["token"],
                    headers={"X-Project-Version": project_version(owner, pid)})
    assert response.status_code < 300, "fixture revoke failed"
    return time.monotonic()


try:
    own = connect(owner["token"])
    res.check("WS-T01", "owner joins", join(own, pid, {"kind": "owner"}), "joined")
    if "outage" in sys.argv:
        print("READY_STOP_PROJECTS", flush=True)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                if call("GET", f"projects/{owner['id']}/{pid}", owner["token"]).status_code >= 500:
                    break
            except Exception:
                break
            time.sleep(0.1)
        res.check("WS-T02", "outage refuses fresh join", join(own, pid, {"kind": "owner"}), "unavailable")
        time.sleep(5.1)
        since = time.monotonic()
        publish(pid, owner["id"], "preview-ready")
        publish(pid, owner["id"], "video-progress")
        publish(pid)
        time.sleep(0.5)
        res.check("WS-T04", "outage does not extend personal/project emission deadline",
                  any(t >= since and e in ("preview-ready", "video-progress", "project-op") for t, e, _ in own.received), False)
        print("READY_START_PROJECTS", flush=True)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                if call("GET", f"projects/{owner['id']}/{pid}", owner["token"]).status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(0.2)
        # Decision 53 (D-30 A): the suspended context resumes on its own fresh allow, without a join.
        time.sleep(1.0)
        since = time.monotonic()
        publish(pid)
        time.sleep(0.5)
        res.check("WS-T02", "recovery resumes the suspended context without a new join",
                  any(t >= since and e == "project-op" for t, e, _ in own.received), True)
        res.check("WS-T02", "recovery allows a fresh join", join(own, pid, {"kind": "owner"}), "joined")
        res.finish()
        sys.exit(0)

    read_link, edit_link = share(), share("edit")
    before = project_version(owner, pid)
    read = connect(reader["token"])
    res.check("WS-T01", "reader joins without editing", join(read, pid, {"kind": "share", "shareId": read_link}), "joined")
    res.check("WS-T01", "WS authorization does not mutate project version", project_version(owner, pid), before)
    attack = connect(outsider["token"])
    res.check("WS-T01", "unrelated owner context denied", join(attack, pid, {"kind": "owner"}), "denied")
    res.check("WS-T01", "unknown share denied", join(attack, pid, {"kind": "share", "shareId": "unknown"}), "denied")
    for bad in (None, "invalid", token(owner["id"], -1), token(owner["id"], 300, aud="other")):
        res.check("S10", "missing/invalid/expired/wrong-audience JWT refused", connect(bad).connected, False)
    # Exact byte limits use the independent raw-frame/ACK control in b8-wire-limits.py.
    anonymous = register("anonymous")
    anon = connect(anonymous["token"])
    res.check("WS-T01", "anonymous JWT with presented share allowed", join(anon, pid, {"kind": "share", "shareId": edit_link}), "joined")

    path = f"/internal/ws/projects/{pid}/authorize"
    evaluations = []
    for n, (sub, access) in enumerate(((owner["id"], {"kind": "owner"}),
        (outsider["id"], {"kind": "owner"}), (reader["id"], {"kind": "share", "shareId": read_link}),
        (reader["id"], {"kind": "share", "shareId": "invalid"}))):
        evaluations.append({"ref": f"member-{n}", "generation": 1, "sequence": 1, "sub": sub,
                            "exp": int(time.time()) + 60, "access": access})
    body = {"requestId": "mixed", "evaluations": evaluations}
    code, data = direct("projects", "POST", path, peer="ws_gateway", body=body, want_body=True)
    res.check("WS-T08", "individual owner/outsider/read/invalid decisions",
              (code, [d["decision"] for d in data.get("decisions", [])]),
              lambda value: value == (200, ["allow", "deny", "allow", "deny"]))
    for peer in ("api_gateway", "users", "projects", "img_storage"):
        res.check("WS-T09", "other CA-valid service cannot delegate",
                  direct("projects", "POST", path, peer=peer, body=body, headers={"X-Caller-Id": "ws_gateway"}), 403)
    res.check("WS-T09", "no certificate cannot delegate", direct("projects", "POST", path, body=body), TLS)
    res.check("WS-T09", "WS cannot use unrelated project operation",
              direct("projects", "GET", f"/{owner['id']}/{pid}", peer="ws_gateway"), 403)

    too_many = {"requestId": "limit", "evaluations": [{**evaluations[0], "ref": f"ref-{n}"} for n in range(51)]}
    res.check("WS-B1", "51 evaluations rejected", direct("projects", "POST", path, peer="ws_gateway", body=too_many), 400)
    fifty = {**too_many, "evaluations": too_many["evaluations"][:50]}
    code, data = direct("projects", "POST", path, peer="ws_gateway", body=fifty, want_body=True)
    res.check("WS-B1", "50 evaluations accepted without truncation", code == 200 and len(data.get("decisions", [])) == 50, True)
    exact = {**body, "padding": ""}
    exact["padding"] = "x" * (65536 - len(json.dumps(exact).encode()))
    res.check("WS-B1", "exact 64 KiB JSON body accepted", direct("projects", "POST", path, peer="ws_gateway", body=exact), 200)
    exact["padding"] += "x"
    res.check("WS-B1", "64 KiB plus one JSON body rejected", direct("projects", "POST", path, peer="ws_gateway", body=exact), 413)
    too_large = {**body, "padding": "x" * 65536}
    res.check("WS-B1", "HTTP body above 64 KiB rejected", direct("projects", "POST", path, peer="ws_gateway", body=too_large), 413)

    publish(pid, owner["id"], "preview-ready")
    publish(pid, owner["id"], "video-progress")
    time.sleep(0.3)
    res.check("WS-E1", "authorized owner receives personal preview/progress",
              {e for _, e, _ in own.received}.issuperset({"preview-ready", "video-progress"}), True)
    res.check("WS-E1", "unjoined outsider gets no protected personal/project events",
              any(e in ("preview-ready", "video-progress", "project-op") for _, e, _ in attack.received), False)
    ack = read.call("join-project", {"projectId": pid, "access": {"kind": "share", "shareId": edit_link}}, timeout=2)
    res.check("WS-T06", "second presented path joins", ack.get("status"), "joined")
    revoke(read_link)
    time.sleep(1.3)
    since = time.monotonic(); publish(pid); time.sleep(0.3)
    res.check("WS-T06", "another presented path survives denial", any(t >= since and e == "project-op" for t, e, _ in read.received), True)
    at = revoke(edit_link)
    for _ in range(26):
        publish(pid)
        publish(pid, reader["id"], "preview-ready")
        publish(pid, reader["id"], "video-progress")
        time.sleep(0.2)
    late = [t - at for t, e, _ in read.received if t > at and e in ("project-op", "preview-ready", "video-progress")]
    res.check("WS-T03", "revocation has no events after 5 seconds", any(t > 5 for t in late), False)
    res.check("WS-T03", "observed last protected event within 2 second target", max(late, default=0) <= 2, True)
    res.check("WS-T03", "revoked link cannot rejoin", join(read, pid, {"kind": "share", "shareId": read_link}), "denied")
    own.emit("leave-project", pid)
    time.sleep(0.1)
    since = time.monotonic(); publish(pid, owner["id"], "preview-ready"); time.sleep(0.2)
    res.check("WS-T05/E1", "leave removes personal authorization", any(t >= since and e == "preview-ready" for t, e, _ in own.received), False)
    res.check("WS-T05", "rejoin consults anew", join(own, pid, {"kind": "owner"}), "joined")

    short = connect(token(owner["id"], 2))
    res.check("WS-T07", "short-lived JWT joins", join(short, pid, {"kind": "owner"}), "joined")
    time.sleep(2.2)
    res.check("WS-T07", "JWT expiry terminates transport", short.connected, False)
    res.finish()
finally:
    for client in sockets:
        if client.connected:
            client.disconnect()
