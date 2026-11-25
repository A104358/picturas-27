#!/usr/bin/env python3
"""OPS-C1 administrative reconciliation. Native evidence is private; no job replay.

The host owns isolation and the case seal. The networked helper cannot change local
worker files; the filesystem mover has no network or installation credentials.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

from maintenance import Maintenance, command, decoded, durable, fail, utc, REPO, acquire_lock, release_lock
from reconcile_policy import classification, fingerprint, refund_change, PendingEvidence
from reconcile_files import manifest

IMAGE='picturas-reconcile:1'
BACKENDS=['projects_mongoDB','users_mongoDB','subscriptions_mongoDB','rabbitmq','seaweedfs']

def crash(point):
    # Explicit operator failpoint, only in the administrative process. Never an HTTP input.
    if point in os.environ.get('RECONCILE_FAILPOINT','').split(','):
        if os.environ.get('RECONCILE_FAIL_MODE')=='exit':os._exit(86)
        fail('injected_'+point)

class Native:
    def __init__(self):
        import pymongo, boto3, pika, ssl, requests
        from botocore.config import Config
        self.case=Path('/case'); self.installation=Path('/installation')
        self.state=json.loads((self.case/'case.json').read_text())
        self.ca=str(self.installation/'pki/ca/ca.crt')
        def secret(name):return (self.installation/'values'/name).read_text().strip()
        self.clients=[]
        for name,db,port in [('projects','project',27018),('users','user',27019)]:
            client=pymongo.MongoClient(name+'_mongoDB',port,username='picturas_admin',password=secret('mongo_'+name+'_admin'),
                authSource='admin',tls=True,tlsCAFile=self.ca,directConnection=True,serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,socketTimeoutMS=30000,retryWrites=False)
            client.admin.command('ping');self.clients.append(client)
        self.projects=self.clients[0].project;self.users=self.clients[1].user
        self.s3=boto3.client('s3',endpoint_url='https://seaweedfs:9000',aws_access_key_id=secret('s3_admin_access'),
            aws_secret_access_key=secret('s3_admin_secret'),region_name='us-east-1',verify=self.ca,
            config=Config(signature_version='s3v4',s3={'addressing_style':'path'},retries={'max_attempts':0},connect_timeout=5,read_timeout=60))
        self.session=requests.Session();self.session.trust_env=False
        self.session.auth=('picturas_admin',secret('rabbit_admin'));self.session.verify=self.ca
        context=ssl.create_default_context(cafile=self.ca)
        self.broker=pika.BlockingConnection(pika.ConnectionParameters('rabbitmq',5671,
            credentials=pika.PlainCredentials('picturas_admin',secret('rabbit_admin')),
            ssl_options=pika.SSLOptions(context,'rabbitmq'),socket_timeout=5,blocked_connection_timeout=5,heartbeat=30))
        self.channel=self.broker.channel()

    def save(self,name,value):
        from bson import json_util
        # BSON types survive inventory/restart; IDs never leave the private case.
        durable(self.case/name,json.loads(json_util.dumps(value)))

    def read(self,name):
        from bson import json_util
        return json_util.loads((self.case/name).read_text())

    def object(self,key):
        from botocore.exceptions import ClientError
        try:
            response=self.s3.get_object(Bucket='picturas',Key=key)
        except ClientError as e:
            if e.response['Error']['Code'] in ('NoSuchKey','404','NotFound'):return None
            raise
        digest=hashlib.sha256();size=0
        with response['Body'] as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):
                size+=len(chunk);digest.update(chunk)
        return {'sha256':digest.hexdigest(),'size':size}

    def queues(self,archive=False):
        response=self.session.get('https://rabbitmq:15671/api/queues',timeout=10);response.raise_for_status()
        result=[];held=[]
        runs=list(self.projects.processing_runs.find())
        known={m for r in runs for m in r.get('message_ids',[])}
        try:
            for queue in response.json():
                if queue.get('consumers',0) or queue.get('messages_unacknowledged',0):fail('consumer_present_during_reconciliation')
                # One bounded snapshot: never basic_get/nack in a loop that sees its own requeues.
                count=self.channel.queue_declare(queue=queue['name'],passive=True).method.message_count
                for _ in range(count):
                    method,properties,body=self.channel.basic_get(queue=queue['name'],auto_ack=False)
                    if not method:fail('queue_changed_while_isolated')
                    try:value=json.loads(body)
                    except (ValueError,UnicodeDecodeError):value={}
                    ids=[value.get('messageId'),value.get('correlationId'),properties.message_id,properties.correlation_id]
                    matched=any(i in known for i in ids if i)
                    notification=queue['name']=='ws_queue' and bool(value.get('projectId'))
                    digest=hashlib.sha256(queue['name'].encode()+b'\0'+body).hexdigest()
                    fields=('content_type','content_encoding','headers','delivery_mode','priority','correlation_id',
                            'reply_to','expiration','message_id','timestamp','type','user_id','app_id','cluster_id')
                    prop={k:getattr(properties,k) for k in fields if getattr(properties,k,None) is not None}
                    record={'queue':queue['name'],'body':base64.b64encode(body).decode(),'properties':prop,
                            'sha256':digest,'known':matched or notification,'notification':notification}
                    result.append(record)
                    if archive and record['known']:
                        self.save('messages/'+digest+'.json',record)  # Durable body/properties BEFORE ack.
                        crash('message_before_ack')
                        self.channel.basic_ack(method.delivery_tag)
                    else:held.append(method.delivery_tag)
        finally:
            for tag in held:self.channel.basic_nack(tag,requeue=True)
        return result

    def snapshot(self):
        projects=list(self.projects.projects.find())
        current_ids=[p['committedRun']['run_id'] for p in projects if p.get('committedRun')]
        runs=list(self.projects.processing_runs.find({'$or':[{'phase':{'$nin':['committed','reconciled']}},{'_id':{'$in':current_ids}}]}))
        processes=list(self.projects.processes.find())
        results=list(self.projects.results.find())
        artifacts=list(self.projects.processing_artifacts.find())
        all_runs=list(self.projects.processing_runs.find({}, {'_id':1,'project_id':1,'token':1,'phase':1,'invalidated':1}))
        accounts=list(self.users.users.find({}, {'operations':1,'quotaLedger':1,'quotaRevision':1,'legacyQuotaRevision':1,'type':1}))
        objects={};protected={}
        for p in projects:
            prefix=f"users/{p['user_id']}/projects/{p['_id']}/"
            for image in p.get('imgs',[]):
                key=prefix+'src/'+image['og_img_key'];value=self.object(key);protected[key]=value
                if not value or (image.get('og_sha256') and value['sha256']!=image['og_sha256']):
                    fail('source_integrity_requires_investigation')
            for row in results:
                if row['project_id']==p['_id'] and row.get('token',0)==p.get('committedToken',0):
                    key=prefix+'out/'+row['img_key'];protected[key]=self.object(key)
                    if not protected[key]:fail('last_commit_integrity_requires_investigation')
        for a in artifacts:objects[a['key']]=self.object(a['key'])
        tracked={a['key'] for a in artifacts}
        tracked.update(f"users/{r['user_id']}/projects/{r['project_id']}/out/{r['img_key']}" for r in results)
        orphans=[]
        for page in self.s3.get_paginator('list_objects_v2').paginate(Bucket='picturas',Prefix='users/'):
            for item in page.get('Contents',[]):
                if '/out/' in item['Key'] and item['Key'] not in tracked:
                    orphans.append({'key':item['Key'],'object':self.object(item['Key'])})
        known_ids={r['_id'] for r in all_runs}
        local=Path('/images/runs')
        if local.is_symlink():fail('symlink_in_run_directory')
        orphan_directories=[p.name for p in local.iterdir() if p.name not in known_ids] if local.exists() else []
        queues=self.queues()
        return dict(projects=projects,runs=runs,processes=processes,results=results,artifacts=artifacts,
                    all_runs=all_runs,orphan_objects=orphans,orphan_directories=orphan_directories,
                    accounts=accounts,objects=objects,protected=protected,queues=queues)

    def classify(self,snapshot):
        cases=[]
        for run in snapshot['runs']:
            project=next((p for p in snapshot['projects'] if p['_id']==run['project_id']),None)
            account=next((u for u in snapshot['accounts'] if u['_id']==run['runner_id']),None)
            rows=[r for r in snapshot['results'] if r.get('run_id')==run['_id']]
            run['artifacts']=[a for a in snapshot['artifacts'] if a['run_id']==run['_id']]
            decision=classification(run,project or {},account,rows,snapshot['objects']) if project else {'state':'indeterminate','reason':'project_missing'}
            cases.append({'run_id':run['_id'],**decision})
        history=snapshot.get('all_runs',snapshot['runs'])
        known={r['_id'] for r in history}
        unknown=[p for p in snapshot['processes'] if p.get('run_id') not in known and not p.get('reconciled')]
        unattributed=0
        for project in snapshot['projects']:
            active=project.get('activeToken',0)
            owned=[r for r in history if r['project_id']==project['_id']]
            matching=any(r['token']==active for r in owned)
            fenced=bool(owned) and active>max(r['token'] for r in owned) and any(r.get('invalidated') for r in owned)
            if (project.get('processingRunId') and project['processingRunId'] not in known) or \
               (project.get('pendingAdvancedOps',0) and not matching) or \
               (active>project.get('committedToken',0) and not matching and not fenced):unattributed+=1
        pending_uploads=self.projects.uploads.count_documents({'$or':[
            {'state':{'$nin':['ready','ready_hash_pending','failed','rejected','expired','cancelled']}},
            {'cleanup':{'$nin':['none','cleaned']}}]})
        return cases,len(unknown)+unattributed+len(snapshot.get('orphan_objects',[]))+len(snapshot.get('orphan_directories',[]))+ \
            sum(not q['known'] for q in snapshot['queues'])+pending_uploads

    def inventory(self):
        if (self.case/'report.json').exists():return self.read('report.json')
        snapshot=self.read('snapshot.json') if (self.case/'snapshot.json').exists() else self.snapshot()
        cases,unknown=self.classify(snapshot)
        if not (self.case/'snapshot.json').exists():self.save('snapshot.json',snapshot)
        plan={'operation':self.state['operation'],'runs':[]}
        for row in cases:
            if row['state']!='confirmed':
                plan['runs'].append({'run_id':row['run_id'],'manifest':manifest(Path('/images/runs')/row['run_id'])})
        self.save('local-plan.json',plan)
        report={'operation':self.state['operation'],'cases':cases,'unknown':unknown,'applied':False,'sealed':False}
        self.save('report.json',report)
        return report

    def protected(self):
        for key,before in self.read('snapshot.json')['protected'].items():
            if self.object(key)!=before:fail('protected_source_or_commit_changed')

    def invalidate(self,run,identifier):
        p=self.projects.projects.find_one({'_id':run['project_id']})
        if not p:fail('project_missing')
        if p.get('activeToken',0)==run['token']:
            query={'_id':p['_id'],'activeToken':run['token'],'version':p.get('version',0)}
            fields={'activeToken':run['token']+1,'processingRunId':None,'pendingAdvancedOps':0,'reconciliationHold':True}
            result=self.projects.projects.update_one(query,{'$set':fields,'$inc':{'version':1,'__v':1}})
            if result.modified_count!=1:fail('generation_precondition_changed')
        elif p.get('activeToken',0)<run['token']:fail('generation_precondition_changed')
        # On restart, the already-incremented generation is read, never incremented twice.
        self.projects.processing_runs.update_one({'_id':run['_id']},{'$set':{'invalidated':True,'reconciliation':identifier}})
        self.projects.processes.update_many({'run_id':run['_id']},{'$set':{'reconciled':True}})
        crash('generation_after_commit')

    def quarantine_object(self,artifact):
        key=artifact['key'];expected={'sha256':artifact['sha256'],'size':artifact['size']}
        expected_key=f"users/{artifact['user_id']}/projects/{artifact['project_id']}/out/{artifact['img_key']}"
        if key!=expected_key or not artifact['img_key'].startswith('run-'+artifact['run_id']+'-'):fail('artifact_namespace_conflict')
        target='quarantine/'+self.state['operation']+'/'+key
        source=self.object(key);copied=self.object(target)
        if source is None and copied is None and self.read('snapshot.json')['objects'].get(key) is not None:
            fail('artifact_missing_without_quarantine_evidence')
        if source is not None and source!=expected:fail('artifact_bytes_changed')
        if copied is not None and copied!=expected:fail('quarantine_collision')
        if source is not None:
            if copied is None:
                self.s3.copy_object(Bucket='picturas',Key=target,CopySource={'Bucket':'picturas','Key':key})
            if self.object(target)!=expected:fail('quarantine_copy_unverified')
            crash('object_before_delete')
            self.s3.delete_object(Bucket='picturas',Key=key)
            crash('object_after_delete')
        # Missing intent object is legitimate if admission/upload died before any write.
        if self.object(key) is not None:fail('quarantine_delete_failed')
        return {'key':key,'target':target,'expected':expected,'existed':source is not None or copied is not None}

    def compensate(self,run,identifier):
        account=self.users.users.find_one({'_id':run['runner_id']})
        if run.get('debit_state') in ('not_requested','rejected') and not any(r['run_id']==run['_id'] for r in (account or {}).get('quotaLedger',[])):
            return {'status':'never_admitted','amount':0}
        updated,effect=refund_change(account,run,identifier)
        if updated is None:effect={**effect,'existing_marker_observed':True}
        if updated is not None:
            revision=account.get('quotaRevision',{'$exists':False})
            crash('quota_before_commit')
            try:
                result=self.users.users.update_one({'_id':account['_id'],'quotaRevision':revision},
                    {'$set':{'operations':updated['operations'],'quotaLedger':updated['quotaLedger']},'$inc':{'quotaRevision':1}})
                if result.modified_count!=1:fail('quota_precondition_changed')
                crash('quota_lost_response')
                crash('quota_after_commit')
            except Exception:
                # Do not retry the write after a lost response. Read the atomic marker.
                current=self.users.users.find_one({'_id':account['_id']})
                _,observed=refund_change(current,run,identifier)
                if observed['status']!='already_applied':raise
                if os.environ.get('RECONCILE_FAILPOINT')=='quota_after_commit':raise
                effect={**observed,'readback_after_lost_response':True}
                self.save('effect-events/'+uuid.uuid4().hex+'.json',{'run_id':run['_id'],**effect})
        return effect

    def apply(self):
        report=self.inventory();self.protected()
        review=json.loads((self.case/'integrity-review.json').read_text())
        snapshot_sha=hashlib.sha256((self.case/'snapshot.json').read_bytes()).hexdigest()
        if review.get('operation')!=self.state['operation'] or review.get('snapshot_sha256')!=snapshot_sha or review.get('integrity_verified') is not True or not review.get('basis'):
            fail('operator_integrity_review_required')
        snapshot=self.read('snapshot.json');effects=[];quarantined=[]
        for decision in report['cases']:
            if decision['state']=='confirmed':continue
            run=next(r for r in snapshot['runs'] if r['_id']==decision['run_id'])
            identifier='reconcile:'+self.state['operation']+':'+run['_id']
            self.invalidate(run,identifier)
            if decision['state']=='indeterminate':continue
            for artifact in run['artifacts'] if 'artifacts' in run else [a for a in snapshot['artifacts'] if a['run_id']==run['_id']]:
                quarantined.append(self.quarantine_object({**artifact,'user_id':run['user_id'],'project_id':run['project_id']}))
            effect=self.compensate(run,identifier);effects.append({'run_id':run['_id'],**effect})
            self.save('effect-events/'+uuid.uuid4().hex+'.json',{'run_id':run['_id'],**effect})
            self.save('effects.json',effects) # A crash before this file is covered by the user marker.
        self.queues(archive=True)
        self.save('object-quarantine.json',quarantined)
        report['applied']=True;self.save('report.json',report)
        return report

    def seal(self):
        report=self.read('report.json');self.protected()
        if not report['applied'] or report['unknown'] or any(c['state']=='indeterminate' for c in report['cases']):fail('unresolved_cases_remain_isolated')
        current=self.snapshot();current_cases,current_unknown=self.classify(current)
        known={c['run_id'] for c in report['cases']}
        if current_unknown or any(c['run_id'] not in known or c['state']=='indeterminate' for c in current_cases):
            fail('inventory_changed_requires_investigation')
        moves=self.read('local-proof.json');plan=self.read('local-plan.json')
        if moves['operation']!=self.state['operation'] or len(moves['runs'])!=len(plan['runs']):fail('local_quarantine_incomplete')
        for item in plan['runs']:
            if any(p.is_symlink() for p in (Path('/images/runs'),Path('/images/quarantine'),Path('/images/quarantine')/self.state['operation'])):
                fail('symlink_in_quarantine_parent')
            moved=next((m for m in moves['runs'] if m['run_id']==item['run_id']),None)
            if not moved or moved.get('quarantined') is not True or (item['manifest'] is not None and moved['manifest']!=item['manifest']):fail('local_quarantine_incomplete')
            source=Path('/images/runs')/item['run_id']
            target=Path('/images/quarantine')/self.state['operation']/item['run_id']
            if manifest(source) is not None or manifest(target)!=moved['manifest']:fail('local_quarantine_changed_before_seal')
        if self.queues():fail('unquarantined_messages_remain')
        snapshot=self.read('snapshot.json')
        for decision in report['cases']:
            run=next(r for r in snapshot['runs'] if r['_id']==decision['run_id'])
            p=self.projects.projects.find_one({'_id':run['project_id']})
            if decision['state']=='confirmed':
                if next(c for c in current_cases if c['run_id']==run['_id'])['state']!='confirmed':fail('confirmed_run_changed')
                continue
            if p.get('activeToken',0)<=run['token']:fail('obsolete_generation_still_live')
            self.compensate(run,'reconcile:'+self.state['operation']+':'+run['_id'])
            self.projects.processing_runs.update_one({'_id':run['_id'],'invalidated':True},{'$set':{'phase':'reconciled'}})
            self.projects.projects.update_one({'_id':p['_id'],'activeToken':p['activeToken']},{'$set':{'reconciliationHold':False}})
        for item in self.read('object-quarantine.json'):
            if self.object(item['key']) is not None or (item['existed'] and self.object(item['target'])!=item['expected']):fail('object_quarantine_incomplete')
        crash('before_seal')
        report['sealed']=True;report['sealed_at']=utc();self.save('report.json',report)
        return report

def host(args):
    probe=Maintenance(argparse.Namespace(**vars(args),mode='compromise',fixture_proof=None))
    fd=acquire_lock(probe.base)
    try:
        return host_locked(args)
    finally:
        release_lock(fd)

def host_locked(args):
    maintenance=Maintenance(argparse.Namespace(**vars(args),mode='compromise',fixture_proof=None))
    state=maintenance.state
    if not state or not state.get('t_isolado') or not maintenance.gate.exists():fail('isolate_first_using_maintenance')
    if json.loads(maintenance.gate.read_text())!=state['operation'] or state.get('phase') in ('reopened','cancelled'):
        fail('admission_gate_operation_mismatch')
    if not re.fullmatch('[a-f0-9]{32}',state['operation']):fail('operation_identifier_invalid')
    if any(p['State']['Running'] for p in maintenance.containers()):fail('all_participants_must_be_stopped')
    case=maintenance.base/state['operation']/'reconciliation';case.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(case,0o700)
    try:
        if not (case/'case.json').exists():durable(case/'case.json',{'operation':state['operation'],'project':args.project,'created_at':utc()})
        if args.action=='apply' and (case/'report.json').exists() and json.loads((case/'report.json').read_text()).get('sealed'):
            fail('case_already_sealed_use_status')
        if args.action=='status':
            report=json.loads((case/'report.json').read_text()) if (case/'report.json').exists() else {}
        else:
            if args.integrity_proof:
                review=Path(args.integrity_proof).resolve()
                if maintenance.root not in review.parents or review.stat().st_mode&0o077:fail('integrity_review_must_be_private_local')
                durable(case/'integrity-review.json',json.loads(review.read_text()))
            command(['docker','build','-t',IMAGE,'-f',str(REPO/'ops/reconcile.Dockerfile'),str(REPO/'ops')],timeout=300)
            command([*maintenance.compose,'up','-d','--no-deps','--no-build','--wait','--wait-timeout','180',*BACKENDS],timeout=210)
            current=maintenance.containers()
            if any(p['State']['Running'] and p['Config']['Labels']['com.docker.compose.service'] not in BACKENDS for p in current):fail('unexpected_consumer_running')
            config=decoded([*maintenance.compose,'config','--format','json'])
            volume=config['volumes']['image_data'].get('name',args.project+'_image_data')
            native=['docker','run','--rm','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
                '--user',str(os.getuid())+':'+str(os.getgid()),'--network',args.project+'_elk',
                '-v',str(REPO/'ops')+':/ops:ro',
                '-v',str(case)+':/case:rw','-v',volume+':/images:ro']
            # The networked data helper receives no CA signing key, session
            # secrets, gateway signing key or application client certificate.
            for name in ('mongo_projects_admin','mongo_users_admin','rabbit_admin','s3_admin_access','s3_admin_secret'):
                native+=['-v',str(maintenance.root/'values'/name)+':/installation/values/'+name+':ro']
            native+=['-v',str(maintenance.root/'pki/ca/ca.crt')+':/installation/pki/ca/ca.crt:ro']
            if os.environ.get('RECONCILE_FAILPOINT'):native+=['-e','RECONCILE_FAILPOINT='+os.environ['RECONCILE_FAILPOINT']]
            if os.environ.get('RECONCILE_FAIL_MODE'):native+=['-e','RECONCILE_FAIL_MODE='+os.environ['RECONCILE_FAIL_MODE']]
            p=command([*native,IMAGE,'python','/ops/reconcile.py','--native',args.action],timeout=600,allowed=True)
            if p.returncode:
                durable(case/'failures'/(uuid.uuid4().hex+'.json'),{'action':args.action,'at':utc(),
                    'failpoint':os.environ.get('RECONCILE_FAILPOINT'),'mode':os.environ.get('RECONCILE_FAIL_MODE'),'exit_code':p.returncode,
                    'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')})
                fail('native_'+args.action+'_failed_review_private_case')
            if args.action=='apply':
                mover=command(['docker','run','--rm','--read-only','--network','none','--cap-drop','ALL',
                    '--cap-add','DAC_OVERRIDE','--security-opt','no-new-privileges','-v',str(REPO/'ops')+':/ops:ro','-v',str(case)+':/case:ro',
                    '-v',volume+':/images:rw',IMAGE,'python','/ops/reconcile_files.py'],timeout=300,allowed=True)
                if mover.returncode:
                    durable(case/'failures'/(uuid.uuid4().hex+'.json'),{'action':'local_quarantine','at':utc(),
                        'stdout':mover.stdout.decode(errors='replace'),'stderr':mover.stderr.decode(errors='replace')})
                    fail('local_quarantine_failed_review_private_case')
                durable(case/'local-proof.json',json.loads(mover.stdout))
            report=json.loads((case/'report.json').read_text())
        if args.action=='seal':
            if report.get('sealed') is not True:fail('case_not_sealed')
            # Backends must be stopped before binding the proof to B10/reopening.
            command([*maintenance.compose,'stop','-t','10',*BACKENDS],timeout=90)
            files={str(p.relative_to(case)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(case.rglob('*')) if p.is_file() and p.name!='seal.json'}
            seal={'operation':state['operation'],'project':args.project,'complete':True,'pending':0,'files':files}
            durable(case/'seal.json',seal)
            state['reconciliation']={'type':'business_runs','operation':state['operation'],'case':str(case),
                'seal_sha256':hashlib.sha256((case/'seal.json').read_bytes()).hexdigest(),'at':utc()}
            maintenance.save('business_reconciled_isolated')
        counts={name:sum(c['state']==name for c in report.get('cases',[])) for name in ('confirmed','lost','indeterminate')}
        print(json.dumps({'operation_ref':hashlib.sha256(state['operation'].encode()).hexdigest()[:12],**counts,
            'unknown':report.get('unknown',0),'applied':report.get('applied',False),'sealed':report.get('sealed',False)}))
    finally:
        if args.action!='status':command([*maintenance.compose,'stop','-t','10',*BACKENDS],timeout=90,allowed=True)

def main():
    if len(sys.argv)>2 and sys.argv[1]=='--native':
        native=Native();getattr(native,sys.argv[2])();return
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['inventory','apply','seal','status'])
    parser.add_argument('--project',required=True);parser.add_argument('--compose-file',action='append',default=[])
    parser.add_argument('--integrity-proof',help='Private integrity review bound to the inventory digest')
    host(parser.parse_args())

if __name__=='__main__':
    try:main()
    except Exception as error:
        if len(sys.argv)>1 and sys.argv[1]=='--native':
            import traceback
            durable(Path('/case/failures')/(uuid.uuid4().hex+'.json'),{'traceback':traceback.format_exc(),'at':utc()})
        code=str(error) if isinstance(error,RuntimeError) and re.fullmatch('[a-z0-9_]+',str(error)) else 'reconciliation_failed_remains_isolated'
        print(json.dumps({'error':code}),file=sys.stderr);sys.exit(1)
