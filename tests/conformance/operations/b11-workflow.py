"""B11 regression lifecycle, with retained volumes and an unchanged med instrument."""
import json,os,re,signal,subprocess,sys,time
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
ROOT=Path.home()/'picturas-secrets'
ENV=dict(os.environ,PICTURAS_SECRETS_DIR=str(ROOT),MED_WS_JOIN_FORMAT='v2')
OUT=REPO/'tests/conformance/results/2026-11-24';OUT.mkdir(exist_ok=True)
def run(args,cwd=REPO,timeout=1800):return subprocess.run(args,cwd=cwd,env=ENV,capture_output=True,timeout=timeout)
def must(args,**kw):
 p=run(args,**kw)
 if p.returncode:raise RuntimeError('command_failed_'+Path(args[0]).name)
 return p
def log(label,args,**kw):
 p=run(args,**kw);value=(p.stdout+p.stderr).decode(errors='replace')
 for file in (ROOT/'values').iterdir():
  secret=file.read_text().strip()
  if len(secret)>=6:value=value.replace(secret,'[REDACTED]')
 value=re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+','[REDACTED-JWT]',value)
 if label.lower().endswith('f01') and re.search(r'^exit: (?!0$)\d+',value,re.M):p.returncode=1
 (OUT/('B11-'+label+'.txt')).write_text(value)
 print(('PASS ' if p.returncode==0 else 'FAIL ')+label,flush=True)
 if p.returncode:raise RuntimeError('check_failed_'+label)
def compose(project):return ['docker','compose','-p',project,'-f',str(REPO/'docker-compose.yaml')]
def alone(project):
 names=must(['docker','ps','--filter','label=com.docker.compose.config-hash','--format','{{.Label "com.docker.compose.project"}}']).stdout.decode().split()
 assert all(not n.startswith('picturas') or n==project for n in names)
action=sys.argv[1]
if action=='guard':
 alone('picturas-dev')
 must([*compose('picturas-dev'),'up','-d','--no-build','--wait','--wait-timeout','300'])
 try:log('B5-guard',['tests/conformance/mtls-pki/b5-guard.sh','picturas-dev'])
 finally:must([*compose('picturas-dev'),'down'])
 print('PASS dev down after guard; volumes preserved')
elif action=='audit':
 import hashlib
 alone('picturas-dev');manifest={}
 files={'projects':['routes/projects.js','utils/runLifecycle.js','controllers/project.js','controllers/process.js',
   'models/processingRun.js','models/processingArtifact.js','models/project.js','models/process.js','models/result.js','utils/project_msg.js'],
  'users':['routes/users.js','admin/quotaLedger.js','models/user.js','controllers/user.js'],
  'img_storage':['server.js','route/processingOutput.js']}
 for service,paths in files.items():
  identifier=must([*compose('picturas-dev'),'ps','-q',service]).stdout.decode().strip()
  image=json.loads(must(['docker','inspect','--format','{{json .Image}}',identifier]).stdout)
  checked={}
  for relative in paths:
   folder='imageStorageService' if service=='img_storage' else service
   expected=hashlib.sha256((REPO/folder/relative).read_bytes()).hexdigest()
   observed=must(['docker','exec',identifier,'sha256sum','/app/'+relative]).stdout.decode().split()[0]
   assert expected==observed,'runtime_source_mismatch_'+service
   checked[relative]=expected
  manifest[service]={'image_id':image,'source_sha256':checked}
 manifest['administrative_helper']={'image_id':json.loads(must(['docker','image','inspect','--format','{{json .Id}}','picturas-reconcile:1']).stdout)}
 (OUT/'B11-runtime.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS running images match all 16 changed runtime source files')
elif action=='native-quota':
 alone('picturas-dev')
 private=ROOT/'b11-component';private.mkdir(mode=0o700,exist_ok=True)
 marker=private/'case.json';marker.write_text(json.dumps({'operation':__import__('uuid').uuid4().hex}));marker.chmod(0o600)
 must(['docker','build','-t','picturas-reconcile:1','-f','ops/reconcile.Dockerfile','ops'])
 args=['docker','run','--rm','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
  '--user',str(os.getuid())+':'+str(os.getgid()),'--network','picturas-dev_elk','-v',str(REPO/'ops')+':/ops:ro',
  '-v',str(REPO/'tests/conformance/operations')+':/tests:ro','-v',str(private)+':/case:rw']
 for name in ('mongo_projects_admin','mongo_users_admin','rabbit_admin','s3_admin_access','s3_admin_secret'):
  args+=['-v',str(ROOT/'values'/name)+':/installation/values/'+name+':ro']
 for relative in ('pki/ca/ca.crt','pki/services/projects/service.crt','pki/services/projects/service.key'):
  args+=['-v',str(ROOT/relative)+':/installation/'+relative+':ro']
 log('native-quota',[*args,'picturas-reconcile:1','python','/tests/b11-quota-db.py'])
 proof=json.loads((private/'public-proof.json').read_text())
 (OUT/'B11-native-quota.json').write_text(json.dumps(proof,indent=2)+'\n')
