#!/usr/bin/env bash
# Local administrator only. The case directory is outside Git and private.
set -euo pipefail
: "${PICTURAS_SECRETS_DIR:?PICTURAS_SECRETS_DIR is required}"
[ "$#" -ge 5 ] && [ "$#" -le 6 ] || { echo 'usage: session-recovery.sh <project> inspect|issue|status <case.json> <installation-ref> <dataset-ref> [output.json]' >&2; exit 2; }
project=$1; command=$2; case_file=$3; installation=$4; dataset=$5; output=${6:-}
case "$project" in picturas-nfr) echo 'refusing the official MF stack' >&2; exit 2;; esac
case "$command" in inspect|issue|status) ;; *) echo 'invalid command' >&2; exit 2;; esac
root=$(cd "$(dirname "$0")/.." && pwd)
# Check ownership, symlinks, and the repository boundary before mounting anything.
python3 - "$case_file" "$root" <<'PY'
import os, pathlib, stat, sys
p=pathlib.Path(os.path.abspath(sys.argv[1])); root=pathlib.Path(sys.argv[2])
if p.resolve() != p or p.is_relative_to(root): raise SystemExit('case must be outside the repository without symlinks')
for target in (p, p.parent):
 s=target.lstat()
 if s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) & 0o077 or target.is_symlink(): raise SystemExit('private owner-only case/directory required')
if not p.is_file(): raise SystemExit('regular case file required')
PY
case_dir=$(cd "$(dirname "$case_file")" && pwd)
case_name=$(basename "$case_file")
image=$(docker compose -p "$project" -f "$root/docker-compose.yaml" images -q users)
[ -n "$image" ] || { echo 'users image is unavailable for this project' >&2; exit 2; }
exec docker run --rm --network "${project}_elk" --user "$(id -u):$(id -g)" \
  --read-only --cap-drop ALL --security-opt no-new-privileges \
  --env-file "$PICTURAS_SECRETS_DIR/env/users.env" \
  -v "$case_dir:/recovery:rw" \
  -v "$PICTURAS_SECRETS_DIR/pki/services/users:/run/secrets/pki:ro" \
  "$image" node admin/sessionRecovery.js "$command" "/recovery/$case_name" "$installation" "$dataset" "$output"
