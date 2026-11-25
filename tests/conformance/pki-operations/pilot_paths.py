"""Persistent private fixture locations; no secret values or ephemeral TMPDIR state."""
import json
import os
from pathlib import Path

ROOT=Path(os.environ.get('PICTURAS_PKI_PILOT_ROOT',str(Path.home()/'picturas-secrets/b10-fixture')))
CACHE=Path.home()/'.cache/picturas-pki-b10'
marker=ROOT/'fixture-installation.json'
PROJECT=json.loads(marker.read_text())['project'] if marker.exists() else 'picturas-pki-pilot-b10'
OVERRIDE=ROOT/'compose.override.json'
PROFILE=ROOT/'browser-profile'
CERTUTIL=CACHE/'nss/extracted/usr/bin/certutil'