elif action=='units':
 log('unit-operations',['python3','-m','unittest','discover','-s','tests/conformance/operations','-p','test_*.py'])
 log('unit-B10',['python3','-m','unittest','discover','-s','tests/conformance/pki-operations','-p','test_maintenance.py'])
 log('unit-quota',['docker','run','--rm','--network','none','-v',str(REPO/'users/tests')+':/app/tests:ro',
   '-v',str(REPO/'users/admin')+':/app/admin:ro','--entrypoint','node','picturas-dev-users','--test','tests/quota-ledger.test.js'])
 log('unit-projects',['docker','run','--rm','--network','none','-v',str(REPO/'projects/tests')+':/app/tests:ro',
   '-v',str(REPO/'projects/controllers')+':/app/controllers:ro','-v',str(REPO/'projects/utils')+':/app/utils:ro',
   '--entrypoint','node','picturas-dev-projects','--test','tests/'])
elif action=='status':
 print(must(['docker','ps','--filter','label=com.docker.compose.config-hash','--format','{{.Names}} {{.Status}}']).stdout.decode())
elif action=='baseline-reuse':
 # The sole outstanding build is an unchanged worker downloading CUDA again.
 assert not must(['git','diff','4a0ce87','HEAD','--','Tools/cut_ai','Tools/utils']).stdout
 manifest=json.loads((OUT/'B10-runtime-manifest.json').read_text())
 image=next(p['image_id'] for p in manifest['services'] if p['service']=='cut_ai_tool')
 must(['docker','image','inspect',image])
 processes=must(['ps','-eo','pid,args']).stdout.decode().splitlines()
 for line in processes:
  parts=line.strip().split(None,1)
  if len(parts)==2 and parts[1].startswith('docker compose -p picturas-dev up -d --build'):
   os.kill(int(parts[0]),signal.SIGINT)
 time.sleep(1)
 must(['docker','image','tag',image,'picturas-dev-cut_ai_tool'])
 must([*compose('picturas-dev'),'up','-d','--no-build','--wait','--wait-timeout','300'])
 print('PASS base healthy; reused exact B10 cut_ai image with unchanged source')
elif action=='baseline-dev':
 alone('picturas-dev')
 log('baseline-smoke',['python3','tests/conformance/mtls-pki/b1-smoke.py'])
 log('baseline-F02',['evaluation/.venv/bin/python','tests/conformance/data-channels/b2-functional.py'])
 log('baseline-F01',['tests/conformance/run-f01.sh','picturas-dev'])
elif action in ('dev-down','exp-down'):
 project='picturas-dev' if action=='dev-down' else 'picturas-nfr-exp'
 if action=='exp-down':must(['.venv/bin/python','-c','from medlib import dockerctl;dockerctl.stop_probe()'],cwd=REPO/'evaluation')
 must([*compose(project),'down']);print('PASS '+project+' down; volumes preserved')
elif action=='dev-up':
 alone('picturas-dev');must([*compose('picturas-dev'),'build','projects','users','img_storage'])
 must([*compose('picturas-dev'),'up','-d','--no-build','--wait','--wait-timeout','300'])
 print('PASS dev rebuilt and healthy')
elif action=='exp-up':
 alone('picturas-nfr-exp')
 cfg=json.loads(must([*compose('picturas-dev'),'config','--format','json']).stdout)
 for service,definition in cfg['services'].items():
  if definition.get('build'):must(['docker','image','tag','picturas-dev-'+service,'picturas-nfr-exp-'+service])
 code="from medlib import dockerctl;from medlib.config import SETTINGS;assert SETTINGS.project=='picturas-nfr-exp';dockerctl.write_override();dockerctl.compose('up','-d','--no-build','--wait','--wait-timeout','300',timeout=600);dockerctl.start_probe()"
 must(['.venv/bin/python','-c',code],cwd=REPO/'evaluation');print('PASS EXP up; volumes preserved')
elif action=='exp-run':
 alone('picturas-nfr-exp')
 log('EXP-run',['.venv/bin/python','med.py','run','--campaign','EXP','--quick','--metrics','S01,S02,S03,S04,S05,S12,S16,S17,S18,S21'],cwd=REPO/'evaluation')
elif action=='baseline-exp':
 alone('picturas-nfr-exp')
 log('baseline-EXP',['.venv/bin/python','med.py','run','--campaign','EXP','--quick','--metrics','S05,S21'],cwd=REPO/'evaluation')
elif action in ('dev-tests','dev-tail'):
 alone('picturas-dev')
 cases=[('B4-identity','b4-identity.py'),('B4-routes','b4-routes.py'),('B4-functional','b4-functional.py'),
   ('B5-mtls','mtls-pki/b5-mtls.py'),('B5-functional','mtls-pki/b5-functional.py'),('B8','websocket/b8-functional.py'),('B9','sessions/b9-functional.py'),
   ('B11-functional','operations/b11-functional.py'),('quota','users-quota.py'),('B6-adapter','upload/b6-adapter.py')]
 if action=='dev-tail':cases=cases[7:]
 for label,script in cases:
  log(label,['tests/conformance/in-network.sh','picturas-dev',script])
 log('smoke',['python3','tests/conformance/mtls-pki/b1-smoke.py'])
 log('F02',['evaluation/.venv/bin/python','tests/conformance/data-channels/b2-functional.py'])
 log('F01',['tests/conformance/run-f01.sh','picturas-dev'])
