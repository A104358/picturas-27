#!/usr/bin/env bash
# Local PKI of one PictuRAS installation (PKI-C1 A).
#
#   ops/pki.sh init            create the installation CA (365 days) and issue every service certificate
#   ops/pki.sh issue <svc|all> issue (or reissue) service certificates (30 days, new key)
#   ops/pki.sh renew --project <name> [--service <svc|all>] [--force]  drain, renew and apply
#   ops/pki.sh retire --project <name>  replace the CA and every key, remaining isolated until verified
#   ops/pki.sh check           verify CA and service certificates before starting the stack
#   ops/pki.sh list            show the current certificates (public data only)
#
# Everything lives under $PICTURAS_SECRETS_DIR/pki, outside the checkout:
#   ca/ca.key, ca/ca.crt           the CA key never leaves this directory (never mounted in a container)
#   services/<svc>/service.{key,crt}, services/<svc>/ca.crt   what each service mounts read-only
#   registry.tsv                   public log of every issued certificate (no keys)
# There is no renewal daemon: the administrator runs `renew` (PKI-C1 A).
set -euo pipefail

CA_DAYS=365
CERT_DAYS=30
RENEW_DAYS=7

# service | DNS/IP names (comma separated, the first is the Docker service name) | extended key usage
SERVICES=(
  "nginx|nginx,localhost,IP:127.0.0.1|serverAuth,clientAuth"
  "frontend|frontend|serverAuth,clientAuth"
  "api_gateway|api_gateway|serverAuth,clientAuth"
  "ws_gateway|ws_gateway|serverAuth,clientAuth"
  "projects|projects|serverAuth,clientAuth"
  "users|users|serverAuth,clientAuth"
  "subscriptions|subscriptions|serverAuth,clientAuth"
  "img_storage|img_storage|serverAuth,clientAuth"
  "seaweedfs|seaweedfs,localhost|serverAuth,clientAuth"
  "rabbitmq|rabbitmq|serverAuth"
  "projects_mongoDB|projects_mongoDB|serverAuth"
  "users_mongoDB|users_mongoDB|serverAuth"
  "subscriptions_mongoDB|subscriptions_mongoDB|serverAuth"
  "generative-mock|generative-mock|serverAuth,clientAuth"
  "expand_ai_tool|expand_ai_tool|clientAuth"
)

die() { echo "pki: $*" >&2; exit 1; }

secrets_dir() {
  [ -n "${PICTURAS_SECRETS_DIR:-}" ] || die "PICTURAS_SECRETS_DIR is not set"
  local repo dir
  repo=$(cd "$(dirname "$0")/.." && pwd -P)
  mkdir -p "$PICTURAS_SECRETS_DIR"
  dir=$(cd "$PICTURAS_SECRETS_DIR" && pwd -P)
  case "$dir/" in "$repo/"*) die "PICTURAS_SECRETS_DIR must be outside the checkout ($repo)" ;; esac
  echo "$dir"
}

ROOT=$(secrets_dir)
PKI="$ROOT/pki"
CA_DIR="$PKI/ca"
SVC_DIR="$PKI/services"
REGISTRY="$PKI/registry.tsv"
umask 077

service_entry() {
  local e
  for e in "${SERVICES[@]}"; do [ "${e%%|*}" = "$1" ] && { echo "$e"; return; }; done
  die "unknown service: $1"
}

all_services() { local e; for e in "${SERVICES[@]}"; do echo "${e%%|*}"; done; }

expires_within() { # <cert> <seconds>: true if the certificate expires within that time (or already has)
  ! openssl x509 -in "$1" -noout -checkend "$2" >/dev/null 2>&1
}

fingerprint() { openssl x509 -in "$1" -noout -fingerprint -sha256 | cut -d= -f2; }

register() { # <svc> <cert>
  [ -f "$REGISTRY" ] || printf 'issued_at\tservice\tserial\tsubject\tissuer\tsan\teku\tnot_before\tnot_after\tsha256\n' > "$REGISTRY"
  local c=$2
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$(date -u +%FT%TZ)" "$1" \
    "$(openssl x509 -in "$c" -noout -serial | cut -d= -f2)" \
    "$(openssl x509 -in "$c" -noout -subject -nameopt RFC2253 | sed 's/^subject=//')" \
    "$(openssl x509 -in "$c" -noout -issuer -nameopt RFC2253 | sed 's/^issuer=//')" \
    "$(openssl x509 -in "$c" -noout -ext subjectAltName 2>/dev/null | tail -n +2 | tr -d " ")" \
    "$(openssl x509 -in "$c" -noout -ext extendedKeyUsage 2>/dev/null | tail -n +2 | sed "s/^ *//")" \
    "$(openssl x509 -in "$c" -noout -startdate | cut -d= -f2)" \
    "$(openssl x509 -in "$c" -noout -enddate | cut -d= -f2)" \
    "$(fingerprint "$c")" >> "$REGISTRY"
  chmod 644 "$REGISTRY"
}

