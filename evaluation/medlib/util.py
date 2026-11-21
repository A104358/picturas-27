"""Small helpers: time, hashing, redaction, results storage and logging."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import statistics
import sys
import threading
import time
from pathlib import Path
from typing import Any, Iterable

_LOCK = threading.Lock()


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def mono_ms() -> float:
    return time.monotonic_ns() / 1e6


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def tag(secret: str) -> str:
    """Short, non-reversible tag to correlate a secret without storing it."""
    return hashlib.sha256(secret.encode()).hexdigest()[:12] if secret else ""


_JWT_RE = re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]*\.?[A-Za-z0-9_\-]*")
_SIG_RE = re.compile(r"(X-Amz-[A-Za-z]+=)[^&\s\"']+", re.I)
_SECRET_WORDS = ("lisan_al_gaib", "admin123", "card_secret_key")


def redact(text: Any) -> str:
    """Remove JWTs, signed-URL parameters and known secret values from text."""
    s = text if isinstance(text, str) else json.dumps(text, default=str)
    s = _JWT_RE.sub("<jwt>", s)
    s = _SIG_RE.sub(r"\1<redacted>", s)
    for w in _SECRET_WORDS:
        s = s.replace(w, "<secret>")
    return s


def snippet(data: bytes | str | None, limit: int = 200) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        data = data[:limit * 2].decode("utf-8", "replace")
    return redact(data[:limit])


def log(msg: str) -> None:
    with _LOCK:
        print(f"[{time.strftime('%H:%M:%S')}] {redact(msg)}", file=sys.stderr, flush=True)


def median(values: Iterable[float]) -> float | None:
    v = [x for x in values if x is not None]
    return statistics.median(v) if v else None


def maximum(values: Iterable[float]) -> float | None:
    v = [x for x in values if x is not None]
    return max(v) if v else None


class Results:
    """Campaign directory: raw/<metric>.jsonl, summary.json, manifest.json."""

    def __init__(self, path: Path):
        self.path = path
        (path / "raw").mkdir(parents=True, exist_ok=True)
        self.summaries: dict[str, dict] = {}
        summary_file = path / "summary.json"
        if summary_file.exists():
            self.summaries = json.loads(summary_file.read_text()).get("metrics", {})

    def raw(self, metric: str, record: dict) -> None:
        line = redact(json.dumps(record, default=str, ensure_ascii=False))
        with _LOCK, open(self.path / "raw" / f"{metric}.jsonl", "a") as f:
            f.write(line + "\n")

    def summary(self, metric: str, value: dict) -> None:
        self.summaries[metric] = json.loads(redact(json.dumps(value, default=str)))
        self._write_summary()

    def _write_summary(self) -> None:
        data = {"updated_at": utc_now(), "metrics": self.summaries}
        (self.path / "summary.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))

    def write_json(self, name: str, data: Any) -> None:
        (self.path / name).write_text(redact(json.dumps(data, indent=1, default=str, ensure_ascii=False)))
