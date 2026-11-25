"""Host driver for `b8-functional.py outage`: stops and starts only `projects` when the test asks.

usage: b8-outage.py [compose-project]   (default picturas-dev; never picturas-nfr)
Prints the in-network test's output unchanged and exits with its status.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
project = sys.argv[1] if len(sys.argv) > 1 else "picturas-dev"
assert project != "picturas-nfr", "never against the measurement stack"
compose = ["docker", "compose", "-p", project]
test = subprocess.Popen([str(ROOT / "tests/conformance/in-network.sh"), project, "websocket/b8-functional.py", "outage"],
                        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
for line in test.stdout:
    print(line, end="", flush=True)
    if line.strip() == "READY_STOP_PROJECTS":
        subprocess.run(compose + ["stop", "projects"], cwd=ROOT, check=True, capture_output=True)
    elif line.strip() == "READY_START_PROJECTS":
        subprocess.run(compose + ["start", "projects"], cwd=ROOT, check=True, capture_output=True)
sys.exit(test.wait())
