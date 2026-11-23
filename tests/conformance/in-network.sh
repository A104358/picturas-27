#!/usr/bin/env bash
# Run a conformance test from a container on the network of a Compose project.
#   tests/conformance/in-network.sh <compose-project> <script.py> [args...]
# The repository is mounted read-only at /repo (some tests read docs/); $PICTURAS_SECRETS_DIR is mounted read-only at
# the same path (the harness is trusted, see README). Direct service calls go to the
# Docker service names and container ports; the public entry is https://nginx.
set -euo pipefail
[ $# -ge 2 ] || { echo "usage: $0 <compose-project> <script.py> [args...]" >&2; exit 2; }
: "${PICTURAS_SECRETS_DIR:?PICTURAS_SECRETS_DIR is not set}"
project=$1; shift
case "$project" in picturas-nfr) echo "refusing the official MF stack" >&2; exit 2;; esac
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
image=picturas-conformance-runner
docker build -q -t "$image" -f "$here/runner.Dockerfile" "$here" >/dev/null
exec docker run --rm --network "${project}_elk" \
  -v "$root:/repo:ro" -w /repo/tests/conformance \
  -v "$PICTURAS_SECRETS_DIR:$PICTURAS_SECRETS_DIR:ro" \
  -e PICTURAS_SECRETS_DIR -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONUNBUFFERED=1 \
  -e B4_DIRECT=network -e B4_BASE_URL=https://nginx \
  "$image" python "$@"
