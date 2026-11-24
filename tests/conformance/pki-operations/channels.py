"""Read-only extra native-channel observations for the final channel matrix."""
import json,os,subprocess
from pathlib import Path
from pilot_paths import ROOT,PROJECT
REPO=Path(__file__).resolve().parents[3]
def run(args):return subprocess.run(args,capture_output=True,timeout=120)
cid=run(['docker','ps','-q','--filter','label=com.docker.compose.project='+PROJECT,
         '--filter','label=com.docker.compose.service=seaweedfs']).stdout.decode().strip()
assert cid
p=run(['docker','run','--rm','--user',str(os.getuid())+':'+str(os.getgid()),'--network','container:'+cid,
 '-v',str(ROOT)+':/installation:ro','-v',str(ROOT/'maintenance'/PROJECT)+':/state:ro',
 '-v',str(REPO/'ops')+':/ops:ro','-v',str(REPO/'tests/conformance/pki-operations')+':/tests:ro',
 'picturas-maintenance-probe','python','/tests/seaweed_loopback.py'])
if p.returncode:raise RuntimeError('loopback_probe_failed_no_credentials_reported')
value=json.loads(p.stdout)
out=REPO/'tests/conformance/results/2026-11-24/B10-seaweed-internal.json'
out.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'internal_controls':len(value['rows']),'passed':value['passed'],
 'failed':[r for r in value['rows'] if not r['passed']]}))
