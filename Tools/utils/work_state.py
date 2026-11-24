"""Observe local work for planned maintenance; no ack/retry semantics change."""
from contextlib import contextmanager
import json
import os
from pathlib import Path

MARKER = Path(f"/tmp/picturas-work-{os.getpid()}.json")
MARKER.unlink(missing_ok=True)

@contextmanager
def active_work():
    temporary = MARKER.with_suffix('.tmp')
    temporary.write_text(json.dumps({'pid': os.getpid(), 'active_count': 1}))
    temporary.chmod(0o600)
    temporary.replace(MARKER)
    try:
        yield
    finally:
        MARKER.unlink(missing_ok=True)
