echo "## 1 listening TCP ports in the seaweedfs container"
docker compose exec -T seaweedfs sh -c 'cat /proc/net/tcp /proc/net/tcp6 2>/dev/null | awk "\$4==\"0A\"{print \$2}"' | sort -u | while read a; do ip=${a%%:*}; printf '  %-6d %s\n' 0x${a##*:} "$( [ "$ip" = 0100007F ] && echo loopback || ([ "$ip" = 0B00007F ] && echo 'docker dns' || echo all-interfaces))"; done | sort -n | uniq
echo "## 2 S3 still works end-to-end (put/get/copy/presigned) with gRPC mTLS"
docker compose exec -T t python /w/matrix.py 2>&1 | grep -E 'img_storage (put|get|copy)|presigned|git_default list_buckets'
echo "## 3 probe each port from another container"
docker compose exec -T t sh -c '
for p in 9333 19333 8080 18080 8888 18888 9000 19000; do
  plain=$(curl -s -m 3 -o /dev/null -w "%{http_code}" http://seaweedfs:$p/ 2>/dev/null); [ -z "$plain" ] && plain=fail
  nocert=$(echo | timeout 4 openssl s_client -connect seaweedfs:$p -servername seaweedfs -CAfile /pki/ca.crt -verify_return_error 2>&1 </dev/null | grep -qE "alert certificate required|alert handshake failure|peer did not return a certificate" && echo client-cert-required || (echo | timeout 4 openssl s_client -connect seaweedfs:$p -CAfile /pki/ca.crt 2>&1 | grep -q "Verify return code: 0" && echo tls-ok-no-cert || echo no-tls))
  h=$(curl -s -m 3 -o /dev/null -w "%{http_code}" --cacert /pki/ca.crt --cert /pki/img_storage.crt --key /pki/img_storage.key https://seaweedfs:$p/ 2>/dev/null); [ -z "$h" ] && h=fail
  printf "  port %-6s plain-http=%-5s tls-without-client-cert=%-22s https-with-img_storage-cert=%s\n" $p "$plain" "$nocert" "$h"
done'
echo "## 4 gRPC as a client: weed shell from another container (master gRPC 19333)"
for who in seaweedfs img_storage none; do
  if [ $who = none ]; then printf '[grpc]\nca = "/pki/ca.crt"\n' > client-$who.toml; else printf '[grpc]\nca = "/pki/ca.crt"\n[grpc.client]\ncert = "/pki/%s.crt"\nkey = "/pki/%s.key"\n' $who $who > client-$who.toml; fi
  printf "  client cert %-12s -> " $who
  docker run --rm --network picturas-spike_default -v $PWD/pki:/pki:ro -v $PWD/client-$who.toml:/etc/seaweedfs/security.toml:ro chrislusf/seaweedfs@sha256:ce9e796f1fe6f06968f4c04bdaf8f678dad9c8acdfef3d244133d71bfa6bf882 shell -master=seaweedfs:9333 <<< 'cluster.ps' 2>&1 | grep -E 'master|filer|volume|error|denied|refused|certificate|Unavailable|PermissionDenied' | head -2 | tr '\n' ' ' | cut -c1-200; echo
done
