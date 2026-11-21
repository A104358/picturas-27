"""Entry point executed inside the probe container: one JSON action on stdin,
one JSON result on the last line of stdout."""
from __future__ import annotations

import json
import sys

from .actions import dumps, run_action


def main() -> None:
    spec = json.loads(sys.stdin.read())
    try:
        result = run_action(spec)
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error_kind": "other", "error": repr(exc)[:300]}
    sys.stdout.write(dumps(result) + "\n")


if __name__ == "__main__":
    main()
