"""Disposable OPS-C1 acceptance installation; no volume deletion or automatic replay."""
import datetime as dt,hashlib,json,os,signal,struct,subprocess,sys,time,uuid,zlib
from pathlib import Path
import requests
REPO=Path(__file__).resolve().parents[3]
ROOT=Path.home()/'picturas-secrets/b11-fixture'
PRIVATE=ROOT/'acceptance'
PROJECT='picturas-ops-b11'
ENV=dict(os.environ,PICTURAS_SECRETS_DIR=str(ROOT))
OUT=REPO/'tests/conformance/results/2026-11-24/B11-operations.json'
IMAGE='picturas-reconcile:1'

def durable(file,value):
 file.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 temp=file.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2));temp.chmod(0o600);os.replace(temp,file)
def command(args,*,timeout=600,input=None,allowed=False,env=ENV):
 result=subprocess.run(args,cwd=REPO,env=env,input=input,capture_output=True,timeout=timeout)
 if result.returncode and not allowed:raise RuntimeError('fixture_command_failed_'+Path(args[0]).name)
 return result
def compose():return ['docker','compose','-p',PROJECT,'-f',str(REPO/'docker-compose.yaml'),'-f',str(ROOT/'compose.json')]
def alone():
 result=command(['docker','ps','--filter','label=com.docker.compose.config-hash','--format','{{.Label "com.docker.compose.project"}}'])
 if any(v.startswith('picturas') and v!=PROJECT for v in result.stdout.decode().split()):raise RuntimeError('another_picturas_stack_running')
def cid(service):
 value=command([*compose(),'ps','-aq',service]).stdout.decode().strip()
 if not value or '\n' in value:raise RuntimeError('fixture_service_not_unique')
 return value
def helper(action,allowed=False):
 args=['docker','run','--rm','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
  '--user',str(os.getuid())+':'+str(os.getgid()),'--network',PROJECT+'_elk',
  '-v',str(REPO/'ops')+':/ops:ro','-v',str(REPO/'tests/conformance/operations')+':/tests:ro',
  '-v',str(PRIVATE)+':/case:rw','-v',PROJECT+'_image_data:/images:ro']
 for name in ('mongo_projects_admin','mongo_users_admin','rabbit_admin','s3_admin_access','s3_admin_secret'):
  args+=['-v',str(ROOT/'values'/name)+':/installation/values/'+name+':ro']
 for relative in ('pki/ca/ca.crt','pki/services/projects/service.crt','pki/services/projects/service.key'):
  args+=['-v',str(ROOT/relative)+':/installation/'+relative+':ro']
 result=command([*args,IMAGE,'python','/tests/b11-native-fixture.py',action],allowed=allowed)
 if action not in ('day-context','admitted') and result.returncode==0:print(result.stdout.decode().strip(),flush=True)
 return result
def check(label,condition=True):
 records=json.loads(OUT.read_text()) if OUT.exists() else {'project':PROJECT,'checks':[]}
 records['checks'].append({'case':label,'passed':bool(condition),'at':dt.datetime.now(dt.timezone.utc).isoformat()})
 durable(OUT,records)
 print(('PASS ' if condition else 'FAIL ')+label,flush=True)
 if not condition:raise RuntimeError('fixture_assertion_failed_'+label.replace('-','_'))
def state():return json.loads((PRIVATE/'fixture.json').read_text())
def api(method,path,token=None,**kw):
 headers=kw.pop('headers',{})
 if token:headers['Authorization']='Bearer '+token
 session=requests.Session();session.trust_env=False
 result=session.request(method,'https://localhost:8080/api-gateway/'+path,
  headers=headers,verify=str(ROOT/'pki/ca/ca.crt'),timeout=120,**kw)
 if result.status_code>=400:raise RuntimeError('fixture_http_'+str(result.status_code))
 return result
def account():
 email='ops-'+uuid.uuid4().hex+'@example.invalid';password=uuid.uuid4().hex
 result=api('POST','users/',json={'name':'OPS fixture','email':email,'password':password,'type':'free'}).json()
 token=api('POST',f'users/{email}/login',json={'password':password}).json()['jwt']
 return {'id':result['user']['_id'],'token':token}
