#!/bin/sh
set -eu

# Linux bind mounts retain the host UID and private modes. Copy only this
# service's material to tmpfs before the official entrypoint drops privileges.
private=/run/picturas-private
mkdir -p "$private/pki"
cp /run/secrets/pki/ca.crt /run/secrets/pki/service.crt /run/secrets/pki/service.key "$private/pki/"
cp /run/secrets/rabbitmq/definitions.json "$private/definitions.json"
chown -R rabbitmq:rabbitmq "$private"
chmod 700 "$private" "$private/pki"
chmod 600 "$private/pki/service.key" "$private/definitions.json"
chmod 644 "$private/pki/ca.crt" "$private/pki/service.crt"
exec /usr/local/bin/docker-entrypoint.sh "$@"
