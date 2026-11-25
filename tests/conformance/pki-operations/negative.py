"""Real fail-closed fault injection on the owned pilot, after all comparable trials.

No old CA is restored. Temporary leaf faults are repaired with the SAME current
material while all participants remain stopped. No business message is changed.
"""
import datetime as dt,json,os,subprocess,time,uuid
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID,ExtendedKeyUsageOID
from pilot_paths import ROOT,PROJECT,OVERRIDE
REPO=Path(__file__).resolve().parents[3]
ENV=dict(os.environ,PICTURAS_SECRETS_DIR=str(ROOT))
OUT=REPO/'tests/conformance/results/2026-11-24/B10-negative-real.json'
COMPOSE=['docker','compose','-p',PROJECT,'-f',str(REPO/'docker-compose.yaml'),'-f',str(OVERRIDE)]
PRIVATE=ROOT/'negative-tests';PRIVATE.mkdir(mode=0o700,exist_ok=True)
def run(args,timeout=600):return subprocess.run(args,cwd=REPO,env=ENV,capture_output=True,timeout=timeout)
def must(args):
 p=run(args)
 if p.returncode:raise RuntimeError('precondition_command_failed')
 return p
def inventory():
 ids=must(['docker','ps','-aq','--filter','label=com.docker.compose.project='+PROJECT]).stdout.decode().split()
 return json.loads(must(['docker','inspect',*ids]).stdout)
def state():return json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
rows=[]
def check(label,result):
 stopped=all(not p['State']['Running'] and p['State']['Pid']==0 for p in inventory())
 closed=(ROOT/'maintenance-gate/admissions-closed').exists()
 row={'case':label,'command_refused':result.returncode!=0,'all_processes_stopped':stopped,'admissions_closed':closed,
      'observed_at':dt.datetime.now(dt.timezone.utc).isoformat()}
 rows.append(row);OUT.write_text(json.dumps(rows,indent=2)+'\n')
 if not all(row[k] for k in ('command_refused','all_processes_stopped','admissions_closed')):raise RuntimeError('fault_did_not_fail_closed')
 print('PASS '+label,flush=True)
assert state()['phase']=='reopened'
old_archive=state()['pki_change']['old_archive']
for name in ['diagnostic-control-retry','trial-1','trial-2','trial-3']:
 trial=ROOT/'pilot'/name
 assert (trial/'completed.json').exists()
 must(['docker','run','--rm','--user',str(os.getuid())+':'+str(os.getgid()),'--network',PROJECT+'_elk',
  '-v',str(ROOT)+':/installation:ro','-v',str(trial)+':/proof:rw',
  '-v',str(REPO/'tests/conformance/pki-operations')+':/tests:ro','picturas-pki-observer','python',
  '/tests/technical_job.py','archive-quarantine'])
# A real local worker with no domain Process also blocks planned maintenance.
trial=ROOT/'planned-worker';trial.mkdir(mode=0o700)
identity=json.loads((ROOT/'pilot/identity.json').read_text());mid=str(uuid.uuid4())
directory='/app/images/pki-fixture/'+mid
fixture={**identity,'message_id':mid,'input':directory+'/input.mp4','output':directory+'/output.mp4'}
(trial/'fixture.json').write_text(json.dumps(fixture));(trial/'fixture.json').chmod(0o600)
video=next(p['Id'] for p in inventory() if p['Config']['Labels']['com.docker.compose.service']=='video_tool')
must(['docker','exec',video,'mkdir','-p',directory])
must(['docker','cp',str(ROOT/'source.mp4'),video+':'+fixture['input']])
must(['docker','run','--rm','--user',str(os.getuid())+':'+str(os.getgid()),'--network',PROJECT+'_elk',
 '-v',str(ROOT)+':/installation:ro','-v',str(trial)+':/proof:rw',
 '-v',str(REPO/'tests/conformance/pki-operations')+':/tests:ro','picturas-pki-observer','python','/tests/technical_job.py','publish'])
