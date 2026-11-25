#!/usr/bin/env bash
# B10 test workflow only. No arbitrary commands, commits, pushes or volume deletion.
set -euo pipefail
export PICTURAS_SECRETS_DIR=$HOME/picturas-secrets
repo=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$repo"
action=${1:-status}
trial=${2:-}
case "$action" in
  prepare-cycle)
    case "$trial" in 1|2|3) ;; *) exit 2;; esac
    evaluation/.venv/bin/python tests/conformance/pki-operations/pilot.py begin "$trial"
    evaluation/.venv/bin/python tests/conformance/pki-operations/pilot.py replace "$trial"
    export PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/picturas-pki-b10/browsers
    python3 tests/conformance/pki-operations/close_browser.py "$trial" --prepare
    exec "$HOME/.cache/picturas-pki-b10/.venv/bin/python" tests/conformance/pki-operations/manual_browser.py "$trial"
    ;;
  complete-cycle)
    case "$trial" in 1|2|3) ;; *) exit 2;; esac
    # This action is invoked only after the agent has viewed all four native pages.
    python3 tests/conformance/pki-operations/record_browser_review.py "$trial"
    exec evaluation/.venv/bin/python tests/conformance/pki-operations/pilot.py resume "$trial"
    ;;
  status)
    exec python3 tests/conformance/pki-operations/workflow_status.py
    ;;
  begin|replace|resume|archive-preparation|archive-diagnostic|archive-initial)
    case "$trial" in 1|2|3) ;; *) echo 'trial must be 1, 2 or 3' >&2; exit 2;; esac
    exec evaluation/.venv/bin/python tests/conformance/pki-operations/pilot.py "$action" "$trial"
    ;;
  renew)
    exec evaluation/.venv/bin/python tests/conformance/pki-operations/planned_renew.py
    ;;
  browser)
    case "$trial" in 1|2|3) ;; *) echo 'trial must be 1, 2 or 3' >&2; exit 2;; esac
    export PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/picturas-pki-b10/browsers
    python3 tests/conformance/pki-operations/close_browser.py "$trial" --prepare
    exec "$HOME/.cache/picturas-pki-b10/.venv/bin/python" tests/conformance/pki-operations/manual_browser.py "$trial"
    ;;
  close-browser)
    case "$trial" in 1|2|3) ;; *) exit 2;; esac
    exec python3 tests/conformance/pki-operations/close_browser.py "$trial"
    ;;
  record-visual-review)
    case "$trial" in 1|2|3) ;; *) exit 2;; esac
    exec python3 tests/conformance/pki-operations/record_browser_review.py "$trial"
    ;;
  export)
    exec python3 tests/conformance/pki-operations/export_evidence.py
    ;;
  inventory)
    export PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/picturas-pki-b10/browsers
    exec python3 tests/conformance/pki-operations/inventory.py
    ;;
  negative)
    exec python3 tests/conformance/pki-operations/negative.py
    ;;
  channels)
    exec python3 tests/conformance/pki-operations/channels.py
    ;;
  browser-live)
    export PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/picturas-pki-b10/browsers
    exec "$HOME/.cache/picturas-pki-b10/.venv/bin/python" tests/conformance/pki-operations/browser_live.py
    ;;
  gate-check)
    exec python3 tests/conformance/pki-operations/gate_live.py
    ;;
  pilot-up|pilot-down|dev-up|dev-tests|dev-independent-tests|dev-down|exp-up|exp-run|exp-down)
    exec python3 tests/conformance/pki-operations/stack_workflow.py "$action"
    ;;
  *) echo 'unsupported B10 workflow action' >&2; exit 2;;
esac
