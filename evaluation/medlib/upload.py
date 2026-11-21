"""Instrumented multipart upload over a raw (TLS) socket.

Separates t_headers / t_send / t_first_byte / t_ready, streams the file in 1 MiB
blocks (never loads it whole), optionally rate-limits, and notices a response that
arrives while the body is still being sent (early rejection, U19).
"""
from __future__ import annotations

import os
import socket
import ssl
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from .config import SETTINGS
from .util import snippet

BLOCK = 1 << 20


def _ctx() -> ssl.SSLContext:
    if SETTINGS.cacert:
        ctx = ssl.create_default_context(cafile=SETTINGS.cacert)
    else:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _try_recv(sock: socket.socket, timeout: float) -> bytes | None:
    """Non-blocking read: None = nothing yet, b'' = closed by peer."""
    sock.setblocking(False)
    try:
        return sock.recv(65536)
    except (ssl.SSLWantReadError, ssl.SSLWantWriteError, BlockingIOError):
        return None
    except (ConnectionResetError, BrokenPipeError, ssl.SSLError, OSError):
        return b""
    finally:
        sock.settimeout(timeout)


def _read_response(sock: socket.socket, buf: bytes, deadline: float) -> tuple[int | None, dict, bytes]:
    def recv() -> bytes:
        sock.settimeout(max(0.5, deadline - time.monotonic()))
        try:
            return sock.recv(65536)
        except (socket.timeout, TimeoutError):
            raise
        except (ConnectionResetError, ssl.SSLError, OSError):
            return b""

    while b"\r\n\r\n" not in buf:
        if time.monotonic() > deadline:
            raise TimeoutError("response headers")
        d = recv()
        if not d:
            break
        buf += d
    if b"\r\n\r\n" not in buf:
        return None, {}, buf
    head, body = buf.split(b"\r\n\r\n", 1)
    lines = head.decode("latin-1").split("\r\n")
    try:
        status = int(lines[0].split()[1])
    except (IndexError, ValueError):
        return None, {}, buf
    headers = {}
    for line in lines[1:]:
        k, _, v = line.partition(":")
        headers[k.strip().lower()] = v.strip()
    if "content-length" in headers:
        need = int(headers["content-length"])
        while len(body) < need and time.monotonic() < deadline:
            d = recv()
            if not d:
                break
            body += d
    elif headers.get("transfer-encoding", "").lower() == "chunked":
        while not body.endswith(b"0\r\n\r\n") and time.monotonic() < deadline:
            d = recv()
            if not d:
                break
            body += d
        body = _dechunk(body)
    elif status not in (204, 304):
        while time.monotonic() < deadline:
            d = recv()
            if not d:
                break
            body += d
    return status, headers, body


def _dechunk(data: bytes) -> bytes:
    out, i = b"", 0
    while i < len(data):
        j = data.find(b"\r\n", i)
        if j < 0:
            break
        try:
            n = int(data[i:j].split(b";")[0], 16)
        except ValueError:
            break
        if n == 0:
            break
        out += data[j + 2:j + 2 + n]
        i = j + 2 + n + 2
    return out


def upload(url: str, *, field: str, filename: str, ctype: str, path: Path | None = None,
           data: bytes | None = None, headers: dict | None = None, rate_mib_s: float | None = None,
           send_timeout: float = 60, total_timeout: float = 1200) -> dict:
    u = urlsplit(url)
    host = u.hostname or "localhost"
    port = u.port or (443 if u.scheme == "https" else 80)
    target = u.path + (f"?{u.query}" if u.query else "")
    size = path.stat().st_size if path is not None else len(data or b"")
    boundary = "----med" + uuid.uuid4().hex
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
            f"filename=\"{filename}\"\r\nContent-Type: {ctype}\r\n\r\n").encode()
    tail = f"\r\n--{boundary}--\r\n".encode()
    length = len(head) + size + len(tail)
    hdrs = {"Host": f"{host}:{port}", "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(length), "Connection": "close", "Accept": "*/*"}
    hdrs.update(headers or {})
    request_head = (f"POST {target} HTTP/1.1\r\n" + "".join(f"{k}: {v}\r\n" for k, v in hdrs.items())
                    + "\r\n").encode()

    rec = {"bytes": size, "status": None, "error": None, "early_response": False,
           "bytes_sent": 0, "bytes_sent_at_response": None}
    t0 = time.monotonic()
    deadline = t0 + total_timeout
    early = b""
    sock = None
    try:
        raw = socket.create_connection((host, port), timeout=30)
        sock = _ctx().wrap_socket(raw, server_hostname=host) if u.scheme == "https" else raw
        sock.settimeout(send_timeout)
        sock.sendall(request_head)
        t_headers = time.monotonic()
        rec["t_headers_ms"] = (t_headers - t0) * 1000
        sent_body = 0
        stalled = False

        def send(chunk: bytes) -> bool:
            nonlocal sent_body, early
            got = _try_recv(sock, send_timeout)
            if got is not None:
                early = got
                return False
            try:
                sock.sendall(chunk)
            except (socket.timeout, TimeoutError):
                rec["send_stalled"] = True
                return False
            except (BrokenPipeError, ConnectionResetError, ssl.SSLError, OSError) as exc:
                rec["send_error"] = repr(exc)[:120]
                return False
            sent_body += len(chunk)
            if rate_mib_s:
                expected = sent_body / (rate_mib_s * BLOCK)
                elapsed = time.monotonic() - t_headers
                if expected > elapsed:
                    time.sleep(expected - elapsed)
            return True

        ok = send(head)
        if ok:
            if path is not None:
                with open(path, "rb") as f:
                    while ok:
                        chunk = f.read(BLOCK)
                        if not chunk:
                            break
                        ok = send(chunk)
            elif data:
                for i in range(0, len(data), BLOCK):
                    ok = send(data[i:i + BLOCK])
                    if not ok:
                        break
        if ok:
            ok = send(tail)
        rec["bytes_sent"] = sent_body
        if ok:
            t_send = time.monotonic()
            rec["t_send_ms"] = (t_send - t0) * 1000
        else:
            rec["early_response"] = bool(early)
            rec["bytes_sent_at_response"] = sent_body
            t_send = None
        status, resp_headers, body = None, {}, b""
        t_first = None
        if early:
            t_first = time.monotonic()
        try:
            status, resp_headers, body = _read_response(sock, early, deadline)
        except (TimeoutError, socket.timeout):
            rec["error"] = "timeout"
        if t_first is None and status is not None:
            t_first = time.monotonic()
        t_ready = time.monotonic()
        rec.update({
            "status": status,
            "t_first_byte_ms": None if t_first is None else (t_first - t0) * 1000,
            "t_ready_ms": (t_ready - t0) * 1000,
            "total_ms": (t_ready - t0) * 1000,
            "post_send_ms": None if t_send is None else (t_ready - t_send) * 1000,
            "response_after_headers_ms": None if t_first is None else (t_first - t_headers) * 1000,
            "body": snippet(body, 200),
            "x_project_version": resp_headers.get("x-project-version"),
        })
        if status is None and not rec["error"]:
            rec["error"] = "no_response"
    except Exception as exc:  # noqa: BLE001
        rec["error"] = repr(exc)[:200]
        rec["total_ms"] = (time.monotonic() - t0) * 1000
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
    return rec


def file_size(path: Path) -> int:
    return os.path.getsize(path)
