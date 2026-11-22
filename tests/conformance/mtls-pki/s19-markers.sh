#!/usr/bin/env bash
# S19 with synthetic markers (plan B1, item 5): a secret placed where secrets usually end up must be
#   (a) ignored by Git, (b) absent from every build context, (c) absent from every built image.
# Usage: tests/conformance/mtls-pki/s19-markers.sh [compose-project]
#   Without a project only (a) and (b) run. With one, the markers stay in place while
#   `docker compose -p <project> build` runs, and every image built from this repository is scanned.
#   PICTURAS_SECRETS_DIR must be set when a project is given (docker compose needs it).
set -uo pipefail

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
PROJECT=${1:-}
TOKEN="S19-MARKER-$(openssl rand -hex 8)"
CONTEXTS=". apiGateway users subscriptions projects imageStorageService wsGateway frontend Tools generative-mock rabbitMQ"
PROBE_IMAGE=busybox:1.36.1
fail=0
created=()

cleanup() { local f; for f in "${created[@]}"; do rm -f "$f"; done; for d in $(printf '%s\n' "${created[@]}" | xargs -n1 dirname | sort -ru); do rmdir "$d" 2>/dev/null; done; }
trap cleanup EXIT

place() { mkdir -p "$(dirname "$1")"; echo "$TOKEN" > "$1"; created+=("$1"); }

for c in $CONTEXTS; do
  d="$ROOT/$c"
  place "$d/certs/s19-$TOKEN.key"
  place "$d/s19-$TOKEN.pem"
  place "$d/.env.s19-$TOKEN"
  place "$d/secrets/s19-$TOKEN.txt"
done
echo "# S19 markers ($TOKEN): ${#created[@]} files in $(echo $CONTEXTS | wc -w | tr -d ' ') locations"

echo "## (a) Git ignores every marker"
for f in "${created[@]}"; do
  rel=${f#"$ROOT"/}
  if ! git -C "$ROOT" check-ignore -q "$rel"; then echo "FAIL not ignored: $rel"; fail=1; fi
done
if git -C "$ROOT" status --porcelain --untracked-files=all | grep -q "$TOKEN"; then echo "FAIL a marker shows up in git status"; fail=1; fi
[ $fail -eq 0 ] && echo "ok   all ${#created[@]} markers ignored"

echo "## (b) markers are absent from each build context (.dockerignore)"
docker image inspect "$PROBE_IMAGE" >/dev/null 2>&1 || docker pull -q "$PROBE_IMAGE" >/dev/null
for c in $CONTEXTS; do
  [ "$c" = . ] && continue   # the repository root is not a build context
  out=$(printf 'FROM %s\nRUN --mount=type=bind,target=/ctx sh -c "if grep -rl %s /ctx; then exit 1; fi"\n' "$PROBE_IMAGE" "$TOKEN" \
    | DOCKER_BUILDKIT=1 docker build --no-cache -q -f - "$ROOT/$c" 2>&1)
  if [ $? -eq 0 ]; then echo "ok   $c"; else echo "FAIL $c: marker inside the build context"; echo "$out" | grep -i "$TOKEN" | head -3; fail=1; fi
done

if [ -n "$PROJECT" ]; then
  echo "## (c) markers are absent from the images built by '$PROJECT'"
  docker compose -f "$ROOT/docker-compose.yaml" -p "$PROJECT" build >/tmp/s19-build-$$.log 2>&1 \
    || { echo "FAIL build failed (log: /tmp/s19-build-$$.log)"; exit 1; }
  for img in $(docker image ls --format '{{.Repository}}' | grep "^$PROJECT-" | sort -u); do
    hits=$(docker run --rm --entrypoint sh "$img" -c "find / -xdev \( -name '*$TOKEN*' -o -path '*/certs/*' -o -name '*.key' -o -name '.env' \) -not -path '/proc/*' -not -path '*/node_modules/*' -not -path '/usr/*' -not -path '/etc/ssl/*' 2>/dev/null" 2>&1)
    if echo "$hits" | grep -q "$TOKEN"; then echo "FAIL $img contains a marker"; echo "$hits" | grep "$TOKEN" | head -3; fail=1
    elif [ -n "$hits" ]; then echo "WARN $img: other key-like paths: $(echo "$hits" | tr '\n' ' ' | cut -c1-160)"
    else echo "ok   $img"; fi
  done
fi

[ $fail -eq 0 ] && echo "S19 markers: passed" || { echo "S19 markers: FAILED"; exit 1; }
