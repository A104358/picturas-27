"""Native quota component fixture on dev; not an installation recovery/bypass."""
import json,os,sys,traceback,uuid
from pathlib import Path
sys.path.insert(0,'/ops')
from reconcile import Native
from bson import ObjectId

native=Native();account=None
try:
 import requests
 http=requests.Session();http.trust_env=False;http.verify=native.ca
 email='quota-'+uuid.uuid4().hex+'@example.invalid'
 response=http.post('https://nginx/api-gateway/users/',json={'name':'B11 quota component',
  'email':email,'password':uuid.uuid4().hex,'type':'free'},timeout=15)
 if response.status_code!=201:raise RuntimeError('fixture_registration_failed')
 body=response.json();account={'id':body['user']['_id'],'token':body['jwt']}
 native.save('account-private.json',account)
 run={'_id':str(uuid.uuid4()),'schema_version':1,'runner_id':ObjectId(account['id']),
  'user_id':ObjectId(),'project_id':ObjectId(),'token':1,'cost':{'image':2,'video':3},'debit_state':'unknown'}
 headers={'x-processing-run':run['_id'],'x-processing-project':str(run['project_id']),
  'x-processing-owner':str(run['user_id']),'x-processing-generation':'1','x-processing-images':'2','x-processing-videos':'3'}
 cert=native.installation/'pki/services/projects'
 admitted=http.get(f"https://users:10001/{account['id']}/process/5",headers=headers,
  cert=(str(cert/'service.crt'),str(cert/'service.key')),timeout=15)
 if admitted.status_code!=200:raise RuntimeError('fixture_admission_failed')
 before=native.users.users.find_one({'_id':run['runner_id']})
 if sum(o['processed'] for o in before['operations'])!=5:raise RuntimeError('fixture_debit_incorrect')
 # Simulate losing the database write response in the actual administrative
 # component. Unlike hard-exit mode, this exercises the catch/readback branch.
 os.environ['RECONCILE_FAILPOINT']='quota_lost_response';os.environ.pop('RECONCILE_FAIL_MODE',None)
 first=native.compensate(run,'component:'+run['_id'])
 after=native.users.users.find_one({'_id':run['runner_id']})
 if not first.get('readback_after_lost_response') or sum(o['processed'] for o in after['operations'])!=0:
  raise RuntimeError('fixture_lost_response_not_reconciled')
 revision=after['quotaRevision']
 repeated=native.compensate(run,'other-component-case:'+run['_id'])
 current=native.users.users.find_one({'_id':run['runner_id']})
 if repeated['status']!='already_applied' or current['quotaRevision']!=revision or current['operations']!=after['operations']:
  raise RuntimeError('fixture_repeated_financial_effect')
 events=[native.read(str(p.relative_to(native.case))) for p in (native.case/'effect-events').glob('*.json')]
 if not any(e.get('readback_after_lost_response') for e in events):raise RuntimeError('fixture_readback_event_not_durable')
 public={'native_mongo':True,'shipped_users_admission':True,'mixed_cost':5,'before':5,'after':0,
  'lost_response_rereads_marker':True,'no_second_financial_write':True,'private_readback_event_preserved':True,
  'component_fixture_only':True}
 native.save('public-proof.json',public)
 print('PASS native Mongo lost-response readback, durable event and no second financial write')
except Exception:
 native.save('failure-private.json',{'traceback':traceback.format_exc()})
 print('FAIL native quota component; inspect private evidence',file=sys.stderr);sys.exit(1)
finally:
 if account:
  deleted=http.delete('https://nginx/api-gateway/users/'+account['id'],
   headers={'Authorization':'Bearer '+account['token']},timeout=15)
  if deleted.status_code!=204:raise RuntimeError('fixture_account_cleanup_failed')
