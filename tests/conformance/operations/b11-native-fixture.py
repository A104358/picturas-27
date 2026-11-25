"""Controlled native fixtures; private IDs/state, public assertions only.

This helper is never shipped as an application endpoint. It requires the test
installation's administrative credentials and is called only by b11-fixture.py.
"""
import copy,hashlib,json,os,sys,time,uuid
from pathlib import Path
sys.path.insert(0,'/ops')
from reconcile import Native
from maintenance import durable,fail
from bson import ObjectId,json_util

native=Native()
directory=Path('/case')
state=json.loads((directory/'fixture.json').read_text())

def save(name,value):native.save(name,value)
def read(name):return native.read(name)
def project(label):return native.projects.projects.find_one({'_id':ObjectId(state['projects'][label]['id'])})
def bind(run):
 return {'x-processing-run':run['_id'],'x-processing-project':str(run['project_id']),
  'x-processing-owner':str(run['user_id']),'x-processing-generation':str(run['token']),
  'x-processing-images':str(run['cost']['image']),'x-processing-videos':str(run['cost']['video'])}

def admission(run):
 import requests
 cert=native.installation/'pki/services/projects'
 response=requests.get(f"https://users:10001/{run['runner_id']}/process/{sum(run['cost'].values())}",
  headers=bind(run),cert=(str(cert/'service.crt'),str(cert/'service.key')),verify=native.ca,timeout=10)
 if response.status_code!=200:fail('fixture_admission_failed')
 return response.json()

def seed(label,image_cost=0,video_cost=0,artifact=False,missing_receipt=False):
 p=project(label);owner=p['user_id'];runner=ObjectId(state['accounts']['editor']['id'])
 token=p.get('activeToken',0)+1;run_id=str(uuid.uuid4());img=p['imgs'][0]
 msg_id='request-'+str(uuid.uuid4())
 run={'_id':run_id,'schema_version':1,'user_id':owner,'runner_id':runner,'project_id':p['_id'],
  'token':token,'phase':'running','debit_state':'unknown' if missing_receipt else 'confirmed',
  'cost':{'image':image_cost,'video':video_cost},'jobs':[{'img_id':str(img['_id']),'msg_id':msg_id,'media_type':'image'}],
  'message_ids':[msg_id],'tools':[],'sources':[{'img_id':str(img['_id']),'key':img['og_img_key'],'sha256':img['og_sha256']}],
  'invalidated':False}
 native.projects.processing_runs.insert_one(run)
 native.projects.projects.update_one({'_id':p['_id']},{'$set':{'activeToken':token,'processingRunId':run_id,'pendingAdvancedOps':image_cost+video_cost}})
 receipt=None if missing_receipt else admission(run)
 native.projects.processes.insert_one({'user_id':owner,'runner_id':str(runner),'project_id':p['_id'],'img_id':img['_id'],
  'msg_id':msg_id,'cur_pos':0,'token':token,'run_id':run_id,'replyClaimed':True,'og_img_uri':'unused','new_img_uri':'unused'})
 if artifact:
  rid=ObjectId();name=f'run-{run_id}-{rid}.png';key=f'users/{owner}/projects/{p["_id"]}/out/{name}'
  data=b'B11 partial, uncommitted output';sha=hashlib.sha256(data).hexdigest()
  native.projects.processing_artifacts.insert_one({'run_id':run_id,'artifact_id':str(rid),'img_id':img['_id'],
   'key':key,'img_key':name,'sha256':sha,'size':len(data),'type':'image','file_name':'partial.png'})
  native.s3.put_object(Bucket='picturas',Key=key,Body=data)
  # Result exists but project pointer never committed: its presence cannot prove success.
  native.projects.results.insert_one({'_id':rid,'user_id':owner,'project_id':p['_id'],'img_id':img['_id'],
   'token':token,'run_id':run_id,'img_key':name,'file_name':'partial.png','type':'image','sha256':sha,'size':len(data)})
 return run,receipt

action=sys.argv[1]
if action=='diagnostics':
 result={}
 for label in ('video-after-reply','video-before-completion'):
  p=project(label);run=native.projects.processing_runs.find_one({'project_id':p['_id']})
  out=Path('/images/runs')/run['_id']/'out'
  result[label]={'run_phase':run['phase'],'partial_files':len(list(out.rglob('*.part.mp4'))),
    'output_bytes':sum(f.stat().st_size for f in out.rglob('*') if f.is_file())}
 for q in ('video_queue','project_queue'):result[q]=native.channel.queue_declare(queue=q,passive=True).method.message_count
 print(json.dumps(result))
