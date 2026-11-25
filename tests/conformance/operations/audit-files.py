"""Changed-file audit. Never print secrets, private paths or matching text."""
import base64,hashlib,json,os,re,subprocess
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
roots=[Path.home()/'picturas-secrets',Path.home()/'picturas-secrets/b11-fixture']
needles=set()
for root in roots:
 for file in (root/'values').iterdir():
  value=file.read_bytes().strip()
  if len(value)>=6:needles.update((value,base64.b64encode(value)))
 for file in [root/'jwt/rs256-private.pem',root/'pki/ca/ca.key',*(root/'pki/services').glob('*/service.key')]:
  if file.exists():
   value=file.read_bytes().strip();needles.add(value)
   needles.add(json.dumps(value.decode())[1:-1].encode())
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO)
paths=set(git('diff','--name-only','-z').decode().split('\0')+git('ls-files','--others','--exclude-standard','-z').decode().split('\0'))-{''}
findings=[];checked=0
patterns=[('jwt',rb'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'),
 ('private_key',rb'-----BEGIN (?:RSA |EC |ENCRYPTED )?PRIVATE KEY-----\s+[A-Za-z0-9+/=]{40,}'),
 ('signed_url',rb'[?&]X-Amz-Signature=[a-fA-F0-9]{32,}'),
 ('share_url',rb'[?&]share=[a-fA-F0-9-]{32,}')]
for name in sorted(paths):
 file=REPO/name
 if not file.is_file():continue
 data=file.read_bytes();checked+=1
 if any(needle in data for needle in needles):findings.append({'file':name,'kind':'installation_value'})
 for kind,pattern in patterns:
  if re.search(pattern,data):findings.append({'file':name,'kind':kind})
frozen=['evaluation/med.py','evaluation/medlib','evaluation/criteria.yaml','evaluation/cases']
frozen_unchanged=not git('diff','--name-only','--',*frozen)
env_ignored=subprocess.run(['git','check-ignore','-q','evaluation/.env.med'],cwd=REPO).returncode==0
result={'changed_files_scanned':checked,'private_patterns_checked':len(needles),'findings':findings,
 'frozen_instrument_unchanged':frozen_unchanged,'measurement_env_ignored':env_ignored}
out=REPO/'tests/conformance/results/2026-11-24/B11-audit.json';out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'files':checked,'findings':len(findings),'frozen_unchanged':frozen_unchanged,'env_ignored':env_ignored}))
if findings or not frozen_unchanged or not env_ignored:raise SystemExit(1)
