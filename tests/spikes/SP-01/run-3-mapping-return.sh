U=https://127.0.0.1:18443
for loc in mapped mapped-return; do echo "## D1' $loc"; for c in 403 409 411 503; do printf "deny-$c -> "; curl -sk -w ' code=%{http_code} t=%{time_total} up=%{size_upload}\n' -X PUT -H "Authorization: Bearer deny-$c" -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/$loc/x; done; done
spool(){ docker compose exec -T nginx sh -c 'n=0; for f in /proc/[0-9]*/fd/*; do l=$(readlink $f 2>/dev/null); case "$l" in *client_temp*) n=$((n+1)); echo "  $l size=$(stat -L -c %s $f)";; esac; done; echo "  spool_fds=$n"'; }
echo "## D3' unbuffered /uploads/ at 3 s"; curl -sk -o /dev/null -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/uploads/temp & sleep 3; spool; wait
echo "## D3' buffered control at 3 s"; curl -sk -o /dev/null -X PUT -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/buffered/temp & sleep 3; spool; wait
