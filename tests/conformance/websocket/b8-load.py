"""Physical B8 WS-N1/J1/P1/L1/L2 workloads over wss, using synthetic sessions.

The trusted harness signs distinct fixture subjects; no real accounts or clocks
are changed. All calls use the delivered limits. Run with in-network.sh.
"""
import asyncio
import base64
import json
import os
import ssl
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from b4_common import AUDIENCE, BASE, CA, ISSUER, ROOT, SESSION_SECRET, SESSION_TYP, call, project_version, register
import aiohttp
import jwt
import socketio

PUBLIC = BASE.removesuffix("/api-gateway/")
TLS = ssl.create_default_context(cafile=CA)
owner = register()
admin = (ROOT / "values/rabbit_admin").read_text().strip()


def fixture_token():
    subject = uuid.uuid4().hex[:24]
    now = int(time.time())
    return jwt.encode({"id": subject, "sub": subject, "iat": now, "exp": now + 600,
                       "iss": ISSUER, "aud": AUDIENCE}, SESSION_SECRET, algorithm="HS256", headers={"typ": SESSION_TYP})


def project():
    pid = call("POST", f"projects/{owner['id']}", owner["token"], body={"name": "B8 physical workload"}).json()["_id"]
    links = []
    for _ in range(2):
        r = call("POST", f"projects/{owner['id']}/{pid}/share", owner["token"], body={"permission": "read"},
                 headers={"X-Project-Version": project_version(owner, pid)})
        assert r.status_code == 201, "fixture link creation failed"
        links.append(r.json()["id"])
    return pid, links


async def publish(http, pid, sequence):
    message = {"type": "project-op", "projectId": pid,
               "op": {"fixtureSequence": sequence, "sent": time.monotonic()}}
    async with http.post("https://rabbitmq:15671/api/exchanges/%2F/picturas/publish",
                         headers={"Authorization": "Basic " + base64.b64encode(("picturas_admin:" + admin).encode()).decode()},
                         json={"properties": {}, "routing_key": "ws_queue", "payload": json.dumps(message),
                               "payload_encoding": "string"}) as r:
        data = await r.json()
        assert r.status == 200 and data.get("routed"), "fixture publish failed"


async def scenario(name, sizes, context_limit=False):
    projects = [project() for _ in (range(8) if context_limit else sizes)]
    clients, events, removals, join_ms, controls = [], [], [], [], []
    started = time.monotonic()
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=TLS, limit=0)) as http:
        async def connection(index):
            client = socketio.AsyncClient(reconnection=False, http_session=http, request_timeout=10)
            events.append([])
            removals.append([])

            @client.on("project-op")
            async def received(data):
                events[index].append((time.monotonic(), data))

            @client.on("project-access")
            async def removed(data):
                removals[index].append(data.get("status"))

            await client.connect(PUBLIC, transports=["websocket"], auth={"token": fixture_token()}, wait_timeout=10)
            clients.append(client)
            return client

        async def join(client, pid, link):
            at = time.monotonic()
            result = await client.call("join-project", {"projectId": pid, "access": {"kind": "share", "shareId": link}}, timeout=2)
            join_ms.append((time.monotonic() - at) * 1000)
            assert result.get("status") == "joined", f"{name}: preload refused: {result.get('status')} / {result.get('reason')}"
            # Gradual preload; never confuse rate-limited flood with capacity.
            await asyncio.sleep(0.012)

        try:
            if context_limit:
                for n in range(512):
                    client = await connection(n)
                    for pid, links in projects:
                        await join(client, pid, links[0])
            else:
                for p, size in enumerate(sizes):
                    pid, links = projects[p]
                    for n in range(size):
                        index = len(clients)
                        client = await connection(index)
                        control = n == size - 1
                        controls.append((index, p, control))
                        await join(client, pid, links[1 if control else 0])
            await asyncio.sleep(2.1)
            assert all(client.connected for client in clients), f"{name}: connections lost during preload"
            assert not any(removals), f"{name}: contexts expired during preload; cap precondition absent"

            # Every participant must receive at least three distinct events before
            # revocation; the cap test requires all eight rooms to remain live.
            for seq in range(3):
                await asyncio.gather(*(publish(http, pid, seq) for pid, _ in projects))
                await asyncio.sleep(0.15)
            if context_limit:
                assert all(len(data) >= 24 for data in events), "L2: 4096 live-context precondition absent"
                extra = socketio.AsyncClient(reconnection=False, http_session=http)
                admitted = False
                try:
                    await extra.connect(PUBLIC, transports=["websocket"], auth={"token": fixture_token()}, wait_timeout=3)
                    admitted = True
                except Exception:
                    pass
                if extra.connected:
                    await extra.disconnect()
                assert not admitted, "L1: 513th connection admitted"
                pid, links = project()
                result = await clients[0].call("join-project", {"projectId": pid,
                    "access": {"kind": "share", "shareId": links[0]}}, timeout=2)
                assert result.get("reason") == "context_limit", "L2: 4097th context not refused by context cap"
                assert not any(removals), "L2: existing authorization displaced"
                print(json.dumps({"case": "WS-L1/L2", "connections_live": 512, "contexts_live": 4096,
                    "excess_connection": "refused", "excess_context": "context_limit",
                    "preload_seconds": round(time.monotonic() - started, 2),
                    "join_max_ms": round(max(join_ms), 2), "unintended_removals": 0}), flush=True)
                return

            assert all(len(data) >= 3 for data in events), f"{name}: legitimate preload control incomplete"
            revoked = []
            for pid, links in projects:
                r = call("DELETE", f"projects/{owner['id']}/{pid}/share/{links[0]}", owner["token"],
                         headers={"X-Project-Version": project_version(owner, pid)})
                assert r.status_code < 300, "fixture revocation failed"
                revoked.append(time.monotonic())
            for seq in range(3, 31):
                await asyncio.gather(*(publish(http, pid, seq) for pid, _ in projects))
                await asyncio.sleep(0.2)
            await asyncio.sleep(0.3)
            last_event = 0.0
            for index, p, control in controls:
                got = {data.get("op", {}).get("fixtureSequence") for _, data in events[index]}
                if control:
                    assert set(range(3, 31)) <= got, f"{name}: nonrevoked control starved"
                else:
                    late = [at - revoked[p] for at, data in events[index]
                            if data.get("op", {}).get("sent", 0) > revoked[p]]
                    last_event = max(last_event, max(late, default=0))
                    assert not any(at > 5 for at in late), f"{name}: event after 5s"
            assert last_event <= 2, f"{name}: cut target exceeded: {last_event:.3f}s"
            print(json.dumps({"case": name, "projects": len(sizes), "connections": len(clients),
                "contexts_before_revocation": len(clients), "preload_and_cut_seconds": round(time.monotonic() - started, 2),
                "join_max_ms": round(max(join_ms), 2), "cut_last_event_max_ms": round(last_event * 1000, 2),
                "events_after_5s": 0, "nonrevoked_controls_complete": True}), flush=True)
        finally:
            await asyncio.gather(*(client.disconnect() for client in clients if client.connected), return_exceptions=True)


async def main():
    cases = sys.argv[1:] or ["N1", "J1", "P1", "L2"]
    for name in cases:
        if name == "N1": await scenario("WS-N1", [5] * 10)
        elif name == "J1": await scenario("WS-J1", [500, 5, 5])
        elif name == "P1": await scenario("WS-P1", [5] * 40)
        elif name == "L2": await scenario("WS-L1/L2", [], context_limit=True)
        else: raise SystemExit("Unknown B8 workload")
        await asyncio.sleep(2.1)


asyncio.run(main())
