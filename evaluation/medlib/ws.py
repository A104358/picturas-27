"""Socket.IO client that records every event with a monotonic timestamp."""
from __future__ import annotations

import threading
import time

import socketio

from .config import SETTINGS


class WS:
    def __init__(self, label: str):
        self.label = label
        self.events: list[tuple[float, str, object]] = []
        self.disconnected_at: float | None = None
        self.connect_error: str | None = None
        self._lock = threading.Lock()
        # Client-side verification is off for the self-signed nginx (recorded in the manifest).
        self.sio = socketio.Client(reconnection=False, ssl_verify=False,
                                   logger=False, engineio_logger=False)

        @self.sio.on("*")
        def _any(event, data=None):  # noqa: ANN001
            with self._lock:
                self.events.append((time.monotonic() * 1000, event, data))

        @self.sio.event
        def disconnect(*_args):  # noqa: ANN001
            self.disconnected_at = time.monotonic() * 1000

        @self.sio.event
        def connect_error(data):  # noqa: ANN001
            self.connect_error = str(data)[:200]

    def connect(self, token: str | None) -> bool:
        try:
            self.sio.connect(SETTINGS.base_url, socketio_path="socket.io", transports=["websocket"],
                             auth={"token": token} if token else None, wait_timeout=10)
            return True
        except Exception as exc:  # noqa: BLE001
            self.connect_error = repr(exc)[:200]
            return False

    @property
    def connected(self) -> bool:
        return self.sio.connected

    def join(self, project_id: str) -> None:
        if self.sio.connected:
            self.sio.emit("join-project", project_id)

    def project_events(self, project_id: str, since: float = 0.0) -> list[tuple[float, str, object]]:
        out = []
        with self._lock:
            for t, ev, data in self.events:
                if t < since or ev not in ("project-op", "project-updated"):
                    continue
                if isinstance(data, dict) and str(data.get("projectId")) == str(project_id):
                    out.append((t, ev, data))
        return out

    def named(self, name: str, since: float = 0.0) -> list[tuple[float, str, object]]:
        with self._lock:
            return [e for e in self.events if e[1] == name and e[0] >= since]

    def close(self) -> None:
        try:
            self.sio.disconnect()
        except Exception:  # noqa: BLE001
            pass


def op_version(data: object) -> int | None:
    """Correlation key of a project-op event: the version it produced."""
    if not isinstance(data, dict):
        return None
    op = data.get("op")
    if isinstance(op, dict) and op.get("newVersion") is not None:
        try:
            return int(op["newVersion"])
        except (TypeError, ValueError):
            return None
    return None