elif action=='persistent-reply':
 import pika
 run=read('controlled.json')['reply']
 msg={'messageId':'controlled-persistent-'+str(uuid.uuid4()),'correlationId':run['message_ids'][0],
  'status':'success','output':{'type':'image','imageURI':'/app/images/runs/'+run['_id']+'/out/old.png'}}
 native.channel.confirm_delivery()
 native.channel.basic_publish(exchange='picturas',routing_key='project_queue',body=json.dumps(msg).encode(),
  properties=pika.BasicProperties(delivery_mode=2),mandatory=True)
 save('persistent-reply-fixture.json',{'run_id':run['_id'],'message':msg,'delivery_mode':2})
 print('PASS controlled persistent obsolete reply published while all consumers remain stopped')
elif action=='admitted':
 print(json.dumps({label:native.projects.processing_runs.count_documents({'project_id':project(label)['_id']})>0
  for label in ('image-early-ack','video-after-reply','video-before-completion')}))
elif action=='seed-readback':
 seed('previous-day',1,0)
 print('PASS new controlled debit prepared for lost-response readback after hard exit')
elif action=='seed':
 run,receipt=seed('response-no-commit',2,3,True)
 # A later real users-function admission uses an injected previous-day clock.
 yesterday,unused=seed('previous-day',1,2,False,True)
 yesterday['debit_state']='requested'
 native.projects.processing_runs.update_one({'_id':yesterday['_id']},{'$set':{'debit_state':'requested'}})
 save('controlled.json',{'reply':run,'yesterday':yesterday})
 print('PASS controlled reply without commit and mixed-cost original executor fixture prepared')
elif action=='day-context':
 run=read('controlled.json')['yesterday']
 # Returned only to the host's private capture; never forwarded to public logs.
 print(json.dumps({'id':str(run['runner_id']),'amount':sum(run['cost'].values()),'context':{
  'run_id':run['_id'],'project_id':str(run['project_id']),'owner_id':str(run['user_id']),
  'executor_id':str(run['runner_id']),'generation':run['token'],'image_cost':1,'video_cost':2}}))
elif action=='before':
 # Snapshot before the administrative tool makes any correction. No body/JWT is public.
 if (directory/'before.json').exists():save('before-history/'+uuid.uuid4().hex+'.json',read('before.json'))
 values={};protected={}
 for label in state['projects']:
  p=project(label);runs=list(native.projects.processing_runs.find({'project_id':p['_id']}))
  values[label]={'project':p,'runs':runs,'results':list(native.projects.results.find({'project_id':p['_id']}))}
  prefix=f"users/{p['user_id']}/projects/{p['_id']}/"
  for img in p.get('imgs',[]):
   key=prefix+'src/'+img['og_img_key'];protected[key]=native.object(key)
  for result in values[label]['results']:
   if result.get('token',0)==p.get('committedToken',0):
    key=prefix+'out/'+result['img_key'];protected[key]=native.object(key)
 save('before.json',{'projects':values,'protected':protected,'accounts':list(native.users.users.find({}, {'operations':1,'quotaLedger':1,'quotaRevision':1,'type':1}))})
 print('PASS private before-state captured')
elif action=='witness':
 p=project('video-before-completion');run=native.projects.processing_runs.find_one({'project_id':p['_id']})
 reply=project('video-after-reply');replyrun=native.projects.processing_runs.find_one({'project_id':reply['_id']})
 # Read queue count only. It cannot acknowledge, requeue or execute an application job.
 count=native.channel.queue_declare(queue='project_queue',passive=True).method.message_count
 video_run=Path('/images/runs')/run['_id']/'out'
 partial=sum(f.stat().st_size for f in video_run.rglob('*.part.mp4') if f.is_file())
 records=native.projects.results.count_documents({'project_id':reply['_id']})
 if count<1 or partial<1 or records:fail('real_video_witness_not_ready')
 save('worker-witness.json',{'reply_run':replyrun['_id'],'interrupted_run':run['_id'],'ready_replies':count,'partial_bytes':partial,
  'results_before_commit':records})
 print('PASS real video reply queued without domain commit; second video has partial output')
