#!/usr/bin/env bash
# B12: full conformance suite (plan §5, B0-B11) against the development stack, one raw file
# per suite in tests/conformance/results/<date>/B12-conf-<label>.txt plus an index.
# Usage: tests/conformance/run-b12.sh [suite-label ...]   (default: every suite)
# Needs picturas-dev up and built; never commits, prunes or removes volumes. The secrets
# directory path is redacted from the saved output.
set -uo pipefail
: "${PICTURAS_SECRETS_DIR:?PICTURAS_SECRETS_DIR is not set}"
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"
P=picturas-dev
OUT="$ROOT/tests/conformance/results/$(date +%F)"
mkdir -p "$OUT"
INDEX="$OUT/B12-conf-index.txt"
PY=${B12_PYTHON:-$ROOT/evaluation/.venv/bin/python}
BROWSER_PY=${B12_BROWSER_PYTHON:-$HOME/picturas-b7-diagnostico/.venv/bin/python}
NET="tests/conformance/in-network.sh $P"
IMG="docker run --rm --network none -v $ROOT:/repo:ro -w /repo"

declare -a SUITES=(
  "B1-pki-check|ops/pki.sh check"
  "B1-secrets-check|ops/secrets.sh check"
  "B1-S19-markers|tests/conformance/mtls-pki/s19-markers.sh"
  "B1-S19-git-grep|tests/conformance/mtls-pki/s19-git-grep.sh"
  "B1-smoke|python3 tests/conformance/mtls-pki/b1-smoke.py"
  "B2-F02-functional|$PY tests/conformance/data-channels/b2-functional.py"
  "B3-quota|$NET users-quota.py"
  "B3-F08-restart|$PY tests/conformance/diagnostics/f08-restart.py $P"
  "B4-route-matrix|$PY tests/conformance/b4-route-matrix.py"
  "B4-identity|$NET b4-identity.py"
  "B4-routes|$NET b4-routes.py"
  "B4-functional|$NET b4-functional.py"
  "B5-mtls|$NET mtls-pki/b5-mtls.py"
  "B5-functional|$NET mtls-pki/b5-functional.py"
  "B5-guard|tests/conformance/mtls-pki/b5-guard.sh $P"
  "B6-adapter|$NET upload/b6-adapter.py"
  "B6-races|$PY tests/conformance/upload/b6-races.py"
  "B6-capacity|$PY tests/conformance/upload/b6-capacity.py"
  "B7-flow|$PY tests/conformance/upload/b7-flow.py"
  "B7-signature|$NET upload/b7-signature.py"
  "B7-lifecycle|$PY tests/conformance/upload/b7-lifecycle.py"
  "B7-late-cleanup|$PY tests/conformance/upload/b7-late-cleanup.py"
  "B7-UL10-probe-limits|$PY tests/conformance/upload/ul10-probe-limits.py"
  "B7-browser|$BROWSER_PY tests/conformance/upload/b7-browser.py"
  "B8-unit|$IMG -e NODE_PATH=/usr/src/app/node_modules --entrypoint node $P-ws_gateway --test tests/conformance/websocket/authorization.test.js tests/conformance/websocket/protocol.test.js tests/conformance/websocket/ws-route.test.js tests/conformance/websocket/presence-agent.test.js tests/conformance/websocket/client-reconnect.test.js"
  "B8-functional|$NET websocket/b8-functional.py"
  "B8-wire-limits|$NET websocket/b8-wire-limits.py 10"
  "B8-load|$NET websocket/b8-load.py"
  "B9-issuer|$IMG -e NODE_PATH=/app/node_modules --entrypoint node $P-users --test tests/conformance/sessions/issuer.test.js"
  "B9-session-profile|docker run --rm --network none -v $ROOT/tests/conformance/sessions:/t:ro --entrypoint node $P-users /t/session-profile.test.js"
  "B9-client|$IMG -e B9_TS_COMPILER=/usr/src/app/node_modules/typescript --entrypoint node $P-frontend tests/conformance/sessions/client.test.js"
  "B9-mutations|$IMG -e B9_TS_COMPILER=/usr/src/app/node_modules/typescript --entrypoint node $P-frontend tests/conformance/sessions/mutations.test.js"
  "B9-functional|$NET sessions/b9-functional.py"
  "B9-browser|$BROWSER_PY tests/conformance/sessions/b9-browser.py"
  "B10-maintenance-unit|$IMG -e PYTHONDONTWRITEBYTECODE=1 --entrypoint python picturas-conformance-runner -m unittest discover -s tests/conformance/pki-operations -p test_maintenance.py"
  "B10-work-callback|$IMG --entrypoint node $P-projects --test tests/conformance/pki-operations/work-callback.test.js"
  "B11-units|$IMG -e PYTHONDONTWRITEBYTECODE=1 --entrypoint python picturas-conformance-runner -m unittest discover -s tests/conformance/operations -p test_*.py"
  "B11-quota-ledger|docker run --rm --network none -v $ROOT/users/tests:/app/tests:ro -v $ROOT/users/admin:/app/admin:ro --entrypoint node $P-users --test tests/quota-ledger.test.js"
  "B11-functional|$NET operations/b11-functional.py"
  "F01|tests/conformance/run-f01.sh $P"
  "B12-regression|$NET regression/b12-regression.py"
  "B12-browser-export|$BROWSER_PY tests/conformance/regression/b12-browser-export.py"
)

want=" $* "
{ echo "# B12 conformance — $(date -u +%FT%TZ) — commit $(git rev-parse --short HEAD)$(git diff --quiet || echo ' (+ uncommitted changes)')"; } >> "$INDEX"
for entry in "${SUITES[@]}"; do
  label=${entry%%|*}; cmd=${entry#*|}
  if [ $# -gt 0 ] && [[ "$want" != *" $label "* ]]; then continue; fi
  file="$OUT/B12-conf-$label.txt"
  start=$(date +%s)
  { echo "# $label — $(date -u +%FT%TZ)"; echo "\$ ${cmd//$ROOT\//}"; echo
    bash -c "$cmd" 2>&1; echo "exit: $?"; } | sed "s#$PICTURAS_SECRETS_DIR#<secrets-dir>#g" > "$file"
  code=$(tail -1 "$file" | sed 's/exit: //')
  printf '%-24s exit=%s %4ss %s\n' "$label" "$code" "$(( $(date +%s) - start ))" \
    "$(grep -E 'checks passed|passed|PASS|FAIL|^ok |^not ok|# (pass|fail)' "$file" | tail -1 | cut -c1-90)" | tee -a "$INDEX"
done
