U=https://127.0.0.1:18443
echo "## 1 page / through nginx (verified TLS + client cert)"; curl -sk -o page.html -w '  %{http_code} %{size_download} bytes %{time_total}s\n' $U/
A=$(grep -o '/_next/static/[^"]*\.js' page.html | head -1); echo "## 2 static asset $A"; curl -sk -o /dev/null -w '  %{http_code} %{size_download} bytes\n' "$U$A"
echo "## 3 other route /login"; curl -sk -o /dev/null -w '  %{http_code}\n' $U/login
echo "## 4 nginx without client cert"; curl -sk -o /dev/null -w '  %{http_code}\n' $U/no-client-cert/
echo "## 5 nginx expects another name (api_gateway)"; curl -sk -o /dev/null -w '  %{http_code}\n' $U/wrong-name/
echo "## 6 direct from another container"
docker compose exec -T t sh -c '
printf "  plain http: "; curl -s -m 5 -o /dev/null -w "%{http_code}\n" http://frontend:3000/ || echo "fail rc=$?";
printf "  https, no client cert: "; curl -s -m 5 --cacert /pki/ca.crt -o /dev/null -w "%{http_code}\n" https://frontend:3000/ || echo "fail rc=$?";
printf "  https, client cert from other CA (CN=nginx): "; curl -s -m 5 --cacert /pki/ca.crt --cert /pki/rogue-client.crt --key /pki/rogue-client.key -o /dev/null -w "%{http_code}\n" https://frontend:3000/ || echo "fail rc=$?";
printf "  https, valid client cert but CN=frontend (not an allowed peer): "; curl -s -m 5 --cacert /pki/ca.crt --cert /pki/frontend.crt --key /pki/frontend.key -o /dev/null -w "%{http_code}\n" https://frontend:3000/ || echo "fail rc=$?"'
echo "## 7 latency: 20 x GET / through nginx"; for i in $(seq 1 20); do curl -sk -o /dev/null -w '%{time_total}\n' $U/; done | sort -n | awk '{a[NR]=$1} END{print "  median", a[int(NR/2)+1]"s", "max", a[NR]"s"}'