def version(p,owner):return str(api('GET',f"projects/{owner['id']}/{p['id']}",owner['token']).json()['version'])
def mutate(method,p,suffix,owner,**kw):
 return api(method,f"projects/{owner['id']}/{p['id']}"+suffix,owner['token'],
  headers={'X-Project-Version':version(p,owner)},**kw)
def png(width=64,height=64):
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 data=(b'\0'+bytes((20,80,130))*width)*height
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b'')
def wait_results(p,owner,timeout=180):
 until=time.monotonic()+timeout
 while time.monotonic()<until:
  rows=api('GET',f"projects/{owner['id']}/{p['id']}/process/url",owner['token']).json()
  rows=rows if isinstance(rows,list) else rows.get('imgs',[])
  if rows:return rows
  time.sleep(.25)
 raise RuntimeError('fixture_result_timeout')
def reconcile(action,failpoint=None,allowed=False):
 env=dict(ENV)
 if failpoint:
  env['RECONCILE_FAILPOINT']=failpoint
  if ',' not in failpoint and failpoint!='quota_lost_response':env['RECONCILE_FAIL_MODE']='exit'
 result=command(['ops/reconcile',action,'--project',PROJECT],env=env,allowed=True,timeout=900)
 # The CLI itself exposes only opaque refs/counts. No native stderr is forwarded.
 if result.returncode==0:print(result.stdout.decode().strip(),flush=True)
 elif not allowed:
  try:code=json.loads(result.stderr)['error']
  except (ValueError,KeyError):code='unknown'
  raise RuntimeError('fixture_reconcile_failed_'+code)
 return result
def case_path():
 value=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
 return ROOT/'maintenance'/PROJECT/value['operation']/'reconciliation'

action=sys.argv[1]
if action=='case-diagnostics':
 import re
 case=case_path();codes=[];exceptions=[]
 for file in (case/'failures').glob('*.json'):
  record=json.loads(file.read_text())
  text=record.get('traceback','')+'\n'+record.get('stderr','')
  exceptions.extend(re.findall(r'\n([A-Za-z_.]+(?:Error|Exception)):',text))
  codes.extend(re.findall(r'RuntimeError: ([a-z0-9_]+)',text))
  try:codes.append(json.loads(record.get('stderr','{}')).get('error',''))
  except ValueError:pass
 print(json.dumps({'failure_codes':sorted(set(v for v in codes if v)),
  'exception_classes':sorted(set(exceptions)),'local_proof_exists':(case/'local-proof.json').exists()}))
elif action=='diagnostics':helper('diagnostics')
elif action=='up':
 alone();ROOT.mkdir(parents=True,exist_ok=True,mode=0o700);PRIVATE.mkdir(exist_ok=True,mode=0o700)
 prior=ROOT/'maintenance'/PROJECT/'state.json'
 if prior.exists():
  previous=json.loads(prior.read_text())
  if previous.get('t_isolado') and previous['phase'] not in ('reopened','cancelled'):
   raise RuntimeError('fixture_has_pending_isolated_operation_do_not_start_consumers')
 command(['ops/secrets.sh','init']);command(['ops/pki.sh','init']);command(['ops/pki.sh','check'])
 if not (ROOT/'compose.json').exists():
  config=json.loads(command(['docker','compose','-p','picturas-dev','config','--format','json'],
   env=dict(ENV,PICTURAS_SECRETS_DIR=str(Path.home()/'picturas-secrets'))).stdout)
  services={}
  for name,definition in config['services'].items():
   if definition.get('build'):
    image=json.loads(command(['docker','image','inspect','picturas-dev-'+name]).stdout)[0]['Id']
    services[name]={'image':image}
  # This backup mount is private to the fixture, never the shared development backup.
  (ROOT/'backups').mkdir(exist_ok=True,mode=0o700)
  services['mongo-backup']={'volumes':[str(ROOT/'backups')+':/backups']}
  durable(ROOT/'compose.json',{'services':services})
 command(['docker','build','-t',IMAGE,'-f','ops/reconcile.Dockerfile','ops'],timeout=600)
 command([*compose(),'up','-d','--no-build','--wait','--wait-timeout','300'],timeout=360)
 durable(PRIVATE/'case.json',{'operation':'0'*32})
 check('separate-normal-installation-healthy')
