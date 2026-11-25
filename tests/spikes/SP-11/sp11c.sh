#!/usr/bin/env bash
# SP-11, loopback mode: listening ports, S3 end-to-end, and the S3 gRPC port with different client certificates.
echo "## 1 listening TCP ports in the seaweedfs container (loopback mode)"
docker compose exec -T seaweedfs sh -c 'cat /proc/net/tcp /proc/net/tcp6 2>/dev/null' \
  | awk '$4=="0A"{print $2}' | sort -u | while read -r a; do
    ip=${a%%:*}; port=$((16#${a##*:}))
    case $ip in 0100007F) where=loopback ;; 0B00007F) where="docker dns" ;; *) where=all-interfaces ;; esac
    printf '  %-6d %s\n' "$port" "$where"
  done | sort -n | uniq

echo "## 2 S3 end-to-end in loopback mode"
docker compose exec -T t python /w/matrix.py 2>&1 \
  | grep -E 'img_storage (put|get|copy|create_bucket)|presigned|git_default list_buckets|uploader put'

echo "## 3 S3 gRPC port 19000 with client certificates (HTTP/2 gRPC request)"
docker compose exec -T t sh /w/grpcprobe.sh
