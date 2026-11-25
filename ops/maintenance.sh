#!/usr/bin/env bash
# Local installation maintenance. State/proofs are private and outside Git.
set -euo pipefail
: "${PICTURAS_SECRETS_DIR:?PICTURAS_SECRETS_DIR is required}"
exec python3 "$(dirname "$0")/maintenance.py" "$@"