def active():return b'"active_count": 1' in run(['docker','exec',video,'sh','-c','cat /run/picturas/picturas-work-*.json']).stdout
deadline=time.monotonic()+10
while not active() and time.monotonic()<deadline:time.sleep(.1)
assert active()
before={p['Id']:p['State']['Pid'] for p in inventory()}
deferred=run(['ops/maintenance.sh','isolate','--project',PROJECT,'--mode','planned','--compose-file',str(OVERRIDE)])
assert deferred.returncode and state()['phase']=='deferred_busy'
assert before=={p['Id']:p['State']['Pid'] for p in inventory()}
assert any(w['service']=='video_tool' for w in state()['drain_observations'][-1]['active_local_workers'])
rows.append({'case':'actual local video work without Process defers planned cut','passed':True,'participants_unchanged':True})
OUT.write_text(json.dumps(rows,indent=2)+'\n')
print('PASS actual local video work defers planned cut without stopping participants',flush=True)
must(['ops/maintenance.sh','cancel','--project',PROJECT])
deadline=time.monotonic()+90
while active() and time.monotonic()<deadline:time.sleep(.2)
assert not active()
must(['ops/maintenance.sh','isolate','--project',PROJECT,'--mode','planned','--compose-file',str(OVERRIDE)])
operation=state()['operation']
base=['ops/maintenance.sh','reopen','--project',PROJECT,'--compose-file',str(OVERRIDE)]
stale=PRIVATE/'stale-mount.json'
stale.write_text(json.dumps({'services':{'frontend':{'volumes':[old_archive+'/services/frontend:/run/secrets/pki:ro']}}}))
check('participant with withdrawn PKI mount',run([*base,'--compose-file',str(stale)]))
certdir=ROOT/'pki/services/frontend'
saved={name:(certdir/name).read_bytes() for name in ['service.crt','service.key']}
try:
 ca=x509.load_pem_x509_certificate((ROOT/'pki/ca/ca.crt').read_bytes())
 key=serialization.load_pem_private_key((ROOT/'pki/ca/ca.key').read_bytes(),password=None)
 leafkey=ec.generate_private_key(ec.SECP256R1());now=dt.datetime.utcnow()
 leaf=(x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'frontend')]))
  .issuer_name(ca.subject).public_key(leafkey.public_key()).serial_number(x509.random_serial_number())
  .not_valid_before(now-dt.timedelta(days=2)).not_valid_after(now-dt.timedelta(days=1))
  .add_extension(x509.SubjectAlternativeName([x509.DNSName('frontend')]),critical=False)
  .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
  .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH,ExtendedKeyUsageOID.CLIENT_AUTH]),critical=False)
  .sign(key,hashes.SHA256()))
 (certdir/'service.key').write_bytes(leafkey.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
 (certdir/'service.crt').write_bytes(leaf.public_bytes(serialization.Encoding.PEM))
 check('expired current-CA participant certificate',run(base))
 for name in saved:(certdir/name).write_bytes((ROOT/'pki/services/users'/name).read_bytes())
 check('wrong service identity from the current CA',run(base))
finally:
 for name,contents in saved.items():(certdir/name).write_bytes(contents)
must(['ops/pki.sh','check'])
restart=PRIVATE/'restart-failure.json'
restart.write_text(json.dumps({'services':{'frontend':{'command':['node','-e','process.exit(73)'],'restart':'no'}}}))
check('participant restart fails after partial application',run([*base,'--compose-file',str(restart)]))
assert state()['operation']==operation and state()['phase']=='failed_isolated'
must(base)
assert state()['phase']=='reopened' and state()['operation']==operation
rows.append({'case':'repaired current configuration passes; no old-CA rollback','passed':True})
OUT.write_text(json.dumps(rows,indent=2)+'\n')
print('PASS all real faults blocked reopening; repaired current configuration verified',flush=True)
