set -u
U=https://127.0.0.1:18443
C="curl -sk -o /dev/null -w %{http_code}"
echo "## version"; docker compose exec -T nginx nginx -v 2>&1
echo "## A1 auth ok, small body";  $C -X PUT -H 'Authorization: Bearer good' --data-binary 'hello' $U/uploads/x; echo
echo "## A2 auth bad -> 401";       $C -X PUT -H 'Authorization: Bearer bad'  --data-binary 'hello' $U/uploads/x; echo
echo "## A3 no auth -> 401";        $C -X PUT --data-binary 'hello' $U/uploads/x; echo
head -c 20971520 /dev/urandom > big.bin
echo "## A4 bad auth + 20 MiB at 2 MiB/s (should be refused fast; time and bytes sent)"
curl -sk -o /dev/null -w 'code=%{http_code} t=%{time_total} up=%{size_upload}\n' -X PUT -H 'Authorization: Bearer bad' -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/uploads/x
echo "## B1 streaming: good auth, 20 MiB at 2 MiB/s through /uploads/ (unbuffered)"
date +%s.%N | cut -c1-14 > t0; curl -sk -w '\ncode=%{http_code} t=%{time_total}\n' -X PUT -H 'Authorization: Bearer good' -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/uploads/x; cat t0
echo "## B2 control: same through /buffered/"
date +%s.%N | cut -c1-14 > t0; curl -sk -w '\ncode=%{http_code} t=%{time_total}\n' -X PUT -H 'Expect:' --limit-rate 2M --data-binary @big.bin $U/buffered/x; cat t0
echo "## B3 chunked client through /uploads/"
curl -sk -w '\ncode=%{http_code}\n' -X PUT -H 'Authorization: Bearer good' -H 'Transfer-Encoding: chunked' -H 'Expect:' --data-binary @big.bin $U/uploads/x
echo "## B4 over location limit (Content-Length 1200 MiB declared, bad auth vs good auth)"
python3 - <<'PY'
import socket, ssl
for auth in ("bad","good"):
    s = ssl._create_unverified_context().wrap_socket(socket.create_connection(("127.0.0.1",18443)))
    s.sendall(f"PUT /uploads/x HTTP/1.1\r\nHost: x\r\nAuthorization: Bearer {auth}\r\nContent-Length: {1200*1024*1024}\r\n\r\n".encode())
    s.settimeout(5); print(auth, s.recv(200).split(b"\r\n")[0]); s.close()
PY
echo "## C1 tls-ok";            curl -sk $U/tls-ok/x
echo "## C2 tls-wrongname";     $C $U/tls-wrongname/x; echo
echo "## C3 tls-untrusted";     $C $U/tls-untrusted/x; echo
echo "## C4 tls-noclientcert";  $C $U/tls-noclientcert/x; echo
echo "## C5 control verify off"; curl -sk $U/tls-verify-off/x