elif action=='prepare':
 alone()
 if (PRIVATE/'fixture.json').exists():
  existing=state()
  if existing['phase']!='preparing':raise RuntimeError('fixture_already_prepared_review_state')
  owners=existing['accounts'];projects=existing['projects']
 else:
  owners={k:account() for k in ('owner','editor','runner')};owner=owners['owner']
  labels=['confirmed','response-no-commit','previous-day','image-early-ack','video-after-reply','video-before-completion','unknown-debit']
  projects={label:{'id':api('POST','projects/'+owner['id'],owner['token'],json={'name':'B11 '+label}).json()['_id']} for label in labels}
  durable(PRIVATE/'fixture.json',{'accounts':owners,'projects':projects,'phase':'preparing'})
 owner=owners['owner']
 for seconds,size in [(1,'160x90'),(45,'1280x720')]:
  file=PRIVATE/f'video-{seconds}.mp4'
  if not file.exists():command(['ffmpeg','-v','error','-f','lavfi','-i',f'testsrc2=size={size}:rate=25',
    '-f','lavfi','-i','sine=frequency=440:sample_rate=44100','-t',str(seconds),'-c:v','libx264','-preset','ultrafast',
    '-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(file)],timeout=120)
 for label,p in projects.items():
  current=api('GET',f"projects/{owner['id']}/{p['id']}",owner['token']).json()
  if not current['imgs'] and label.startswith('video-'):
   file=PRIVATE/('video-1.mp4' if label=='video-after-reply' else 'video-45.mp4')
   with file.open('rb') as stream:mutate('POST',p,'/video',owner,files={'video':(file.name,stream,'video/mp4')})
  elif not current['imgs']:mutate('POST',p,'/img',owner,files={'image':('fixture.png',png(),'image/png')})
  if not current['tools'] and label in ('confirmed','image-early-ack'):
   mutate('POST',p,'/tool',owner,json={'procedure':'resize','params':{'width':32 if label=='confirmed' else 6000,'height':32 if label=='confirmed' else 6000}})
  elif not current['tools'] and label.startswith('video-'):
   for i in range(1 if label=='video-after-reply' else 4):mutate('POST',p,'/tool',owner,json={'procedure':'brightness','params':{'brightness':1.05}})
  if label in ('image-early-ack','video-after-reply','video-before-completion'):
   shares=api('GET',f"projects/{owner['id']}/{p['id']}/share",owner['token']).json()
   projects[label]['share']=next((s['id'] for s in shares if s['permission']=='edit' and not s.get('revoked')),None)
   if not projects[label]['share']:projects[label]['share']=mutate('POST',p,'/share',owner,json={'permission':'edit'}).json()['id']
 mutate('POST',projects['confirmed'],'/process',owner,json={});wait_results(projects['confirmed'],owner)
 durable(PRIVATE/'fixture.json',{'accounts':owners,'projects':projects,'phase':'prepared'})
 helper('seed')
 context=json.loads(helper('day-context').stdout)
 # Exercise the shipped ledger against real Mongo with only its local clock dependency
 # injected. The host clock, TLS validity and public HTTP API are unchanged.
 code='''const fs=require('fs'),mongoose=require('mongoose'),q=require('./admin/quotaLedger');
const c=JSON.parse(fs.readFileSync(0,'utf8'));
(async()=>{await mongoose.connect(process.env.MONGO_URI);await q.admit(c.id,c.amount,c.context,new Date(Date.now()-86400000));
await mongoose.disconnect();console.log('PASS original-day admission committed atomically');})().catch(()=>process.exit(1));'''
 result=command(['docker','exec','-i',cid('users'),'node','-e',code],input=json.dumps(context).encode())
 print(result.stdout.decode().strip(),flush=True)
 check('known-financial-fixtures-and-confirmed-output-prepared')
elif action=='reset-image-observer':
 # Preserve the completed observer attempt and its domain proof. Create a new
 # synthetic project, rather than replay an already-admitted run.
 data=state();owner=data['accounts']['owner']
 data['projects']['confirmed-observer-attempt']=data['projects']['image-early-ack']
 p={'id':api('POST','projects/'+owner['id'],owner['token'],json={'name':'B11 image early ack corrected observer'}).json()['_id']}
 mutate('POST',p,'/img',owner,files={'image':('fixture.png',png(),'image/png')})
 mutate('POST',p,'/tool',owner,json={'procedure':'resize','params':{'width':9000,'height':9000}})
 p['share']=mutate('POST',p,'/share',owner,json={'permission':'edit'}).json()['id']
 data['projects']['image-early-ack']=p;durable(PRIVATE/'fixture.json',data)
 check('previous-observer-attempt-preserved-new-image-fixture-created')
elif action=='interrupt':
 alone();data=state();owner=data['accounts']['owner'];runner=data['accounts']['runner'];projects=data['projects']
 # Queue both real video jobs while the single video worker is stopped, then stop
 # the projects Node process after HTTP admission. No mock replaces a tool.
 command(['docker','kill','--signal','STOP',cid('video_tool')])
 command(['docker','kill','--signal','STOP',cid('resize_tool')])
 admitted=json.loads(helper('admitted').stdout)
 for label in ('image-early-ack','video-after-reply','video-before-completion'):
  p=projects[label]
  # A failed observer does not authorize repeating admission or a tool job.
  # Existing runs stay exactly as they were; continue only the observation/cut.
  if admitted[label]:continue
  api('POST',f"projects/{owner['id']}/{p['id']}/process",runner['token'],params={'owner':owner['id'],'share':p['share']},
   headers={'X-Project-Version':version(p,owner)},json={})
 watch='''import glob,json,os,signal,time,sys
print('READY',flush=True)
for _ in range(20000):
 for file in glob.glob('/tmp/picturas-work-*.json'):
  try: state=json.load(open(file))
  except (ValueError,FileNotFoundError):continue
  if state.get('active_count',0)>0:
   print('ACTIVE',flush=True);sys.exit(0)
 time.sleep(.001)
sys.exit(1)
'''
 stopped=command(['docker','exec',cid('resize_tool'),'python','-c',
  "import glob,json;print(any(json.load(open(f)).get('active_count')==1 for f in glob.glob('/tmp/picturas-work-*.json')) and 'State:\\tT' in open('/proc/1/status').read())"]).stdout.strip()==b'True'
 if not stopped:
  watcher=subprocess.Popen(['docker','exec',cid('resize_tool'),'python','-u','-c',watch],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=ENV)
  if watcher.stdout.readline()!=b'READY\n':raise RuntimeError('image_observer_not_ready')
  command(['docker','kill','--signal','CONT',cid('resize_tool')])
  active=watcher.stdout.readline()==b'ACTIVE\n'
  if active:command(['docker','kill','--signal','STOP',cid('resize_tool')])
  watcher.communicate(timeout=30)
  stopped=active and watcher.returncode==0 and command(['docker','exec',cid('resize_tool'),'python','-c',
   "import glob,json;print(any(json.load(open(f)).get('active_count')==1 for f in glob.glob('/tmp/picturas-work-*.json')) and 'State:\\tT' in open('/proc/1/status').read())"]).stdout.strip()==b'True'
 check('real-image-autoack-worker-stopped-during-active-callback',stopped)
 stop='''const fs=require('fs');for(const pid of fs.readdirSync('/proc').filter(x=>/^\\d+$/.test(x))){try{
const a=fs.readFileSync('/proc/'+pid+'/cmdline','utf8').split('\\0');if(a[0]?.endsWith('node')&&a.slice(1).some(x=>/^(\\.\\/)?bin\\/www$/.test(x))){
process.kill(Number(pid),'SIGSTOP');console.log('STOPPED_PROJECTS');break;}}catch(_){}}'''
 result=command(['docker','exec',cid('projects'),'node','-e',stop]);check('real-project-consumer-stopped-after-admission',b'STOPPED_PROJECTS' in result.stdout)
 command(['docker','kill','--signal','CONT',cid('video_tool')])
 deadline=time.monotonic()+90
 while time.monotonic()<deadline:
  witness=helper('witness',allowed=True)
  if witness.returncode==0:break
  time.sleep(.1)
 else:raise RuntimeError('real_video_witness_timeout')
 command(['docker','kill','--signal','STOP',cid('video_tool')])
 helper('before')
 command(['ops/maintenance.sh','isolate','--project',PROJECT,'--mode','compromise','--compose-file',str(ROOT/'compose.json')],timeout=90)
 check('B10-cut-all-real-workers-before-administrative-effects')
elif action=='cut-after-reply':
 helper('before')
 command(['ops/maintenance.sh','isolate','--project',PROJECT,'--mode','compromise','--compose-file',str(ROOT/'compose.json')],timeout=90)
 check('B10-cut-after-real-video-replies-before-domain-commit')
elif action in ('exercise','exercise-finish','exercise-quarantine'):
 if action=='exercise':reconcile('inventory')
 case=case_path()
 snapshot_sha=hashlib.sha256((case/'snapshot.json').read_bytes()).hexdigest()
 operation=json.loads((case/'case.json').read_text())['operation']
 # Review basis is the known synthetic before-state and the immutable uploaded
 # fixtures; it is not a claim that certificate replacement proves data integrity.
 review={'operation':operation,'snapshot_sha256':snapshot_sha,'integrity_verified':True,
  'basis':'Known synthetic accounts/uploads and controlled preincident fixture states in acceptance/before.json; no external actors.'}
 durable(case/'integrity-review.json',review)
 if action=='exercise':
  for point in ('generation_after_commit','object_before_delete','object_after_delete','quota_before_commit','quota_after_commit'):
   result=reconcile('apply',point,True)
   check('crash-'+point+'-remains-isolated',result.returncode!=0)
  # A lost DB acknowledgement is handled by rereading the marker. No second write.
  reconcile('apply','quota_lost_response')
 if action!='exercise-quarantine':
  effects=json.loads((case/'effects.json').read_text())
  check('lost-quota-response-reads-atomic-marker',any(e.get('readback_after_lost_response') for e in effects))
 # The existing publisher uses non-persistent replies: a broker SIGKILL can lose
 # them despite durable queues. Inject one explicitly persistent, known obsolete
 # fixture reply to exercise archive-before-ack and redelivery across helper exit.
 backends=['projects_mongoDB','users_mongoDB','rabbitmq','seaweedfs']
 command([*compose(),'up','-d','--no-deps','--no-build','--wait','--wait-timeout','180',*backends],timeout=210)
 try:helper('persistent-reply')
 finally:command([*compose(),'stop','-t','10',*backends])
 check('crash-message-before-ack-remains-isolated',reconcile('apply','message_before_ack',True).returncode!=0)
 failures=[json.loads(f.read_text()) for f in (case/'failures').glob('*.json')]
 check('message-before-ack-helper-exited-at-target',any(f.get('failpoint')=='message_before_ack' and f.get('exit_code')==86 for f in failures))
 reconcile('apply')
 original=(case/'local-plan.json').read_bytes();plan=json.loads(original)
 if plan['runs']:
  # The expected directory manifest is changed deliberately: the mover must refuse
  # cleanup, while the admission gate and durable quota markers remain intact.
  first=plan['runs'][0];first['manifest']=[{'path':'not-a-real-output','size':1,'sha256':'0'*64}]
  durable(case/'local-plan.json',plan)
  check('cleanup-precondition-failure',reconcile('apply',allowed=True).returncode!=0)
  check('cleanup-failure-blocks-seal',reconcile('seal',allowed=True).returncode!=0)
  (case/'local-plan.json').write_bytes(original);(case/'local-plan.json').chmod(0o600)
 reconcile('apply')
 check('crash-before-seal-remains-isolated',reconcile('seal','before_seal',True).returncode!=0)
 reconcile('seal');check('business-case-sealed-without-technical-fixture-bypass')
 command(['ops/maintenance.sh','reopen','--project',PROJECT],timeout=600)
 check('B10-reopens-only-after-business-proof-and-channel-controls')
 helper('verify')
elif action in ('video-interrupt','video-finish'):
 if action=='video-finish':
  case=case_path()
  reconcile('apply')
  events=[json.loads(f.read_text()) for f in (case/'effect-events').glob('*.json')]
  check('native-existing-marker-readback-after-helper-exit',any(e.get('existing_marker_observed') for e in events))
  reconcile('seal');command(['ops/maintenance.sh','reopen','--project',PROJECT],timeout=600)
  helper('verify');check('real-video-interruption-before-completion-reconciled')
  raise SystemExit(0)
 data=state();owner=data['accounts']['owner'];runner=data['accounts']['runner'];p=data['projects']['video-before-completion']
 # This is a new, explicitly requested fixture Apply after successful recovery.
 # Old messages were quarantined; none are replayed to start this generation.
 api('POST',f"projects/{owner['id']}/{p['id']}/process",runner['token'],params={'owner':owner['id'],'share':p['share']},
  headers={'X-Project-Version':version(p,owner)},json={})
 watch="""import glob,json,sys,time,os
for _ in range(3000):
 active=any(json.load(open(f)).get('active_count')==1 for f in glob.glob('/tmp/picturas-work-*.json'))
 parts=glob.glob('/app/images/runs/*/out/*.part.mp4')
 if active and any(os.path.getsize(f)>0 for f in parts):print('ACTIVE_PARTIAL',flush=True);sys.exit(0)
 time.sleep(.005)
sys.exit(1)
"""
 observed=command(['docker','exec',cid('video_tool'),'python','-u','-c',watch],timeout=30)
 command(['docker','kill','--signal','STOP',cid('video_tool')])
 active=command(['docker','exec',cid('video_tool'),'python','-c',
  "import glob,json;print(any(json.load(open(f)).get('active_count')==1 for f in glob.glob('/tmp/picturas-work-*.json')) and 'State:\\tT' in open('/proc/1/status').read())"]).stdout.strip()==b'True'
 check('real-video-stopped-with-active-callback-and-partial-output',active and b'ACTIVE_PARTIAL' in observed.stdout)
 helper('seed-readback')
 helper('before');command(['ops/maintenance.sh','isolate','--project',PROJECT,'--mode','compromise'],timeout=90)
 reconcile('inventory');case=case_path();operation=json.loads((case/'case.json').read_text())['operation']
 durable(case/'integrity-review.json',{'operation':operation,'snapshot_sha256':hashlib.sha256((case/'snapshot.json').read_bytes()).hexdigest(),
  'integrity_verified':True,'basis':'New explicit real-video fixture, stopped with a partial output; private before-state retained.'})
 check('hard-exit-after-real-video-quota-commit',reconcile('apply','quota_after_commit',True).returncode!=0)
 failures=[json.loads(f.read_text()) for f in (case/'failures').glob('*.json')]
 check('quota-helper-exited-86-before-any-journal',any(f.get('failpoint')=='quota_after_commit' and f.get('exit_code')==86 for f in failures))
 reconcile('apply','quota_lost_response')
 events=[json.loads(f.read_text()) for f in (case/'effect-events').glob('*.json')]
 check('native-existing-marker-readback-after-helper-exit',any(e.get('existing_marker_observed') for e in events))
 reconcile('seal');command(['ops/maintenance.sh','reopen','--project',PROJECT],timeout=600)
 helper('verify');check('real-video-interruption-before-completion-reconciled')
elif action=='late':
 data=state();owner=data['accounts']['owner'];p=data['projects']['video-after-reply'];runner=data['accounts']['runner']
 api('POST',f"projects/{owner['id']}/{p['id']}/process",runner['token'],params={'owner':owner['id'],'share':p['share']},
  headers={'X-Project-Version':version(p,owner)},json={})
 helper('late');wait_results(p,owner);time.sleep(.5);helper('late-check')
 check('late-reply-does-not-affect-explicit-new-generation')
elif action=='unknown':
 helper('unknown')
 command(['ops/maintenance.sh','isolate','--project',PROJECT,'--mode','compromise'],timeout=90)
 reconcile('inventory');case=case_path();operation=json.loads((case/'case.json').read_text())['operation']
 durable(case/'integrity-review.json',{'operation':operation,'snapshot_sha256':hashlib.sha256((case/'snapshot.json').read_bytes()).hexdigest(),
  'integrity_verified':True,'basis':'Controlled missing receipt fixture; financial evidence intentionally absent.'})
 reconcile('apply');check('missing-receipt-blocks-seal',reconcile('seal',allowed=True).returncode!=0)
 check('missing-receipt-blocks-consumers',command(['ops/maintenance.sh','reopen','--project',PROJECT],allowed=True).returncode!=0)
 # Only the native backends run for this verification, still no consumers or ingress.
 command([*compose(),'up','-d','--no-deps','--no-build','--wait','--wait-timeout','180','projects_mongoDB','users_mongoDB','rabbitmq','seaweedfs'],timeout=210)
 try:helper('unknown-check')
 finally:command([*compose(),'stop','-t','10','projects_mongoDB','users_mongoDB','rabbitmq','seaweedfs'])
 check('indeterminate-case-kept-isolated-with-zero-financial-effect')
elif action=='down':
 command([*compose(),'down']);check('fixture-stopped-with-volumes-and-private-evidence-preserved')
else:raise RuntimeError('unsupported_fixture_action')
