"""Exact byte controls using raw Engine.IO/Socket.IO frames over verified wss.

This independent client avoids background writer threads and does not log packet
contents. A transport-sized positive event must get its application ACK, so a
lost client write cannot be mistaken for acceptance merely because it is open.
"""
import asyncio
import json
import ssl
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from b4_common import BASE, CA, register
import aiohttp

owner = register()
url = BASE.removesuffix("/api-gateway/").replace("https://", "wss://") + "/socket.io/?EIO=4&transport=websocket"
tls = ssl.create_default_context(cafile=CA)
encode = lambda data: json.dumps(data, ensure_ascii=False, separators=(",", ":"))


async def receive(ws):
    while True:
        message = await ws.receive(timeout=5)
        if message.type != aiohttp.WSMsgType.TEXT:
            return None
        if message.data == "2":
            await ws.send_str("3")
            continue
        return message.data


async def connect(http, size):
    ws = await http.ws_connect(url, max_msg_size=100000)
    opened = await receive(ws)
    assert opened and opened.startswith("0"), "Engine.IO OPEN absent"
    auth = {"token": owner["token"], "padding": "é"}
    auth["padding"] += "x" * (size - len(encode(auth).encode()))
    body = encode(auth)
    assert len(body.encode()) == size
    await ws.send_str("40" + body)
    answer = await receive(ws)
    return ws, bool(answer and answer.startswith("40"))


async def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    passed = 0
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=tls)) as http:
        for n in range(rounds):
            for size in (8191, 8192, 8193):
                at = time.monotonic()
                ws, accepted = await connect(http, size)
                await ws.close()
                assert accepted == (size <= 8192), f"handshake {size}: unexpected {accepted}"
                passed += 1
                print(json.dumps({"case": "WS-B1 handshake", "round": n + 1, "bytes": size,
                    "accepted": accepted, "ms": round((time.monotonic() - at) * 1000, 2)}), flush=True)
        for size in (65536, 65537):
            ws, accepted = await connect(http, 1024)
            assert accepted, "normal authenticated control failed"
            data = ["join-project", {"projectId": "000000000000000000000001", "access": {"kind": "owner"}, "padding": ""}]
            prefix = "421"  # Engine.IO MESSAGE + Socket.IO EVENT + ACK id 1.
            data[1]["padding"] = "x" * (size - len((prefix + encode(data)).encode()))
            packet = prefix + encode(data)
            assert len(packet.encode()) == size
            await ws.send_str(packet)
            answer = await receive(ws)
            if size == 65536:
                assert answer and answer.startswith("431"), "accepted frame did not reach the application"
                assert json.loads(answer[3:])[0]["status"] == "invalid_request", "expected application-size refusal"
            else:
                assert not answer or not answer.startswith("431"), "oversized frame reached the application"
            await ws.close()
            passed += 1
            print(json.dumps({"case": "WS-B1 transport", "bytes": size,
                "application_ack": bool(answer and answer.startswith("431"))}), flush=True)
        # Escapes must not bypass the wire limit by normalizing to a shorter
        # Unicode string inside the decoded authentication object.
        ws, accepted = await connect(http, 1024)
        assert accepted
        await ws.close()
        ws = await http.ws_connect(url)
        assert (await receive(ws)).startswith("0")
        auth = {"token": owner["token"], "padding": "é"}
        auth["padding"] += "x" * (8192 - len(encode(auth).encode()))
        escaped = json.dumps(auth, ensure_ascii=True, separators=(",", ":"))
        assert len(escaped.encode()) > 8192
        await ws.send_str("40" + escaped)
        answer = await receive(ws)
        assert not answer or not answer.startswith("40"), "escaped handshake bypassed the byte cap"
        await ws.close(); passed += 1
        print(json.dumps({"case": "WS-B1 escaped handshake", "received_bytes": len(escaped.encode()), "accepted": False}), flush=True)
        for size in (4096, 4097):
            ws, accepted = await connect(http, 1024)
            assert accepted
            payload = {"projectId": "000000000000000000000001", "access": {"kind": "share", "shareId": "é"}}
            payload["access"]["shareId"] += "x" * (size - len(encode(payload).encode()))
            await ws.send_str('421["join-project",' + encode(payload) + ']')
            answer = await receive(ws)
            assert answer and answer.startswith("431"), "join byte control needs an explicit callback"
            expected = "denied" if size == 4096 else "invalid_request"
            assert json.loads(answer[3:])[0]["status"] == expected, "join limit/schema decision confused"
            await ws.close(); passed += 1
            print(json.dumps({"case": "WS-B1 join JSON", "bytes": size, "callback": expected}), flush=True)
        ws, accepted = await connect(http, 1024)
        assert accepted
        payload = {"projectId": "000000000000000000000001", "access": {"kind": "share", "shareId": "é" * 800}}
        escaped = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        assert len(encode(payload).encode()) < 4096 < len(escaped.encode())
        await ws.send_str('421["join-project",' + escaped + ']')
        answer = await receive(ws)
        assert answer and answer.startswith("431") and json.loads(answer[3:])[0]["status"] == "invalid_request"
        await ws.close(); passed += 1
        print(json.dumps({"case": "WS-B1 escaped join", "received_bytes": len(escaped.encode()), "callback": "invalid_request"}), flush=True)
    print(f"B8 raw wire limits: {passed}/{rounds * 3 + 6} passed", flush=True)


asyncio.run(main())
