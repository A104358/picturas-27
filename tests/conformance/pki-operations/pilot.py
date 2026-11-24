"""Host controller for the private technical pilot; all credentials stay outside Git.

Commands: init, begin <trial>, replace <trial>, resume <trial>. Each replacement
stops before interactive visual browser proof. No receipt is inferred or fabricated.
"""
import hashlib
import http.client
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import time
import urllib.request
import uuid

REPO=Path(__file__).resolve().parents[3]
from pilot_paths import ROOT,PROJECT,OVERRIDE
ENV=dict(os.environ,PICTURAS_SECRETS_DIR=str(ROOT))
COMPOSE=['docker','compose','-p',PROJECT,'-f',str(REPO/'docker-compose.yaml'),'-f',str(OVERRIDE)]
BASE=ROOT/'pilot';BASE.mkdir(exist_ok=True,mode=0o700)
SOURCE=ROOT/'source.mp4'

def run(args,timeout=600,allow=False):
 p=subprocess.run(args,cwd=REPO,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
 if p.returncode and not allow:raise RuntimeError('command_failed_'+Path(str(args[0])).name)
 return p

def write(path,value):path.write_text(json.dumps(value,indent=2));path.chmod(0o600)
def api(method,path,body=None,token=None):
 ctx=ssl.create_default_context(cafile=str(ROOT/'pki/ca/ca.crt'))
 headers={'Content-Type':'application/json'}
 if token:headers['Authorization']='Bearer '+token
 request=urllib.request.Request('https://localhost:8080/api-gateway/'+path,
  data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
 with urllib.request.urlopen(request,context=ctx,timeout=15) as response:return json.load(response)

def container(service):return run([*COMPOSE,'ps','-q',service]).stdout.decode().strip()
def helper(action,trial):
 p=run(['docker','run','--rm','--user',str(os.getuid())+':'+str(os.getgid()),'--network',PROJECT+'_elk','-v',str(ROOT)+':/installation:ro',
   '-v',str(trial)+':/proof:rw','-v',str(REPO/'tests/conformance/pki-operations')+':/tests:ro',
   'picturas-pki-observer','python','/tests/technical_job.py',action],timeout=30)
 result=json.loads(p.stdout)
 if result.get('fixture_failed'):raise RuntimeError('technical_fixture_failed')
 return result

def wait_file(path,seconds=20):
 deadline=time.monotonic()+seconds
 while not path.exists() and time.monotonic()<deadline:time.sleep(.1)
 if not path.exists():raise RuntimeError('observation_not_available_'+path.name)
 return json.loads(path.read_text())

def main():
 action=sys.argv[1];trial=BASE/('trial-'+sys.argv[2]) if len(sys.argv)>2 else None
 if action=='archive-initial':
  if not (trial/'completed.json').exists():raise RuntimeError('initial_trial_not_completed')
  trial.rename(BASE/('initial-trial-'+sys.argv[2]))
  old=REPO/'tests/conformance/results/2026-11-24'/('B10-trial-'+sys.argv[2]+'.json')
  old.rename(old.with_name('B10-initial-trial-'+sys.argv[2]+'.json'))
  print('PASS initial trial retained; next cycle will include principal/effect snapshots');return
 if action=='archive-diagnostic':
  state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
  if state['phase']!='reopened' or not (trial/'completed.json').exists():raise RuntimeError('diagnostic_not_completed')
  target=BASE/'diagnostic-control-retry'
  if target.exists():raise RuntimeError('diagnostic_already_retained')
  trial.rename(target)
  print('PASS completed diagnostic/retry retained outside the three comparable trials');return
 if action=='archive-preparation':
  state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
  if state['phase']!='reopened' or (trial/'ready.json').exists() or (trial/'job-active.json').exists():
   raise RuntimeError('only_unstarted_preparation_can_be_archived')
  run(['docker','rm','picturas-pki-observer-'+sys.argv[2]])
  target=trial.with_name(trial.name+'-preparation-'+str(time.time_ns()))
  trial.rename(target)
  print('PASS preparation failure retained; no incident clock had started');return
 if action=='init':
  if (BASE/'identity.json').exists():raise RuntimeError('pilot_already_initialized_do_not_repeat_registration')
  run([*COMPOSE,'up','-d','--wait','--wait-timeout','300'])
  if not SOURCE.exists():
   run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=duration=90:size=1280x720:rate=30',
       '-c:v','libx264','-preset','ultrafast','-crf','28','-an',str(SOURCE)],timeout=180)
  user=api('POST','users/',{'type':'anonymous'})
  project=api('POST','projects/'+user['user']['_id'],{'name':'B10 technical observer'},user['jwt'])
  write(BASE/'identity.json',{'user':user['user']['_id'],'project':project['_id'],'token':user['jwt']})
  print('PASS pilot initialized; fresh fixture installation, no retained dataset used');return
 if action=='begin':
  if trial.exists():raise RuntimeError('trial_already_exists_preserve_original_clock')
  trial.mkdir(mode=0o700)
  identity=json.loads((BASE/'identity.json').read_text());mid=str(uuid.uuid4())
  directory='/app/images/pki-fixture/'+mid
  data={**identity,'message_id':mid,'input':directory+'/input.mp4','output':directory+'/output.mp4','brightness_steps':4}
  write(trial/'fixture.json',data)
  name='picturas-pki-observer-'+sys.argv[2]
  config=json.loads(run([*COMPOSE,'config','--format','json']).stdout)
  volume=config['volumes']['image_data']['name']
  run(['docker','run','-d','--user',str(os.getuid())+':'+str(os.getgid()),'--name',name,'--network',PROJECT+'_elk',
    '-v',volume+':/images:ro','-v',str(ROOT)+':/installation:ro',
    '-v',str(trial)+':/proof:rw','-v',str(REPO/'tests/conformance/pki-operations')+':/tests:ro',
    'picturas-pki-observer','python','/tests/persistent_observer.py'])
  ready=wait_file(trial/'ready.json');assert ready['prepared']
  video=container('video_tool');run(['docker','exec',video,'mkdir','-p',directory])
  run(['docker','cp',str(SOURCE),video+':'+data['input']])
  helper('publish',trial)
  deadline=time.monotonic()+15
  while time.monotonic()<deadline:
   active=run(['docker','exec',video,'sh','-c','cat /tmp/picturas-work-*.json'],allow=True)
   partial=run(['docker','exec',video,'test','-s',data['output']+'.part.mp4'],allow=True)
   if b'"active_count": 1' in active.stdout and partial.returncode==0:break
   time.sleep(.1)
  else:raise RuntimeError('real_video_job_not_observed')
  broker=container('rabbitmq')
  def broker_snapshot():
   channels=json.loads(run(['docker','exec',broker,'rabbitmqctl','--quiet','--formatter=json','list_channels','user','consumer_count']).stdout)
   connections=json.loads(run(['docker','exec',broker,'rabbitmqctl','--quiet','--formatter=json','list_connections','user','channels','state']).stdout)
   queues=json.loads(run(['docker','exec',broker,'rabbitmqctl','--quiet','--formatter=json','list_queues','name','messages_ready','messages_unacknowledged','consumers']).stdout)
   users=sorted({row['user'] for row in channels+connections})
   return {'at_ns':time.time_ns(),'queues':queues,'principals':{user:{'consumers':sum(r['consumer_count'] for r in channels if r['user']==user),
           'connections':sum(r['user']==user for r in connections)} for user in users}}
  before=broker_snapshot()
  if not any(q['name']=='video_queue' and q['messages_unacknowledged']>0 for q in before['queues']):raise RuntimeError('video_delivery_not_in_flight')
  expected=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())['registered_consumers']
  if not all(before['principals'].get(u,{}).get('consumers',0)>0 for u in expected):raise RuntimeError('required_principal_not_observed_before_incident')
  write(trial/'broker-before.json',before)
  active=run(['docker','exec',video,'sh','-c','cat /tmp/picturas-work-*.json'],allow=True)
  if b'"active_count": 1' not in active.stdout:raise RuntimeError('job_finished_before_incident_do_not_claim_live_load')
  write(trial/'job-active.json',{'at_ns':time.time_ns(),'active_marker':True,'partial_output_observed':True,'brightness_steps':4,'message_id':mid})
  detection=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
  start=time.time_ns()
  result=run(['ops/maintenance.sh','isolate','--project',PROJECT,'--mode','compromise',
    '--detected-at',detection,'--compose-file',str(OVERRIDE),'--cut-proof',str(trial/'cut.json')])
  (trial/'cut-complete').touch()
  cut=wait_file(trial/'cut.json',10)
  state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
  if not cut['all_persistent_cut']:raise RuntimeError('persistent_cut_incomplete')
  if not cut['rows'].get('video-progress',{}).get('successes'):raise RuntimeError('correlated_video_events_not_observed')
  last=max([r['first_cut_ns'] for k,r in cut['rows'].items() if k!='video-progress' and r.get('first_cut_ns')]+[cut['local_effects']['samples'][-1]['at_ns']])
  before=json.loads((trial/'broker-before.json').read_text())
  write(trial/'broker-isolated.json',{'at_ns':time.time_ns(),'broker_pid_zero':all(not p['running'] and p['pid']==0 for p in state['participants_isolated']),
     'new_connections_refused':True,'principals':{u:{'connections':0,'consumers':0} for u in before['principals']}})
  write(trial/'isolation.json',{'operation':state['operation'],'command_wall_ns':start,
      'controller':json.loads(result.stdout),'independent_last_cut_ns':last,
      'independent_cut_ms':(last-start)/1e6,'persistent_cut':True,'job_observed':True})
  print('PASS trial '+sys.argv[2]+': live video job and all seven persistent connection types cut');return
 if action=='replace':
  data=json.loads((trial/'fixture.json').read_text())
  run(['ops/pki.sh','retire','--project',PROJECT,'--mode','compromise','--compose-file',str(OVERRIDE)])
  # Start only native backends for fixture quarantine; no application/worker may run.
  backends=['rabbitmq','projects_mongoDB','users_mongoDB','subscriptions_mongoDB','seaweedfs']
  run([*COMPOSE,'up','-d','--no-deps','--force-recreate','--wait','--wait-timeout','180',*backends])
  helper('quarantine',trial)
  state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text());operation=state['operation']
  config=json.loads(run([*COMPOSE,'config','--format','json']).stdout)
  volume=config['volumes']['image_data']['name']
  video_image=next(p['image'] for p in state['participants_before'] if p['service']=='video_tool')
  code='from pathlib import Path; import sys; source=Path(sys.argv[1]); target=Path(sys.argv[2]); target.parent.mkdir(parents=True,exist_ok=True); source.rename(target)'
  source='/images/pki-fixture/'+data['message_id'];target='/images/pki-quarantine/'+operation
  run(['docker','run','--rm','--network','none','-v',volume+':/images','--entrypoint','python',
       video_image,'-c',code,source,target])
  proof=json.loads((trial/'quarantine.json').read_text());proof['fixture_outputs_quarantined']=True
  write(trial/'quarantine.json',proof)
  # Before verification the backends are stopped again, preserving isolation.
  ids=run([*COMPOSE,'ps','-q']).stdout.decode().split()
  if ids:run(['docker','update','--restart=no',*ids]);run(['docker','kill',*ids],allow=True)
  print('PASS trial '+sys.argv[2]+': new CA/all keys prepared; only owned fixture quarantined; awaiting manual browser proof');return
 if action=='resume':
  proof=trial/'browser-proof.json'
  if not proof.exists():raise RuntimeError('manual_browser_proof_required')
  run(['ops/maintenance.sh','reopen','--project',PROJECT,'--mode','compromise',
    '--fixture-proof',str(trial/'quarantine.json'),'--browser-proof',str(proof),'--persistent-proof',str(trial/'resumption.json')],timeout=600)
  (trial/'reopen-ready').touch()
  resumed=wait_file(trial/'resumption.json',30)
  if not resumed['all_refused']:raise RuntimeError('old_tls_session_not_refused')
  name='picturas-pki-observer-'+sys.argv[2]
  run(['docker','wait',name],timeout=15);run(['docker','rm',name])
  state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
  broker=container('rabbitmq')
  channels=json.loads(run(['docker','exec',broker,'rabbitmqctl','--quiet','--formatter=json','list_channels','user','consumer_count']).stdout)
  connections=json.loads(run(['docker','exec',broker,'rabbitmqctl','--quiet','--formatter=json','list_connections','user','channels','state']).stdout)
  users=sorted({row['user'] for row in channels+connections})
  write(trial/'broker-reopened.json',{'at_ns':time.time_ns(),'principals':{u:{'consumers':sum(r['consumer_count'] for r in channels if r['user']==u),
     'connections':sum(r['user']==u for r in connections)} for u in users}})
  write(trial/'completed.json',{'operation':state['operation'],'completed':True,'t_reabertura':state['t_reabertura'],
      'isolation_ms':state['isolation_ms'],'isolation_target_met':state['isolation_target_met'],
      'old_session_refused':True})
  print('PASS trial '+sys.argv[2]+': complete manifest, controls and stale-session refusal; reopened');return
 raise RuntimeError('invalid_pilot_action')

try:main()
except Exception as error:
 print('FAIL pilot: '+(str(error) if isinstance(error,RuntimeError) else type(error).__name__))
 raise SystemExit(1)
