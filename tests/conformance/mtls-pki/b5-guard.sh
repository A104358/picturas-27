#!/usr/bin/env bash
# B5 conformance, run on the host (uses docker):
#  1. Runtime validity guard (B5 item 4, PKI-C3 A): with a throwaway CA and certificate made
#     inside a disposable container from the product image, the Node guard (tls/pkiTls.js)
#     and the Python guard (generative-mock/server_tls.py) refuse to start with an expired or
#     not-yet-valid certificate, keep running with a valid one and stop when it expires.
#  2. Server identity checked by the clients (B5 item 2): the Node client agent of projects
#     and the requests client of expand_ai refuse a server whose certificate does not carry
#     the expected name, and accept the right one.
# Usage: tests/conformance/mtls-pki/b5-guard.sh [compose-project]   (default picturas-dev)
set -uo pipefail
P=${1:-picturas-dev}
[ "$P" != picturas-nfr ] || { echo "refusing the official MF stack" >&2; exit 2; }
pass=0; fail=0
check() { # label expected got
  if [ "$2" = "$3" ]; then pass=$((pass+1)); echo "PASS $1: $3"; else fail=$((fail+1)); echo "FAIL $1: $3 (expected $2)"; fi
}

# Makes /tmp/pki/{ca.crt,service.crt,service.key} valid from $1 to $2 seconds relative to now.
MKCERT='set -e; mkdir -p /tmp/pki && cd /tmp/pki
ts() { date -u -d "@$(( $(date +%s) + $1 ))" +%Y%m%d%H%M%SZ; }
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout ca.key -out ca.crt -subj /CN=guard-test-ca -days 2 2>/dev/null
openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout service.key -out s.csr -subj /CN=guard-test 2>/dev/null
openssl x509 -req -in s.csr -CA ca.crt -CAkey ca.key -out service.crt -not_before "$(ts $NB)" -not_after "$(ts $NA)" 2>/dev/null
rm -f ca.key s.csr'

run_guard() { # image interpreter code NB NA wait -> "exit=<code> after=<s>"
  docker run --rm -e NB="$4" -e NA="$5" -e PKI_DIR=/tmp/pki -e CODE="$3" --entrypoint sh "$1" -c "$MKCERT
set +e; cd /app; start=\$(date +%s); timeout $6 $2 \"\$CODE\" >/dev/null 2>&1; code=\$?; echo \"exit=\$code after=\$(( \$(date +%s) - start ))\""
}
NODE_GUARD="require('/app/tls/pkiTls').guardValidity(); setInterval(() => {}, 1000);"
PY_GUARD="import server_tls, time; server_tls.guard_validity(); time.sleep(60)"

for kind in node python; do
  if [ $kind = node ]; then img=$P-api_gateway; it="node -e"; code=$NODE_GUARD
  else img=$P-generative-mock; it="python -c"; code=$PY_GUARD; fi
  r=$(run_guard "$img" "$it" "$code" -3600 -60 20); check "$kind guard: expired at start-up" "exit=1" "${r%% *}"
  r=$(run_guard "$img" "$it" "$code" 3600 7200 20); check "$kind guard: not yet valid" "exit=1" "${r%% *}"
  r=$(run_guard "$img" "$it" "$code" -60 3600 8); check "$kind guard: valid certificate keeps running (timeout)" "exit=124" "${r%% *}"
  r=$(run_guard "$img" "$it" "$code" -60 12 40); code=${r%% *}; after=${r##*=}
  check "$kind guard: stops when the certificate expires" "exit=1" "$code"
  check "$kind guard: stops within 3 s of expiry (12 s certificate)" "yes" "$([ "$after" -ge 10 ] && [ "$after" -le 15 ] && echo yes || echo "no, ${after}s")"
done

# Client-side server identity (Node agent of projects -> users).
NODE_ID='const a=require("/app/tls/pkiTls").clientAgent();
const r=require("https").request({host:"users",port:10001,path:"/",agent:a,servername:process.argv[1]},
 s=>{console.log("http");process.exit(0)});r.on("error",e=>{console.log(e.code||"error");process.exit(0)});r.end()'
check "projects client: expected name users" "http" "$(docker exec $P-projects-1 node -e "$NODE_ID" users)"
check "projects client: server name img_storage on the users server" "ERR_TLS_CERT_ALTNAME_INVALID" \
  "$(docker exec $P-projects-1 node -e "$NODE_ID" img_storage)"
# expand_ai -> generative-mock with requests (cert + CA); the IP has no SAN.
PY_ID='import socket,sys,requests
d="/run/secrets/pki/"
host=sys.argv[1] if sys.argv[1]!="ip" else socket.gethostbyname("generative-mock")
try:
    r=requests.get(f"https://{host}:7860/sdapi/v1/samplers",cert=(d+"service.crt",d+"service.key"),verify=d+"ca.crt",timeout=5)
    print(r.status_code)
except requests.exceptions.SSLError:
    print("SSLError")'
check "expand_ai client: generative-mock by name" "200" "$(docker exec $P-expand_ai_tool-1 python -c "$PY_ID" generative-mock)"
check "expand_ai client: generative-mock by IP (name mismatch)" "SSLError" "$(docker exec $P-expand_ai_tool-1 python -c "$PY_ID" ip)"

echo "B5 guard and client identity: $pass/$((pass+fail)) checks passed"
[ $fail -eq 0 ]