require_ca() {
  [ -f "$CA_DIR/ca.key" ] && [ -f "$CA_DIR/ca.crt" ] || die "no CA in $CA_DIR (run: ops/pki.sh init)"
  expires_within "$CA_DIR/ca.crt" 0 && die "the CA has expired; replace it (new CA and reissue everything, PKI-C2 B)"
  return 0
}

cmd_init() {
  [ -e "$CA_DIR/ca.key" ] && die "a CA already exists in $CA_DIR; init does not replace it"
  mkdir -p "$CA_DIR" "$SVC_DIR"
  chmod 700 "$ROOT" "$PKI" "$CA_DIR" "$SVC_DIR"
  openssl ecparam -name prime256v1 -genkey -noout -out "$CA_DIR/ca.key"
  openssl req -x509 -new -key "$CA_DIR/ca.key" -sha256 -days "$CA_DAYS" \
    -subj "/O=PictuRAS/CN=PictuRAS installation CA $(date -u +%Y%m%d%H%M%S)" \
    -addext "basicConstraints=critical,CA:true,pathlen:0" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" \
    -addext "subjectKeyIdentifier=hash" \
    -out "$CA_DIR/ca.crt" 2>/dev/null
  chmod 600 "$CA_DIR/ca.key"; chmod 644 "$CA_DIR/ca.crt"
  register "CA" "$CA_DIR/ca.crt"
  echo "pki: CA created ($CA_DIR/ca.crt, valid $CA_DAYS days)"
  cmd_issue all
}

issue_one() {
  local entry svc names eku dir san n tmp
  entry=$(service_entry "$1")
  svc=${entry%%|*}; names=$(echo "$entry" | cut -d'|' -f2); eku=${entry##*|}
  # Never issue past the CA validity: the CA must outlive the new certificate.
  expires_within "$CA_DIR/ca.crt" $((CERT_DAYS * 86400)) \
    && die "the CA expires within $CERT_DAYS days; replace the CA before issuing ($svc)"
  san=""
  IFS=, read -ra parts <<< "$names"
  for n in "${parts[@]}"; do
    case $n in IP:*) san="$san,$n" ;; *) san="$san,DNS:$n" ;; esac
  done
  san=${san#,}
  dir="$SVC_DIR/$svc"; mkdir -p "$dir"; chmod 700 "$dir"
  tmp=$(mktemp -d)
  openssl ecparam -name prime256v1 -genkey -noout -out "$tmp/service.key"
  openssl req -new -key "$tmp/service.key" -subj "/O=PictuRAS/CN=$svc" -out "$tmp/service.csr" 2>/dev/null
  printf 'basicConstraints=critical,CA:false\nkeyUsage=critical,digitalSignature,keyAgreement\nextendedKeyUsage=%s\nsubjectAltName=%s\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid\n' \
    "$eku" "$san" > "$tmp/ext.cnf"
  openssl x509 -req -in "$tmp/service.csr" -CA "$CA_DIR/ca.crt" -CAkey "$CA_DIR/ca.key" \
    -set_serial "0x$(openssl rand -hex 16)" -days "$CERT_DAYS" -sha256 -extfile "$tmp/ext.cnf" \
    -out "$tmp/service.crt" 2>/dev/null
  openssl verify -CAfile "$CA_DIR/ca.crt" "$tmp/service.crt" >/dev/null || die "issued certificate does not verify ($svc)"
  # Replace atomically: key and certificate always match.
  mv "$tmp/service.key" "$dir/service.key"; mv "$tmp/service.crt" "$dir/service.crt"
  cp "$CA_DIR/ca.crt" "$dir/ca.crt"
  chmod 600 "$dir/service.key"; chmod 644 "$dir/service.crt" "$dir/ca.crt"
  rm -rf "$tmp"
  register "$svc" "$dir/service.crt"
  echo "pki: issued $svc ($san; $eku; $CERT_DAYS days)"
}