elif action=='verify':
 before=read('before.json');checks=[];after_total=0
 for key,expected in before.get('protected',{}).items():
  if native.object(key)!=expected:fail('fixture_original_or_confirmed_bytes_changed')
 for label,value in before['projects'].items():
  p=project(label);rows=list(native.projects.results.find({'project_id':p['_id']}))
  if label.startswith('confirmed'):
   if p['committedRun']!=value['project']['committedRun']:fail('fixture_confirmed_pointer_changed')
   if [r['_id'] for r in rows]!=[r['_id'] for r in value['results']]:fail('fixture_confirmed_results_changed')
  else:
   for run in value['runs']:
    if p['activeToken']<=run['token']:fail('fixture_old_generation_live')
    if p.get('committedToken',0)==run['token']:fail('fixture_partial_visible')
   if p.get('processingRunId') or p.get('reconciliationHold'):fail('fixture_unresolved_hold')
  checks.append(label)
 for account in native.users.users.find({}, {'operations':1,'quotaLedger':1,'type':1}):
  after_total+=sum(o['processed'] for o in account.get('operations',[]))
  original=next(a for a in before['accounts'] if a['_id']==account['_id'])
  day=lambda value:value.strftime('%Y-%m-%d')
  expected={day(o['day']):o['processed'] for o in original.get('operations',[])}
  for receipt in original.get('quotaLedger',[]):
   run=native.projects.processing_runs.find_one({'_id':receipt['run_id']})
   p=native.projects.projects.find_one({'_id':run['project_id']})
   if (p.get('committedRun') or {}).get('run_id')!=run['_id'] and not receipt.get('compensation') and receipt['charged']:
    expected[receipt['day']]-=receipt['charged']
  if expected!={day(o['day']):o['processed'] for o in account.get('operations',[])}:fail('fixture_wrong_original_day_balance')
  for receipt in account.get('quotaLedger',[]):
   run=native.projects.processing_runs.find_one({'_id':receipt['run_id']})
   p=native.projects.projects.find_one({'_id':run['project_id']})
   confirmed=(p.get('committedRun') or {}).get('run_id')==run['_id']
   if confirmed:
    if receipt.get('compensation'):fail('fixture_confirmed_debit_refunded')
   elif not receipt.get('compensation') or receipt['compensation']['amount']!=receipt['charged']:fail('fixture_missing_exact_compensation')
  # The owner's account was never the executor. No fabricated transfer/credit.
  if str(account['_id'])==state['accounts']['owner']['id'] and account.get('operations',[])!=original.get('operations',[]):fail('fixture_wrong_owner_credited')
 if (directory/'verified.json').exists():save('verified-history/'+uuid.uuid4().hex+'.json',read('verified.json'))
 save('verified.json',{'projects_checked':checks,'no_undue_charges':True,'no_undue_compensations':True,
  'balance_before':sum(o['processed'] for a in before['accounts'] for o in a.get('operations',[])),
  'balance_after':after_total,'original_day_balances_verified':True,'no_partial_visibility':True,'confirmed_preserved':True})
 print('PASS native quota markers, actual executor/day, old generations, visibility and confirmed result')
elif action=='late':
 before=read('before.json');run=before['projects']['video-after-reply']['runs'][0]
 process=native.projects.processes.find_one({'run_id':run['_id']})
 if not process or not process.get('reconciled'):fail('fixture_obsolete_process_not_fenced')
 body={'messageId':'late-'+str(uuid.uuid4()),'correlationId':process['msg_id'],'status':'success',
  'output':{'type':'video','imageURI':str(Path('/app/images/runs')/run['_id']/'out/late.mp4')}}
 native.channel.basic_publish(exchange='picturas',routing_key='project_queue',body=json.dumps(body).encode())
 print('PASS explicit obsolete reply injected for the late-message negative control')
elif action=='late-check':
 before=read('before.json');run=before['projects']['video-after-reply']['runs'][0]
 if native.projects.results.count_documents({'run_id':run['_id']}):fail('fixture_obsolete_result_promoted')
 p=project('video-after-reply')
 if p.get('committedRun',{}).get('run_id')==run['_id']:fail('fixture_obsolete_commit')
 if not p.get('committedRun') or p['activeToken']<=run['token']:fail('fixture_new_generation_missing')
 print('PASS obsolete reply produced no Result or commit after an explicit new Apply')
elif action=='unknown':
 run,_=seed('unknown-debit',1,0,False,True)
 save('unknown-before.json',{'run':run,'account':native.users.users.find_one({'_id':run['runner_id']},{'operations':1,'quotaLedger':1})})
 print('PASS missing-debit-evidence fixture prepared')
elif action=='unknown-check':
 before=read('unknown-before.json');run=before['run']
 current=native.users.users.find_one({'_id':run['runner_id']},{'operations':1,'quotaLedger':1})
 if current!=before['account']:fail('fixture_unknown_debit_changed')
 p=project('unknown-debit')
 if not p.get('reconciliationHold') or p['activeToken']<=run['token']:fail('fixture_unknown_case_not_fenced')
 print('PASS unknown debit has no invented refund and remains fenced/isolated')
else:fail('unknown_fixture_action')
