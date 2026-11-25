#!/usr/bin/env python3
"""Local PKI maintenance; private durable state, no automatic mutation replay.

Isolation uses container termination (including workers, databases and broker),
not only an ingress rule. Every reopen is gated until the manifest and probes pass.
"""
import argparse
import concurrent.futures
import contextlib
import datetime as dt
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

REPO = Path(__file__).resolve().parents[1]
IMAGE = 'picturas-maintenance-probe'
CLOCK_START = time.monotonic_ns()
UTC_START = dt.datetime.now(dt.timezone.utc).isoformat()
CLOCK_EPOCH = Path('/proc/sys/kernel/random/boot_id').read_text().strip() if Path('/proc/sys/kernel/random/boot_id').exists() else None

def fail(code):
    raise RuntimeError(code)

def command(args, *, env=None, timeout=120, allowed=False):
    result = subprocess.run(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode and not allowed:
        fail('command_failed_' + Path(str(args[0])).name.replace('-', '_'))
    return result

def decoded(args, **kw):
    return json.loads(command(args, **kw).stdout)

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def durable(file, value):
    file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = file.with_name(file.name + '.' + uuid.uuid4().hex + '.tmp')
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as output:
        json.dump(value, output, indent=2); output.write('\n'); output.flush(); os.fsync(output.fileno())
    os.replace(tmp, file)
    fd = os.open(file.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

def acquire_lock(base):
    # Kernel ownership is released even on SIGKILL. Keep the inode: unlinking it
    # could let another process lock a different file while a waiter owns this one.
    fd=os.open(base/'operation.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        if os.fstat(fd).st_uid!=os.getuid() or os.fstat(fd).st_mode&0o077:fail('operation_lock_not_private')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except Exception:
        os.close(fd);fail('operation_locked_review_before_retry')
    return fd

def release_lock(fd):
    fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)

def certificate(file):
    der = command(['openssl','x509','-in',str(file),'-outform','DER']).stdout
    return hashlib.sha256(der).hexdigest()

class Maintenance:
    def __init__(self, args):
        self.args = args
        self.root = Path(os.environ['PICTURAS_SECRETS_DIR']).resolve()
        if self.root == REPO or REPO in self.root.parents: fail('secrets_inside_repository')
        if not re.fullmatch(r'picturas-[a-z0-9][a-z0-9-]*', args.project) or args.project == 'picturas-nfr':
            fail('use_an_explicit_non_official_project')
        self.base = self.root / 'maintenance' / args.project
        self.base.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.base, 0o700)
        self.state_file = self.base / 'state.json'
        self.state = json.loads(self.state_file.read_text()) if self.state_file.exists() else None
        if self.state and not args.compose_file:
            args.compose_file=self.state.get('compose_files',[])
        self.compose = ['docker','compose','-p',args.project,'-f',str(REPO/'docker-compose.yaml')]
        for extra in args.compose_file: self.compose += ['-f',str(Path(extra).resolve())]
        self.gate = self.root / 'maintenance-gate/admissions-closed'

    def save(self, phase):
        self.state['phase'] = phase
        self.state['updated_at'] = utc()
        events=self.state.setdefault('events',[])
        events.append({'phase':phase,'at':self.state['updated_at'],'monotonic_ns':time.monotonic_ns()})
        if len(events)>512:
            del events[0];self.state['events_truncated']=self.state.get('events_truncated',0)+1
        durable(self.state_file, self.state)
        durable(self.base / (self.state['operation']+'.json'), self.state)

    def containers(self):
        # Image build labels also appear on standalone unit-test containers. A
        # Compose participant must have the runtime config label as well.
        ids = command(['docker','ps','-aq','--filter','label=com.docker.compose.project='+self.args.project,
                       '--filter','label=com.docker.compose.config-hash']).stdout.split()
        if not ids: return []
        return decoded(['docker','inspect',*[x.decode() for x in ids]])

    def participants(self, containers):
        result = []
        for item in containers:
            # Never store Config.Env: it contains the runtime credentials.
            result.append({'service':item['Config']['Labels']['com.docker.compose.service'],
                'id':item['Id'],'image':item['Image'],'pid':item['State']['Pid'],
                'started_at':item['State']['StartedAt'],'running':item['State']['Running'],
                'exit_code':item['State']['ExitCode'], 'restart_policy':item['HostConfig']['RestartPolicy'],
                'addresses':[v.get('IPAddress') for v in item['NetworkSettings']['Networks'].values() if v.get('IPAddress')],
                'pki_mounts':[{'destination':m['Destination'],'source_sha256':hashlib.sha256(m['Source'].encode()).hexdigest()}
                              for m in item['Mounts'] if '/pki' in m['Destination']]})
        return result

    def probe(self, action, *extra):
        args=['docker','run','--rm','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
              '--user',str(os.getuid())+':'+str(os.getgid()),'--network',self.args.project+'_elk',
              '-v',str(REPO/'ops')+':/ops:ro']
        if action=='cut':
            ports={'nginx':[443], 'frontend':[3000], 'api_gateway':[8000], 'ws_gateway':[4000],
              'projects':[9001], 'users':[10001], 'subscriptions':[11001], 'img_storage':[11000],
              'generative-mock':[7860], 'rabbitmq':[5671,15671], 'seaweedfs':[9000,19000],
              'projects_mongoDB':[27018], 'users_mongoDB':[27019], 'subscriptions_mongoDB':[27017]}
            targets=[{'service':p['service'],'address':address,'port':port}
                     for p in self.state['participants_before'] for address in p['addresses']
                     for port in ports.get(p['service'],[])]
            args+=['-e','CUT_TARGETS='+json.dumps(targets)]
            import socket
            try:
                with socket.create_connection(('127.0.0.1',8080),timeout=.5): public_closed=False
            except OSError: public_closed=True
        else:
            args+=['-v',str(self.root)+':/installation:ro','-v',str(self.base)+':/state:ro',
                   '-e','PICTURAS_SECRETS_DIR=/installation']
        p=command([*args,IMAGE,'python','/ops/maintenance_probe.py',action,*extra],timeout=90)
        result=json.loads(p.stdout)
        if action=='cut':
            result['public_closed']=public_closed
            result['all_closed']=result['all_closed'] and public_closed
        return result

    def manifest(self):
        result={}
        for p in (self.root/'pki/services').iterdir():
            if not p.is_dir() or not (p/'service.crt').exists():continue
            details=command(['openssl','x509','-in',str(p/'service.crt'),'-noout','-serial','-subject','-issuer',
                '-nameopt','RFC2253','-dates','-ext','subjectAltName,extendedKeyUsage']).stdout.decode().strip()
            result[p.name]={'certificate':certificate(p/'service.crt'),'ca':certificate(p/'ca.crt'),'public_profile':details}
        return result

    def safe_manifest(self):
        try: return self.manifest()
        except Exception: return {'observation_unavailable': True}

    def begin(self):
        if self.state and self.state['phase'] not in ('reopened','cancelled'):
            if self.state['mode'] != self.args.mode: fail('operation_already_active')
            return
        current = self.containers()
        if not current: fail('no_participants')
        self.state = {'schema_version':1,'operation':uuid.uuid4().hex,'project':self.args.project,
            'mode':self.args.mode,'t_detectado':self.args.detected_at or UTC_START,
            't_comando':UTC_START,'command_monotonic_ns':CLOCK_START,'clock_epoch':CLOCK_EPOCH,'t_isolado':None,
            't_reabertura':None,'phase':'starting','commit':command(['git','rev-parse','HEAD']).stdout.decode().strip(),
            'participants_before':self.participants(current),'certificates_before':self.safe_manifest(),
            'interrupted_work':self.args.mode == 'compromise', 'reconciliation':None,
            'compose_files':[str(Path(p).resolve()) for p in self.args.compose_file]}
        self.save('starting')

    def close_admissions(self):
        # Content is only a public operation reference; the directory is already private.
        self.gate.parent.mkdir(parents=True,exist_ok=True,mode=0o755)
        self.gate.parent.chmod(0o755)
        durable(self.gate,self.state['operation'])

    def planned_busy(self):
        nginx = next((p for p in self.containers() if p['Config']['Labels']['com.docker.compose.service']=='nginx'),None)
        if not nginx or not nginx['State']['Running']: fail('planned_ingress_observation_unavailable')
        output = command(['docker','exec',nginx['Id'],'curl','-fsS','--max-time','2',
                          'http://127.0.0.1:8091/maintenance-status']).stdout.decode()
        match = re.search(r'Reading:\s*(\d+)\s+Writing:\s*(\d+)',output)
        if not match: fail('invalid_ingress_observation')
        reading,writing = map(int,match.groups())
        table = command(['docker','exec',nginx['Id'],'cat','/proc/net/tcp','/proc/net/tcp6']).stdout.decode()
        websockets = sum(1 for line in table.splitlines() if len(line.split())>3 and
                         line.split()[2].endswith(':0FA0') and line.split()[3]=='01')
        work = self.probe('work')
        broker=next((p for p in self.containers() if p['Config']['Labels']['com.docker.compose.service']=='rabbitmq'),None)
        if not broker: fail('broker_work_observation_unavailable')
        live_queues=decoded(['docker','exec',broker['Id'],'rabbitmqctl','--quiet','--formatter=json',
                             'list_queues','name','messages_ready','messages_unacknowledged'])
        work['broker_work']=sum(q['messages_ready']+q['messages_unacknowledged'] for q in live_queues)
        work['live_queues']=live_queues
        workers=[]
        for participant in self.containers():
            service=participant['Config']['Labels']['com.docker.compose.service']
            if not (service.endswith('_tool') or service=='watermark_tool_ms' or service=='projects'): continue
            script='for f in /run/picturas/picturas-work-*.json; do [ -f "$f" ] || continue; cat "$f"; printf "\\n"; done'
            result=command(['docker','exec',participant['Id'],'sh','-c',script])
            for line in result.stdout.splitlines():
                if line.strip():
                    value=json.loads(line)
                    if value['active_count']>0: workers.append({'service':service,**value})
        work['active_local_workers']=workers
        observation = {'at':utc(),'reading':reading,'writing':writing,
            'ws_upstream_connections':websockets,'active_non_ws_requests':max(0,writing-websockets-1),**work}
        self.state.setdefault('drain_observations',[]).append(observation)
        self.save('admissions_suspended')
        return reading>0 or writing-websockets-1>0 or work['processes']>0 or work['broker_work']>0 or bool(work['active_local_workers'])

    def isolate(self):
        self.begin()
        if self.state.get('t_isolado'): return
        try: self.close_admissions()
        except OSError:
            if self.args.mode=='planned': raise
            self.state['ingress_gate_unavailable']=True
        if self.args.mode=='planned' and self.planned_busy():
            self.save('deferred_busy'); fail('maintenance_deferred_busy_no_participant_stopped')
        active = [p['Id'] for p in self.containers() if p['State']['Running']]
        # Disable restart before killing. No worker can continue local CPU/file work or
        # reconnect after a daemon restart while an operation is isolated.
        if active:
            command(['docker','update','--restart=no',*active])
            command(['docker','kill',*active],allowed=True)
        current = self.containers()
        if any(p['State']['Running'] or p['State']['Pid'] for p in current):
            self.save('isolation_incomplete'); fail('participants_still_running')
        try: proof = self.probe('cut')
        except Exception:
            self.save('isolation_incomplete'); raise
        self.state['cut_observation'] = proof
        self.state['participants_isolated'] = self.participants(current)
        if not proof['all_closed']:
            self.save('isolation_incomplete'); fail('isolation_incomplete')
        if getattr(self.args,'cut_proof',None):
            witness_path=Path(self.args.cut_proof).resolve()
            if self.root not in witness_path.parents:fail('cut_witness_must_be_private_local')
            deadline=time.monotonic()+5
            while not witness_path.exists() and time.monotonic()<deadline:time.sleep(.05)
            try:
                witness=json.loads(witness_path.read_text())
                if witness.get('operation')!=self.state['operation'] or witness.get('all_persistent_cut') is not True:
                    fail('persistent_cut_not_observed')
            except Exception:
                self.save('isolation_incomplete');raise
            self.state['persistent_cut_witness']=witness
        self.state['t_isolado'] = utc()
        elapsed=time.monotonic_ns()-self.state['command_monotonic_ns']
        same_clock=self.state.get('clock_epoch',CLOCK_EPOCH)==CLOCK_EPOCH and CLOCK_EPOCH is not None and elapsed>=0
        self.state['isolation_ms'] = elapsed/1e6 if same_clock else None
        self.state['isolation_limit_met'] = same_clock and self.state['isolation_ms']<=30000
        self.state['isolation_target_met'] = same_clock and self.state['isolation_ms']<=10000
        self.save('isolated' if self.state['isolation_limit_met'] else 'isolated_over_30s')

    def stage(self, kind):
        if not self.state or not self.state.get('t_isolado'): fail('isolate_before_pki_change')
        if any(p['State']['Running'] for p in self.containers()): fail('participant_running')
        if self.state.get('pki_change'): fail('pki_change_already_started_reconcile_do_not_retry')
        candidate = self.base / self.state['operation'] / 'candidate'
        candidate.mkdir(parents=True,mode=0o700)
        env = dict(os.environ,PICTURAS_SECRETS_DIR=str(candidate))
        self.state['pki_change']={'kind':kind,'started_at':utc(),'phase':'preparing'}
        self.save('preparing_pki')
        if kind=='renew':
            shutil.copytree(self.root/'pki',candidate/'pki')
            for service in self.renew_targets:
                command([str(REPO/'ops/pki.sh'),'issue',service],env=env)
        else: command([str(REPO/'ops/pki.sh'),'init'],env=env)
        command([str(REPO/'ops/pki.sh'),'check'],env=env)
        old = self.base / self.state['operation'] / 'withdrawn-pki'
        self.state['pki_change']['phase']='activation_intent'
        self.state['pki_change']['old_archive']=str(old)
        self.state['pki_change']['old_archive_relative']=str(old.relative_to(self.root))
        self.save('pki_activation_intent')
        # No rollback to withdrawn trust. Any interruption leaves admissions closed and
        # participants stopped; the durable intent tells the operator what to reconcile.
        os.rename(self.root/'pki',old)
        os.rename(candidate/'pki',self.root/'pki')
        self.state['pki_change'].update(phase='activated',activated_at=utc())
        self.state['certificates_expected']=self.manifest()
        self.state['ca_changed']=kind=='retire'
        self.save('pki_activated_isolated')

    def loaded_material(self, participants):
        expected_ca=certificate(self.root/'pki/ca/ca.crt')
        records={}
        for item in participants:
            service=item['service']
            if service in ('nginx','rabbitmq','seaweedfs','s3-bootstrap','mongo-backup') or service.endswith('_mongoDB'):
                continue
            # Read records only for live processes. A short-lived CLI cannot attest the
            # application process, and a dead process's old file is not evidence.
            script='for f in /run/picturas/pki-loaded-*.json; do [ -f "$f" ] || continue; p=${f##*/pki-loaded-}; p=${p%.json}; [ -d "/proc/$p" ] && cat "$f" && printf "\\n"; done'
            result=command(['docker','exec',item['id'],'sh','-c',script],allowed=True)
            values=[]
            for line in result.stdout.splitlines():
                if not line.strip(): continue
                try: value=json.loads(line)
                except ValueError: fail('invalid_loaded_material_record')
                if value.get('ca')!=expected_ca or value.get('trusted_cas')!=[expected_ca]:
                    fail('participant_still_trusts_other_ca')
                if service in self.state['certificates_loaded'] and service!='expand_ai_tool' and value.get('certificate')!=self.state['certificates_loaded'][service]['certificate']:
                    fail('participant_certificate_not_updated')
                values.append(value)
            if not values: fail('participant_loaded_material_unobserved_'+service.replace('-','_').lower())
            records[service]=values
            self.state['loaded_material_partial']=dict(records)
        return records

    def fixture_reconciliation(self):
        if not self.args.fixture_proof: return
        # D-33/decision 42: no such escape exists for a normal installation.
        installation=self.root/'fixture-installation.json'
        if not self.args.project.startswith('picturas-pki-pilot-') or not installation.exists():
            fail('technical_fixture_proof_forbidden_for_normal_installation')
        marker=json.loads(installation.read_text())
        proof_path=Path(self.args.fixture_proof).resolve()
        if self.root not in proof_path.parents or proof_path.stat().st_mode & 0o077:
            fail('fixture_proof_must_be_private_and_local')
        proof=json.loads(proof_path.read_text())
        if marker.get('technical_fixture') is not True or marker.get('project')!=self.args.project or proof.get('operation')!=self.state['operation'] or \
           not all(proof.get(k) is True for k in ('technical_fixture','only_fixture_message_quarantined',
             'fixture_outputs_quarantined','no_domain_process','no_domain_debit','no_automatic_replay')):
            fail('fixture_reconciliation_incomplete')
        if not re.fullmatch(r'[a-f0-9-]{16,64}',proof.get('message_id','')):
            fail('fixture_message_not_identified')
        self.state['reconciliation']={'type':'technical_fixture_only','proof_sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest(),
            'message_id':proof['message_id'],'at':utc()}
        self.save('fixture_quarantined_isolated')

    def validate_mounts(self):
        config=decoded([*self.compose,'config','--format','json'])
        original={p['service']:{m['destination']:m['source_sha256'] for m in p['pki_mounts']}
                  for p in self.state['participants_before']}
        if set(config['services'])!=set(original): fail('participant_configuration_changed')
        for service,definition in config['services'].items():
            mounts={m['target']:hashlib.sha256(m['source'].encode()).hexdigest()
                    for m in definition.get('volumes',[]) if '/pki' in m['target']}
            if mounts!=original[service]: fail('participant_not_updated_or_wrong_pki_mount')

    def start_for_verification(self):
        self.fixture_reconciliation()
        if self.state['interrupted_work'] and not self.state.get('reconciliation'):
            fail('interrupted_work_requires_reconciliation_before_consumers_restart')
        proof=self.state.get('reconciliation') or {}
        if proof.get('type')=='business_runs':
            case=self.base/self.state['operation']/'reconciliation'
            if proof.get('operation')!=self.state['operation'] or proof.get('case')!=str(case):
                fail('reconciliation_operation_mismatch')
            seal_path=case/'seal.json'
            if hashlib.sha256(seal_path.read_bytes()).hexdigest()!=proof.get('seal_sha256'):
                fail('reconciliation_seal_changed')
            seal=json.loads(seal_path.read_text())
            if seal.get('operation')!=self.state['operation'] or seal.get('project')!=self.args.project or seal.get('complete') is not True or seal.get('pending')!=0:
                fail('reconciliation_not_complete')
            files={str(p.relative_to(case)) for p in case.rglob('*') if p.is_file() and p.name!='seal.json'}
            if files!=set(seal.get('files',{})):fail('reconciliation_inventory_changed')
            for name,digest in seal['files'].items():
                file=case/name
                if file.is_symlink() or file.stat().st_uid!=os.getuid() or file.stat().st_mode&0o077 or hashlib.sha256(file.read_bytes()).hexdigest()!=digest:
                    fail('reconciliation_evidence_changed')
            report=json.loads((case/'report.json').read_text())
            if report.get('sealed') is not True or report.get('unknown') or any(c['state']=='indeterminate' for c in report['cases']):
                fail('reconciliation_pending_remains_isolated')
        if not self.gate.exists(): fail('admission_gate_missing')
        if json.loads(self.gate.read_text())!=self.state['operation']:fail('admission_gate_operation_mismatch')
        if any(p['State']['Running'] for p in self.containers()):
            self.stop_partial('unexpected_running_participant'); fail('unexpected_running_participant_stopped')
        command([str(REPO/'ops/pki.sh'),'check'])
        self.validate_mounts()
        self.save('restarting_isolated')
        try:
            p = command([*self.compose,'up','-d','--force-recreate','--wait','--wait-timeout','240'],timeout=270,allowed=True)
        except Exception:
            self.stop_partial('restart_execution_failed');raise
        if p.returncode:
            self.stop_partial('restart_failed'); fail('restart_failed_remains_isolated')
        # Gate remains closed. Newly created processes/contexts replace every old TLS state.
        now = self.participants(self.containers())
        old = {p['service']:p for p in self.state['participants_before']}
        names = set(command([*self.compose,'config','--services']).stdout.decode().split())
        if set(p['service'] for p in now)!=names:
            self.stop_partial('manifest_incomplete'); fail('manifest_incomplete')
        for p in now:
            if p['id']==old.get(p['service'],{}).get('id'):
                self.stop_partial('old_participant'); fail('old_participant')
            if p['service']=='s3-bootstrap' and p['exit_code']==0: continue
            if not p['running'] or p['pid']==0:
                self.stop_partial('old_or_missing_participant'); fail('old_or_missing_participant')
        self.state['participants_loaded']=now
        self.state['certificates_loaded']=self.manifest()
        if self.state['certificates_loaded']!=self.state.get('certificates_expected',self.state['certificates_before']):
            self.stop_partial('certificate_manifest_changed'); fail('certificate_manifest_changed')
        self.save('verifying_isolated')
        try:
            deadline=time.monotonic()+90
            expected_users=set()
            for file in (self.root/'env').glob('*.env'):
                env=dict(line.split('=',1) for line in file.read_text().splitlines() if '=' in line and not line.startswith('#'))
                user=env.get('RABBITMQ_USERNAME') or env.get('RABBITMQ_USER')
                if user:expected_users.add(user)
            broker=next(p for p in now if p['service']=='rabbitmq')
            while True:
                try:
                    self.state['loaded_material']=self.loaded_material(now)
                    channels=decoded(['docker','exec',broker['id'],'rabbitmqctl','--quiet','--formatter=json',
                                     'list_channels','user','consumer_count'])
                    consumers={user:sum(c['consumer_count'] for c in channels if c['user']==user) for user in expected_users}
                    if all(n>0 for n in consumers.values()):
                        self.state['registered_consumers']=consumers;break
                    if time.monotonic()>=deadline:fail('required_consumer_not_ready')
                except RuntimeError as error:
                    if not str(error).startswith('participant_loaded_material_unobserved_') or time.monotonic()>=deadline:raise
                time.sleep(2)
            proof=self.probe('verify')
            storage=next(p for p in now if p['service']=='img_storage')
            native_s3=command(['docker','exec',storage['id'],'node','-e',
                'const s3=require("./services/s3Client");s3.config.maxRetries=0;s3.headBucket({Bucket:"picturas"},e=>{process.exit(e?1:0)});'],allowed=True,timeout=15)
            proof['native_s3_head']=native_s3.returncode==0
            proof['passed']=proof['passed'] and proof['native_s3_head']
            self.state['channel_controls']=proof
            if not proof['passed']: fail('channel_controls_failed')
        except Exception as error:
            if isinstance(error,RuntimeError) and re.fullmatch(r'[a-z0-9_]+',str(error)):
                self.state['failure_detail']=str(error)
            self.state.setdefault('verification_failures',[]).append({'at':utc(),
                'reason':self.state.get('failure_detail','channel_controls_failed'),
                'controls':self.state.get('channel_controls')})
            self.stop_partial('channel_controls_failed'); raise
        self.state['channel_controls']=proof
        self.save('verified_admissions_closed')

    def stop_partial(self, reason):
        active=[p['Id'] for p in self.containers() if p['State']['Running']]
        if active:
            command(['docker','update','--restart=no',*active],allowed=True)
            command(['docker','kill',*active],allowed=True)
        self.close_admissions()
        self.state['failure']=reason
        stopped=not any(p['State']['Running'] or p['State']['Pid'] for p in self.containers())
        self.save('failed_isolated' if stopped else 'isolation_incomplete')

    def reopen(self):
        if not self.state or not self.state.get('t_isolado'): fail('no_isolated_operation')
        if self.state.get('ca_changed'):
            if not self.args.browser_proof: fail('browser_trust_withdrawal_proof_required_admissions_remain_closed')
            proof=json.loads(Path(self.args.browser_proof).read_text())
            expected=certificate(self.root/'pki/ca/ca.crt')
            if proof.get('operation')!=self.state['operation'] or proof.get('new_ca')!=expected or \
               proof.get('manual') is not True or not all(proof.get(k) is True for k in
                    ('new_trust_positive','old_ca_removed','old_ca_rejected','expired_rejected','wrong_name_rejected','no_warning_override')):
                fail('browser_proof_incomplete_admissions_remain_closed')
            self.state['browser_proof']=proof
            if not self.args.persistent_proof:
                fail('persistent_connection_and_resumption_proof_required')
        if self.state['phase']!='verified_admissions_closed': self.start_for_verification()
        if self.state.get('ca_changed'):
            proof_path=Path(self.args.persistent_proof).resolve()
            if self.root not in proof_path.parents:
                self.stop_partial('external_persistent_proof'); fail('persistent_proof_must_be_private_local')
            deadline=time.monotonic()+8
            while not proof_path.exists() and time.monotonic()<deadline:time.sleep(.1)
            try:
                if not proof_path.exists() or proof_path.stat().st_size>65536 or proof_path.stat().st_mode & 0o077:
                    fail('persistent_proof_missing_or_unsafe')
                persistent=json.loads(proof_path.read_text())
                if persistent.get('operation')!=self.state['operation'] or \
                    persistent.get('new_ca')!=certificate(self.root/'pki/ca/ca.crt') or \
                    persistent.get('all_refused') is not True or persistent.get('all_persistent_cut') is not True or \
                    persistent.get('valid_old_ticket_tested') is not True:
                    fail('persistent_cut_or_resumption_control_failed')
            except Exception:
                self.stop_partial('persistent_cut_or_resumption_control_failed');raise
            self.state['persistent_controls']=persistent
        current={p['service']:(p['id'],p['pid'],p['running'],p['exit_code']) for p in self.participants(self.containers())}
        expected={p['service']:(p['id'],p['pid'],p['running'],p['exit_code']) for p in self.state['participants_loaded']}
        if current!=expected or self.manifest()!=self.state['certificates_loaded']:
            self.stop_partial('participant_changed_after_verification'); fail('participant_changed_after_verification')
        self.gate.unlink()
        self.state['t_reabertura']=utc()
        self.save('reopened')

    def cancel(self):
        # Only an uncut planned deferral can be cancelled. No certificate rollback.
        if not self.state or self.state.get('mode')!='planned' or self.state.get('t_isolado') or self.state.get('pki_change') or \
            self.state['phase'] not in ('starting','admissions_suspended','deferred_busy'):
            fail('only_an_unchanged_planned_deferral_can_be_cancelled')
        now=self.participants(self.containers())
        signature=lambda p:(p['id'],p['pid'],p['started_at'],p['running'])
        if sorted(signature(p) for p in now)!=sorted(signature(p) for p in self.state['participants_before']) or \
            self.manifest()!=self.state['certificates_before']:
            self.stop_partial('deferral_participant_or_certificate_changed');fail('deferral_changed_remains_isolated')
        if self.gate.exists():
            owner=self.gate.read_text().strip()
            if owner.startswith('"'):owner=json.loads(owner)
            if owner!=self.state['operation']:fail('admission_gate_owned_by_other_operation')
            self.gate.unlink()
        self.save('cancelled')

    def run(self):
        if self.args.action=='status':
            if not self.state: return {'phase':'no_operation'}
        elif self.args.action=='isolate': self.isolate()
        elif self.args.action=='cancel': self.cancel()
        elif self.args.action in ('renew','retire'):
            if self.args.action=='renew':
                targets=[p for p in (self.root/'pki/services').iterdir() if p.is_dir() and
                         (self.args.service=='all' or p.name==self.args.service)]
                if not targets: fail('unknown_service')
                self.renew_targets=[p.name for p in targets if self.args.force or command(['openssl','x509',
                     '-in',str(p/'service.crt'),'-noout','-checkend','604800'],allowed=True).returncode]
                if not self.renew_targets: return {'phase':'not_due','renewed':0}
            self.isolate(); self.stage(self.args.action)
            if self.args.action=='renew': self.reopen()
        elif self.args.action=='reopen':
            if self.state and self.state.get('phase')=='reopened':
                return {k:self.state.get(k) for k in ('operation','phase','isolation_ms','isolation_limit_met','isolation_target_met')}
            self.reopen()
        return {k:self.state.get(k) for k in ('operation','phase','isolation_ms','isolation_limit_met','isolation_target_met')}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['isolate','reopen','renew','retire','status','cancel'])
    parser.add_argument('--project',required=True)
    parser.add_argument('--mode',choices=['planned','compromise'],default='planned')
    parser.add_argument('--detected-at')
    parser.add_argument('--compose-file',action='append',default=[])
    parser.add_argument('--service',default='all')
    parser.add_argument('--force',action='store_true')
    parser.add_argument('--browser-proof')
    parser.add_argument('--fixture-proof')
    parser.add_argument('--persistent-proof')
    parser.add_argument('--cut-proof')
    args=parser.parse_args()
    maintenance=Maintenance(args)
    if args.action=='status': print(json.dumps(maintenance.run())); return
    fd=acquire_lock(maintenance.base)
    try: print(json.dumps(maintenance.run()))
    finally: release_lock(fd)

if __name__=='__main__':
    try: main()
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) and re.fullmatch(r'[a-z0-9_]+',str(error)) else 'maintenance_failed_review_private_state'
        print(json.dumps({'error':code}),file=sys.stderr);sys.exit(1)
