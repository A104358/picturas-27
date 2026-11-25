#!/usr/bin/env bash
# Restricted B11 workflow; never commits, pushes, prunes or removes volumes.
set -euo pipefail
export PICTURAS_SECRETS_DIR=$HOME/picturas-secrets
cd "$(dirname "$0")/../../.."
case "${1:-status}" in
  fixture-export)
    exec python3 tests/conformance/operations/export-evidence.py ;;
  final-metrics)
    exec python3 tests/conformance/operations/finalize-evidence.py ;;
  audit-files)
    exec python3 tests/conformance/operations/audit-files.py ;;
  sync)
    exec python3 tests/conformance/operations/sync-branch.py ;;
  sync-resume)
    exec python3 tests/conformance/operations/sync-branch.py --resume ;;
  fixture-up|fixture-prepare|fixture-diagnostics|fixture-case-diagnostics|fixture-reset-image-observer|fixture-interrupt|fixture-cut-after-reply|fixture-exercise|fixture-exercise-finish|fixture-exercise-quarantine|fixture-video-interrupt|fixture-video-finish|fixture-late|fixture-unknown|fixture-down)
    exec python3 tests/conformance/operations/b11-fixture.py "${1#fixture-}" ;;
  baseline-reuse|baseline-dev|baseline-exp|dev-tests|dev-tail|units|guard|audit|native-quota|exp-up|exp-run|dev-up|dev-down|exp-down|status)
    exec python3 tests/conformance/operations/b11-workflow.py "${1:-status}" ;;
  *) echo 'unsupported B11 workflow action' >&2; exit 2;;
esac
