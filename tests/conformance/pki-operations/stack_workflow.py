"""Scoped B10 stack/regression workflow; no volume deletion or instrument edits."""
import json,os,re,subprocess,sys,time
from pathlib import Path
from pilot_paths import ROOT,PROJECT,OVERRIDE,CACHE
REPO=Path(__file__).resolve().parents[3]
PRIMARY=Path.home()/'picturas-secrets'
ENV=dict(os.environ,PICTURAS_SECRETS_DIR=str(PRIMARY),MED_WS_JOIN_FORMAT='v2')
OUT=REPO/'tests/conformance/results/2026-11-24'
def run(args,env=ENV,cwd=REPO,timeout=1200):
 return subprocess.run(args,cwd=cwd,env=env,capture_output=True,timeout=timeout)
def must(args,**kw):
 result=run(args,**kw)
 if result.returncode:raise RuntimeError('workflow_command_failed_'+Path(args[0]).name)
 return result
def compose(project):return ['docker','compose','-p',project,'-f',str(REPO/'docker-compose.yaml')]
def alone(project):
 # Standalone F01/guard containers inherit image build labels, but are not stacks.
 names=must(['docker','ps','--filter','label=com.docker.compose.config-hash',
             '--format','{{.Label "com.docker.compose.project"}}']).stdout.decode().split()
 if any(n.startswith('picturas') and n!=project for n in names):raise RuntimeError('another_application_stack_is_running')
def checked_material():
 for command in [['ops/secrets.sh','render'],['ops/secrets.sh','check'],['ops/pki.sh','check']]:must(command)
 if (PRIMARY/'maintenance-gate/admissions-closed').exists():raise RuntimeError('primary_admissions_already_closed')
 print('PASS primary secrets render/check and PKI check; no values displayed',flush=True)
def tag(project):
 config=json.loads(must([*compose(project),'config','--format','json']).stdout)
 manifest=json.loads((OUT/'B10-runtime-manifest.json').read_text())
 images={r['service']:r['image_id'] for r in manifest['services']}
 for service,definition in config['services'].items():
  if definition.get('build'):must(['docker','image','tag',images[service],project+'-'+service])
 print('PASS reused the exact verified B10 image IDs for '+project,flush=True)
def safe_log(data):
 text=data.decode(errors='replace')
 for root in [PRIMARY,ROOT]:
  for file in (root/'values').iterdir():
   if file.is_file():
    value=file.read_text().strip()
    if len(value)>=6:text=text.replace(value,'[REDACTED]')
 text=re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+','[REDACTED-JWT]',text)
 return re.sub(r'https://[^\s"\']*X-Amz-[^\s"\']*','[REDACTED-SIGNED-URL]',text)
def test(label,args,**kw):
 result=run(args,**kw)
 (OUT/('B10-'+label+'.txt')).write_text(safe_log(result.stdout+result.stderr))
 print(('PASS ' if result.returncode==0 else 'FAIL ')+label,flush=True)
 if result.returncode:raise RuntimeError('regression_failed_'+label)
action=sys.argv[1]
if action=='pilot-up':
 alone(PROJECT)
 must([*compose(PROJECT),'-f',str(OVERRIDE),'up','-d','--no-build','--wait','--wait-timeout','240'],env=dict(ENV,PICTURAS_SECRETS_DIR=str(ROOT)))
 expected=set(json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())['registered_consumers'])
 broker=must(['docker','ps','-q','--filter','label=com.docker.compose.project='+PROJECT,
              '--filter','label=com.docker.compose.service=rabbitmq']).stdout.decode().strip()
 deadline=time.monotonic()+90
 while True:
  channels=json.loads(must(['docker','exec',broker,'rabbitmqctl','--quiet','--formatter=json','list_channels','user','consumer_count']).stdout)
  present={r['user'] for r in channels if r['consumer_count']>0}
  if expected<=present:break
  if time.monotonic()>deadline:raise RuntimeError('required_pilot_consumers_not_ready')
  time.sleep(2)
 print('PASS pilot up; retained dataset, current CA, no volume deletion')
elif action=='pilot-down':
 must([*compose(PROJECT),'-f',str(OVERRIDE),'down'],env=dict(ENV,PICTURAS_SECRETS_DIR=str(ROOT)))
 print('PASS pilot down without -v; all volumes preserved')
elif action in ('dev-up','exp-up'):
 project='picturas-dev' if action=='dev-up' else 'picturas-nfr-exp'
 alone(project);checked_material();tag(project)
 if action=='dev-up':must([*compose(project),'up','-d','--no-build','--wait','--wait-timeout','240'])
 else:
  script='''from medlib import dockerctl
from medlib.config import SETTINGS
assert SETTINGS.project=='picturas-nfr-exp'
dockerctl.guard_owned()
dockerctl.write_override()
dockerctl.compose('up','-d','--no-build','--wait','--wait-timeout','240',timeout=600)
dockerctl.start_probe()
print('PASS EXP up; retained volumes, frozen override generation, probe ready')'''
  must(['.venv/bin/python','-c',script],cwd=REPO/'evaluation')
 print('PASS '+project+' healthy',flush=True)
elif action=='dev-tests':
 alone('picturas-dev')
 test('b4-route-matrix-dev',['python3','tests/conformance/b4-route-matrix.py'])
 for label,script in [('b4-identity','b4-identity.py'),('b4-routes','b4-routes.py'),('b4-functional','b4-functional.py'),
  ('b5-mtls','mtls-pki/b5-mtls.py'),('b5-functional','mtls-pki/b5-functional.py'),
  ('b8-functional','websocket/b8-functional.py'),('b9-functional','sessions/b9-functional.py')]:
  test(label+'-dev',['tests/conformance/in-network.sh','picturas-dev',script])
 test('smoke-dev',['python3','tests/conformance/mtls-pki/b1-smoke.py'])
 test('F02-dev',['evaluation/.venv/bin/python','tests/conformance/data-channels/b2-functional.py'])
elif action=='dev-independent-tests':
 test('F01-dev',['tests/conformance/run-f01.sh','picturas-dev'])
 test('b5-guard-dev',['tests/conformance/mtls-pki/b5-guard.sh','picturas-dev'])
elif action=='exp-run':
 alone('picturas-nfr-exp')
 test('EXP-run',['.venv/bin/python','med.py','run','--campaign','EXP','--quick',
    '--metrics','S01,S02,S03,S04,S05,S12,S16,S17,S18,S21'],cwd=REPO/'evaluation',timeout=1800)
elif action in ('dev-down','exp-down'):
 project='picturas-dev' if action=='dev-down' else 'picturas-nfr-exp'
 if action=='exp-down':must(['.venv/bin/python','-c','from medlib import dockerctl;dockerctl.stop_probe()'],cwd=REPO/'evaluation')
 must([*compose(project),'down'])
 print('PASS '+project+' down without -v; volumes preserved')
else:raise RuntimeError('unsupported_workflow_action')
