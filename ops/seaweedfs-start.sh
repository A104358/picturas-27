#!/bin/sh
# Keep the SeaweedFS master on loopback while preparing volumes for large uploads.
set -eu

rm -f /data/.picturas-volumes-ready

weed "$@" &
server=$!
trap 'kill -TERM "$server" 2>/dev/null || true; wait "$server" 2>/dev/null || true' TERM INT

attempt=0
while [ "$attempt" -lt 45 ]; do
  attempt=$((attempt + 1))
  if topology=$(printf 'volume.list\nexit\n' | weed shell -master=localhost:9333 2>/dev/null); then
    count=$(printf '%s\n' "$topology" | grep -c 'Collection:picturas,' || true)
    if [ "$count" -ge 3 ]; then
      touch /data/.picturas-volumes-ready
      wait "$server"
      exit $?
    fi
    needed=$((3 - count))
    # The master API (loopback only, mTLS with this service's certificate) also creates the
    # collection on a fresh install; `weed shell volume.grow` refuses an unknown collection,
    # and the bucket that would create it is made only after this service is healthy.
    if curl -fsS --cacert /run/secrets/pki/ca.crt --cert /run/secrets/pki/service.crt \
        --key /run/secrets/pki/service.key \
        "https://localhost:9333/vol/grow?collection=picturas&count=$needed" >/dev/null 2>&1; then
      sleep 1
      continue
    fi
  fi
  sleep 2
done
echo 'SeaweedFS volume preparation failed' >&2
kill -TERM "$server" 2>/dev/null || true
wait "$server" 2>/dev/null || true
exit 1
