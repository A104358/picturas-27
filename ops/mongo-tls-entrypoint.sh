#!/bin/sh
set -eu

# The private key is mounted read-only and copied only into the container's tmpfs.
cat /run/secrets/pki/service.key /run/secrets/pki/service.crt > /tmp/picturas-mongo.pem
cp /run/secrets/pki/ca.crt /tmp/picturas-mongo-ca.crt
cp /run/secrets/mongo/init.js /docker-entrypoint-initdb.d/init.js
chown mongodb:mongodb /tmp/picturas-mongo.pem
chown mongodb:mongodb /docker-entrypoint-initdb.d/init.js
chmod 600 /tmp/picturas-mongo.pem
chmod 600 /docker-entrypoint-initdb.d/init.js
chmod 644 /tmp/picturas-mongo-ca.crt
exec /usr/local/bin/docker-entrypoint.sh mongod "$@" \
  --tlsMode requireTLS \
  --tlsCertificateKeyFile /tmp/picturas-mongo.pem \
  --tlsCAFile /tmp/picturas-mongo-ca.crt \
  --tlsAllowConnectionsWithoutCertificates \
  --auth
