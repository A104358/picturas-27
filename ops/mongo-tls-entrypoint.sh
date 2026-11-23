#!/bin/sh
set -eu

# The private key is mounted read-only and copied only into the container's tmpfs.
cat /run/secrets/pki/service.key /run/secrets/pki/service.crt > /tmp/picturas-mongo.pem
chown mongodb:mongodb /tmp/picturas-mongo.pem
chmod 600 /tmp/picturas-mongo.pem
exec /usr/local/bin/docker-entrypoint.sh mongod "$@" \
  --tlsMode requireTLS \
  --tlsCertificateKeyFile /tmp/picturas-mongo.pem \
  --tlsCAFile /run/secrets/pki/ca.crt \
  --tlsAllowConnectionsWithoutCertificates \
  --auth
