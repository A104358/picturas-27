U=https://127.0.0.1:18443
spool(){ docker compose exec -T -u nginx nginx sh -c 'n=0; for f in /proc/[0-9]*/fd/*; do l=$(readlink $f 2>/dev/null); case "$l" in *client_temp*) n=$((n+1)); echo "  $l size=$(stat -L -c %s $f)";; esac; done; echo "  spool_fds=$n"'; }
echo "## D3' unbuffered /uploads/ at 3 s"; curl -sk -o /dev/null -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/uploads/temp & sleep 3; spool; wait
echo "## D3' buffered control at 3 s"; curl -sk -o /dev/null -X PUT -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/buffered/temp & sleep 3; spool; wait
echo "## D3' chunked unbuffered at 3 s"; curl -sk -o /dev/null -X PUT -H 'Authorization: Bearer good' -H 'Transfer-Encoding: chunked' -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/uploads/temp & sleep 3; spool; wait