cmd_issue() {
  [ $# -ge 1 ] || die "usage: ops/pki.sh issue <service|all>"
  require_ca
  local s
  if [ "$1" = all ]; then for s in $(all_services); do issue_one "$s"; done; else issue_one "$1"; fi
}

cmd_renew() {
  # The applied operation owns draining, process/socket replacement and verification.
  exec python3 "$(dirname "$0")/maintenance.py" renew "$@"
}

cmd_retire() {
  exec python3 "$(dirname "$0")/maintenance.py" retire "$@"
}

perm() {
  local mode
  if mode=$(stat -f %Lp "$1" 2>/dev/null); then printf '%s\n' "$mode"; else stat -c %a "$1"; fi
}

cmd_check() {
  local fail=0 warn=0 s dir cert key mod_c mod_k entry expected_eku actual_eku usage label eku subject
  if [ ! -f "$CA_DIR/ca.crt" ]; then echo "FAIL CA missing ($CA_DIR/ca.crt)"; exit 1; fi
  if expires_within "$CA_DIR/ca.crt" 0; then echo "FAIL CA expired"; fail=1
  elif expires_within "$CA_DIR/ca.crt" $((CERT_DAYS * 86400)); then echo "WARN CA expires within $CERT_DAYS days: plan its replacement"; warn=1
  else echo "ok   CA ($(openssl x509 -in "$CA_DIR/ca.crt" -noout -enddate | cut -d= -f2))"; fi
  for s in $(all_services); do
    dir="$SVC_DIR/$s"; cert="$dir/service.crt"; key="$dir/service.key"
    if [ ! -f "$cert" ] || [ ! -f "$key" ]; then echo "FAIL $s: certificate or key missing"; fail=1; continue; fi
    if ! openssl verify -CAfile "$CA_DIR/ca.crt" "$cert" >/dev/null 2>&1; then
      echo "FAIL $s: does not verify against the current CA (expired or from another CA)"; fail=1; continue
    fi
    if ! cmp -s "$dir/ca.crt" "$CA_DIR/ca.crt"; then echo "FAIL $s: ca.crt differs from the current CA"; fail=1; continue; fi
    mod_c=$(openssl x509 -in "$cert" -noout -pubkey | openssl sha256)
    mod_k=$(openssl pkey -in "$key" -pubout 2>/dev/null | openssl sha256)
    if [ "$mod_c" != "$mod_k" ]; then echo "FAIL $s: key does not match certificate"; fail=1; continue; fi
    if ! openssl x509 -in "$cert" -noout -ext subjectAltName | grep -q "DNS:$s\(,\|$\)"; then
      echo "FAIL $s: SAN does not contain DNS:$s"; fail=1; continue
    fi
    entry=$(service_entry "$s")
    expected_eku=${entry##*|}
    actual_eku=$(openssl x509 -in "$cert" -noout -ext extendedKeyUsage 2>/dev/null | tail -n +2)
    IFS=, read -ra usages <<< "$expected_eku"
    for usage in "${usages[@]}"; do
      case "$usage" in
        serverAuth) label="TLS Web Server Authentication" ;;
        clientAuth) label="TLS Web Client Authentication" ;;
      esac
      if ! grep -Fq "$label" <<< "$actual_eku"; then
        echo "WARN $s: missing EKU $usage (run: ops/pki.sh issue $s)"; warn=1
      fi
    done
    if [ "$(perm "$key")" != 600 ]; then echo "FAIL $s: key permissions are not 600"; fail=1; continue; fi
    subject=$(openssl x509 -in "$cert" -noout -subject -nameopt RFC2253 | sed 's/^subject=//')
    if ! printf '%s\n' "$subject" | grep -Eq "(^|,)CN=$s(,|$)"; then
      echo "FAIL $s: certificate CN differs from service identity"; fail=1; continue
    fi
    entry=$(service_entry "$s"); eku=${entry##*|}
    if [[ "$eku" == *serverAuth* ]] && ! openssl verify -purpose sslserver -CAfile "$CA_DIR/ca.crt" "$cert" >/dev/null 2>&1; then
      echo "FAIL $s: invalid server purpose"; fail=1; continue
    fi
    if [[ "$eku" == *clientAuth* ]] && ! openssl verify -purpose sslclient -CAfile "$CA_DIR/ca.crt" "$cert" >/dev/null 2>&1; then
      echo "FAIL $s: invalid client purpose"; fail=1; continue
    fi
    if expires_within "$cert" $((RENEW_DAYS * 86400)); then
      echo "WARN $s: expires within $RENEW_DAYS days (run: ops/pki.sh renew)"; warn=1
    else
      echo "ok   $s ($(openssl x509 -in "$cert" -noout -enddate | cut -d= -f2))"
    fi
  done
  # The CA key must never sit next to what containers mount.
  if find "$SVC_DIR" -name 'ca.key' | grep -q .; then echo "FAIL a CA key was found under $SVC_DIR"; fail=1; fi
  [ $fail -eq 0 ] || { echo "pki check: FAILED"; exit 1; }
  [ $warn -eq 0 ] && echo "pki check: passed" || echo "pki check: passed with warnings"
}

cmd_list() {
  local s cert
  printf '%-22s %-26s %-26s %s\n' service not_after eku sha256
  for s in CA $(all_services); do
    if [ "$s" = CA ]; then cert="$CA_DIR/ca.crt"; else cert="$SVC_DIR/$s/service.crt"; fi
    [ -f "$cert" ] || { printf '%-22s missing\n' "$s"; continue; }
    printf '%-22s %-26s %-26s %s\n' "$s" "$(openssl x509 -in "$cert" -noout -enddate | cut -d= -f2)" \
      "$(openssl x509 -in "$cert" -noout -ext extendedKeyUsage 2>/dev/null | tail -n +2 | sed 's/^ *//;s/TLS Web //g;s/ Authentication//g')" \
      "$(fingerprint "$cert" | cut -c1-23)…"
  done
}

case "${1:-}" in
  init) cmd_init ;;
  issue) shift; cmd_issue "$@" ;;
  renew) shift; cmd_renew "$@" ;;
  retire) shift; cmd_retire "$@" ;;
  check) cmd_check ;;
  list) cmd_list ;;
  *) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
