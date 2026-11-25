#!/bin/sh
# Runs inside the test container: one gRPC call to seaweedfs:19000 per client identity.
URL=https://seaweedfs:19000/grpc.reflection.v1alpha.ServerReflection/ServerReflectionInfo
for who in none img_storage seaweedfs; do
  if [ "$who" = none ]; then opts=""; else opts="--cert /pki/$who.crt --key /pki/$who.key"; fi
  printf '  %-11s -> ' "$who"
  out=$(curl -s -m 4 --http2 --cacert /pki/ca.crt $opts -X POST \
    -H 'content-type: application/grpc' -H 'te: trailers' --data-binary '' \
    -o /dev/null -D - "$URL" 2>&1)
  rc=$?
  echo "$out" | grep -iE '^HTTP|grpc-status|grpc-message' | tr -d '\r' | tr '\n' ' '
  echo "curl_rc=$rc"
done
