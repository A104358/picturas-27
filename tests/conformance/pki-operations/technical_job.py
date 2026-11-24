"""D-33 fixture protocol. Runs on the private pilot network, never on a normal dataset."""
import hashlib,json,os,sys
from pathlib import Path
import pika
import pymongo
import ssl

ROOT=Path('/installation');PROOF=Path('/proof');fixture=json.loads((PROOF/'fixture.json').read_text())
assert json.loads((ROOT/'fixture-installation.json').read_text())['technical_fixture'] is True

def secret(name):return (ROOT/'values'/name).read_text().strip()
def broker(admin=False):
 ctx=ssl.create_default_context(cafile=str(ROOT/'pki/ca/ca.crt'))
 user='picturas_admin' if admin else 'projects';password=secret('rabbit_admin' if admin else 'rabbit_projects')
 return pika.BlockingConnection(pika.ConnectionParameters('rabbitmq',5671,credentials=pika.PlainCredentials(user,password),
  ssl_options=pika.SSLOptions(ctx,'rabbitmq'),socket_timeout=3,connection_attempts=1))

def domain_state():
 result={}
 for label,port,db in [('users',27019,'user'),('projects',27018,'project')]:
  c=pymongo.MongoClient(label+'_mongoDB',port,username='picturas_admin',password=secret('mongo_'+label+'_admin'),
   authSource='admin',tls=True,tlsCAFile=str(ROOT/'pki/ca/ca.crt'),serverSelectionTimeoutMS=3000)
  try:
   if label=='users':result['accounts']=list(c[db].users.find({}, {'_id':1,'type':1,'operations':1}))
   else:
    result['process_count']=c[db].processes.count_documents({})
    result['projects']=list(c[db].projects.find({}, {'_id':1,'user_id':1,'name':1,'version':1}))
  finally:c.close()
 assert result['process_count']==0
 return hashlib.sha256(json.dumps(result,sort_keys=True,default=str).encode()).hexdigest()

def run():
 action=sys.argv[1]
 if action=='archive-quarantine':
  record=json.loads((PROOF/'quarantine.json').read_text())
  if (PROOF/'quarantine-archived.json').exists():return {'already_archived':True}
  conn=broker(True);ch=conn.channel()
  method,props,body=ch.basic_get(record['holding_queue'],auto_ack=False)
  if not method:raise RuntimeError('owned_quarantine_missing_do_not_repeat')
  if json.loads(body).get('messageId')!=fixture['message_id']:
   ch.basic_nack(method.delivery_tag,requeue=True);raise RuntimeError('unexpected_quarantine_preserved')
  # Exclusive durable copy before acknowledging this one technical fixture.
  fd=os.open(PROOF/'archived-message.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as output:output.write(body);output.flush();os.fsync(output.fileno())
  ch.basic_ack(method.delivery_tag);conn.close()
  (PROOF/'quarantine-archived.json').write_text(json.dumps({'only_owned_fixture':True,'no_replay':True}))
  (PROOF/'quarantine-archived.json').chmod(0o600)
  return {'owned_fixture_archived':True}
 if action=='publish':
  before=domain_state();fixture['domain_before']=before
  (PROOF/'fixture.json').write_text(json.dumps(fixture));(PROOF/'fixture.json').chmod(0o600)
  msg={'messageId':fixture['message_id'],'procedure':'video','parameters':{
    'inputImageURI':fixture['input'],'outputImageURI':fixture['output'],
    'tools':[{'procedure':'brightness','params':{'brightness':1.01}}]*fixture.get('brightness_steps',1), 'preview':False,
    'progress':{'user':fixture['user'],'projectId':fixture['project'],'imgId':'0'*24}}}
  conn=broker();ch=conn.channel();ch.confirm_delivery()
  ch.basic_publish('picturas','video_queue',json.dumps(msg),mandatory=True,
      properties=pika.BasicProperties(delivery_mode=2,message_id=fixture['message_id'],content_type='application/json'))
  conn.close();return {'published':True}
 if action=='quarantine':
  state=json.loads((ROOT/'maintenance'/json.loads((ROOT/'fixture-installation.json').read_text())['project']/'state.json').read_text());operation=state['operation']
  assert state.get('ca_changed') and state['pki_change']['phase']=='activated'
  conn=broker(True);ch=conn.channel();ch.confirm_delivery()
  method,props,body=ch.basic_get('video_queue',auto_ack=False)
  if not method:raise RuntimeError('fixture_message_missing_do_not_invent_recovery')
  if json.loads(body).get('messageId')!=fixture['message_id']:
   ch.basic_nack(method.delivery_tag,requeue=True);raise RuntimeError('unexpected_message_preserved')
  holding='pki_quarantine_'+operation
  ch.queue_declare(queue=holding,durable=True)
  ch.basic_publish('',holding,body,mandatory=True,properties=pika.BasicProperties(delivery_mode=2,content_type='application/json'))
  ch.basic_ack(method.delivery_tag);conn.close()
  after=domain_state();assert after==fixture['domain_before']
  record={'operation':operation,'message_id':fixture['message_id'],'technical_fixture':True,
    'only_fixture_message_quarantined':True,'no_domain_process':True,'no_domain_debit':True,
    'no_automatic_replay':True,'holding_queue':holding,'fixture_outputs_quarantined':False}
  (PROOF/'quarantine.json').write_text(json.dumps(record));(PROOF/'quarantine.json').chmod(0o600)
  return {'quarantined':True,'domain_unchanged':True}
 raise RuntimeError('invalid_fixture_action')

try:print(json.dumps(run()))
except Exception as e:
 print(json.dumps({'error_type':type(e).__name__,'fixture_failed':True}));raise SystemExit(1)
