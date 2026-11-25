#!/usr/bin/env bash
# F01: existing regression suites (projects node:test and Tools/video pytest), run inside the
# product images so the toolchain matches what ships (the video tests need ffmpeg with libass).
# Usage: tests/conformance/run-f01.sh [compose-project]   (default: picturas-dev)
# The images <project>-projects and <project>-video_tool must exist (docker compose -p <project> build).
set -uo pipefail

PROJECT=${1:-picturas-dev}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT_DIR="$ROOT/tests/conformance/results/$(date +%F)"
OUT="$OUT_DIR/F01-$(date +%H%M%S).txt"
mkdir -p "$OUT_DIR"

{
  echo "# F01 regression — $(date -u +%FT%TZ)"
  echo "commit: $(git -C "$ROOT" rev-parse --short HEAD)$(git -C "$ROOT" diff --quiet || echo ' (+ uncommitted changes)')"
  echo "images: $PROJECT-projects $PROJECT-video_tool"
  echo
  echo "## projects (node --test)"
  docker run --rm -v "$ROOT/projects/tests:/app/tests:ro" -v "$ROOT/projects/utils:/app/utils:ro" \
    --entrypoint bash "$PROJECT-projects" -o pipefail -c 'node -v && node --test tests/ 2>&1 | tail -9'
  echo "exit: $?"
  echo
  echo "## Tools/video (pytest)"
  docker run --rm -v "$ROOT/Tools/video:/src:ro" --entrypoint bash "$PROJECT-video_tool" -o pipefail -c \
    'cp -r /src /tmp/video && cd /tmp/video && rm -rf .venv && pip install -q "pytest>=8" >/dev/null 2>&1 &&
     python -m pytest -q -p no:cacheprovider tests 2>&1 | tail -3'
  echo "exit: $?"
} 2>&1 | tee "$OUT"
echo "saved: $OUT"
