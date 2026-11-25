U=https://127.0.0.1:18443
echo "## D1 mapped denials (403 + X-Deny-Status) with 20 MiB body at 2 MiB/s"
for c in 403 404 409 410 411 413 429 503; do printf "deny-$c -> "; curl -sk -w ' code=%{http_code} t=%{time_total} up=%{size_upload}\n' -X PUT -H "Authorization: Bearer deny-$c" -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/mapped/x; done
echo "## D2 auth slow (5 s > proxy_read_timeout 2 s)"
curl -sk -o /dev/null -w 'code=%{http_code} t=%{time_total}\n' -X PUT -H 'Authorization: Bearer slow' --data-binary hello $U/uploads/slow
echo "## D3 client_temp during unbuffered upload (sampled at 3 s and 6 s)"
curl -sk -o /dev/null -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/uploads/temp & sleep 3; docker compose exec -T nginx sh -c 'echo files=$(find /var/cache/nginx/client_temp -type f | wc -l) kib=$(du -sk /var/cache/nginx/client_temp | cut -f1)'; sleep 3; docker compose exec -T nginx sh -c 'echo files=$(find /var/cache/nginx/client_temp -type f | wc -l)'; wait
echo "## D3b client_temp during buffered control (sampled at 3 s)"
curl -sk -o /dev/null -X PUT -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/buffered/temp & sleep 3; docker compose exec -T nginx sh -c 'echo files=$(find /var/cache/nginx/client_temp -type f | wc -l) kib=$(du -sk /var/cache/nginx/client_temp | cut -f1)'; wait
echo "## D4 streaming to verified TLS upstream (mTLS)"
date +%s.%N | cut -c1-14; curl -sk -w 'code=%{http_code} t=%{time_total}\n' -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/uploads-tls/x
echo "## D5 auth service stopped"
docker compose stop auth >/dev/null 2>&1
curl -sk -o /dev/null -w 'code=%{http_code} t=%{time_total}\n' -X PUT -H 'Authorization: Bearer good' --data-binary hello $U/uploads/down
docker compose start auth >/dev/null 2>&1
