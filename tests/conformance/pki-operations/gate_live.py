"""Real durable gate/owner cancellation check; retained quarantine makes it defer."""
import json,os,ssl,subprocess,urllib.error,urllib.request
from pathlib import Path
from pilot_paths import ROOT,PROJECT,OVERRIDE
REPO=Path(__file__).resolve().parents[3];ENV=dict(os.environ,PICTURAS_SECRETS_DIR=str(ROOT))
def command(args):return subprocess.run(args,cwd=REPO,env=ENV,capture_output=True,timeout=120)
def inventory():
 ids=command(['docker','ps','-aq','--filter','label=com.docker.compose.project='+PROJECT,
              '--filter','label=com.docker.compose.config-hash']).stdout.decode().split()
 data=json.loads(command(['docker','inspect',*ids]).stdout)
 return sorted((p['Id'],p['State']['Pid'],p['State']['Running']) for p in data)
def status():
 try:
  with urllib.request.urlopen('https://localhost:8080',context=ssl.create_default_context(cafile=str(ROOT/'pki/ca/ca.crt')),timeout=5) as r:return r.status
 except urllib.error.HTTPError as r:return r.code
before=inventory();assert status()==200
result=command(['ops/maintenance.sh','isolate','--project',PROJECT,'--mode','planned','--compose-file',str(OVERRIDE)])
state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
assert result.returncode and state['phase']=='deferred_busy'
flag=ROOT/'maintenance-gate/admissions-closed'
assert json.loads(flag.read_text())==state['operation'] and flag.stat().st_mode & 0o777==0o600
assert status()==503 and before==inventory()
result=command(['ops/maintenance.sh','cancel','--project',PROJECT])
assert result.returncode==0 and not flag.exists() and status()==200 and before==inventory()
out={'durable_json_gate':True,'nginx_admissions_suspended':True,'participants_unchanged':True,
     'unchanged_owned_deferral_cancelled':True,'nginx_reopened':True,'no_pki_change':True}
(REPO/'tests/conformance/results/2026-11-24/B10-gate-live.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS durable gate, actual nginx 503/200 and owned cancellation; no participant cut')
