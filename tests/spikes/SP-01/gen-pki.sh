#!/usr/bin/env bash
# Throwaway PKI for the SP-01 spike. Keys stay in ./pki (git-ignored); never reuse them.
set -euo pipefail
cd "$(dirname "$0")" && mkdir -p pki && cd pki
for ca in ca otherca; do
  openssl req -x509 -new -newkey rsa:2048 -nodes -keyout $ca.key -subj "/CN=spike-$ca" -days 365 -sha256 \
    -addext basicConstraints=critical,CA:true -addext keyUsage=critical,keyCertSign,cRLSign -out $ca.crt 2>/dev/null
done
mk() { # <name> <issuing ca>
  openssl req -new -newkey rsa:2048 -nodes -keyout $1.key -subj "/CN=$1" -out $1.csr 2>/dev/null
  printf "subjectAltName=DNS:$1\nextendedKeyUsage=serverAuth,clientAuth\n" > $1.ext
  openssl x509 -req -in $1.csr -CA $2.crt -CAkey $2.key -CAcreateserial -days 30 -sha256 -extfile $1.ext -out $1.crt 2>/dev/null
}
mk backend ca; mk nginx-client ca; mk front ca; mk rogue otherca
