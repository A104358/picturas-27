#!/usr/bin/env bash
# S19 / B1 acceptance: no current secret of this installation is in the repository.
# Searches every value in $PICTURAS_SECRETS_DIR (values/, the RS256 private key and the CA/service keys)
# in tracked and untracked-but-not-ignored files. The values are never printed.
# It also lists where the formerly committed secrets still appear, for information: they are no longer
# accepted by any service, and the frozen measurement tool (evaluation/) keeps them on purpose.
set -uo pipefail

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
[ -n "${PICTURAS_SECRETS_DIR:-}" ] || { echo "PICTURAS_SECRETS_DIR is not set"; exit 2; }
S=$PICTURAS_SECRETS_DIR
fail=0; n=0

search() { # <fixed string>: true if found in the working tree (tracked + untracked, not ignored)
  git -C "$ROOT" grep -q --untracked -F -e "$1" 2>/dev/null
}

for f in "$S"/values/*; do
  v=$(cat "$f"); n=$((n + 1))
  if search "$v"; then echo "FAIL current secret found in the repository: values/$(basename "$f")"; fail=1; fi
done
# Keys: search a distinctive line of the base64 body of each private key.
while IFS= read -r k; do
  line=$(grep -v -- '-----' "$k" | sed -n '2p'); [ -n "$line" ] || line=$(grep -v -- '-----' "$k" | head -1)
  n=$((n + 1))
  if search "$line"; then echo "FAIL private key material found in the repository: ${k#"$S"/}"; fail=1; fi
done < <(find "$S" -name '*.key' -o -name 'rs256-private.pem')
echo "checked $n current secrets"

echo "## formerly committed secrets (information; not valid any more)"
for old in lisan_al_gaib admin123 card_secret_key uma-frase-secreta-bem-grande-ou-64-hex picturas-kek-passphrase-change-me 'RABBITMQ_DEFAULT_PASS: "password"' '"password": "password"'; do
  hits=$(git -C "$ROOT" grep -l --untracked -F -e "$old" -- . ':!docs' ':!evaluation' ':!tests/spikes' ':!memory-bank' ':!tests/conformance/mtls-pki' 2>/dev/null | tr '\n' ' ')
  printf '  %-40s %s\n' "$old" "${hits:-none outside docs/evaluation/tests}"
done

[ $fail -eq 0 ] && echo "S19 git grep: passed (no current secret in the repository)" || { echo "S19 git grep: FAILED"; exit 1; }
