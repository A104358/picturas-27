"""Bounded, read-only network observations for maintenance. No diagnostic credentials.

`cut` mounts no installation secrets and uses only the captured endpoint addresses.
`work` is privileged read-only inventory; `verify` checks actual TLS peers/roles.
"""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import sys
import time

ROOT=Path(os.environ.get('PICTURAS_SECRETS_DIR','/installation'))
PORTS={'nginx':[443], 'frontend':[3000], 'api_gateway':[8000], 'ws_gateway':[4000],
       'projects':[9001], 'users':[10001], 'subscriptions':[11001], 'img_storage':[11000],
       'generative-mock':[7860], 'rabbitmq':[5671,15671], 'seaweedfs':[9000,19000],
       'projects_mongoDB':[27018], 'users_mongoDB':[27019], 'subscriptions_mongoDB':[27017]}
PEERS={'frontend':'nginx','api_gateway':'nginx','ws_gateway':'nginx','projects':'api_gateway',
       'users':'projects','subscriptions':'api_gateway','img_storage':'projects',
       'generative-mock':'expand_ai_tool','seaweedfs-grpc':'seaweedfs'}

def secret(name): return (ROOT/'values'/name).read_text().strip()
def ctx(peer=None,ca=None,certroot=None):
    c=ssl.create_default_context(cafile=str(ca or ROOT/'pki/ca/ca.crt'))
    if peer:
        p=(certroot or ROOT/'pki')/'services'/peer
        c.load_cert_chain(p/'service.crt',p/'service.key')
    return c

def fingerprint(cert):
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert(cert.read_text())).hexdigest()

def transport(host,port,context,hostname=None,http=True):
    try:
        with socket.create_connection((host,port),timeout=2) as raw:
            with context.wrap_socket(raw,server_hostname=hostname or host) as tls:
                peer=hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest()
                if http:
                    path='/socket.io/?EIO=4&transport=polling' if host=='ws_gateway' else '/'
                    tls.sendall(('GET '+path+' HTTP/1.1\r\nHost: '+host+'\r\nConnection: close\r\n\r\n').encode())
                    data=tls.recv(1024)
                    if not data.startswith(b'HTTP/'):return {'result':'not_http'}
                    return {'result':'http','status':int(data.split(b' ')[1]),'peer':peer,'resumed':tls.session_reused}
                # For mTLS TLS 1.3, an invalid client can be rejected after wrap_socket.
                tls.settimeout(.25)
                try:
                    tls.sendall(b'\x00');tls.recv(1)
                except socket.timeout: pass
                return {'result':'tls','peer':peer,'resumed':tls.session_reused}
    except ssl.SSLError as e:
        return {'result':'tls_refused','reason':getattr(e,'verify_code',None) or getattr(e,'reason','ssl_error')}
    except OSError:
        return {'result':'unavailable'}

def work():
    import pymongo,requests
    client=pymongo.MongoClient('projects_mongoDB',27018,username='picturas_admin',password=secret('mongo_projects_admin'),
        authSource='admin',tls=True,tlsCAFile=str(ROOT/'pki/ca/ca.crt'),directConnection=True,
        serverSelectionTimeoutMS=2000,connectTimeoutMS=2000,socketTimeoutMS=2000)
    try:
        records=list(client.project.processes.find({}, {'_id':1,'project_id':1,'img_id':1,'msg_id':1,'token':1,'user_id':1}))
    finally:client.close()
    session=__import__('requests').Session();session.trust_env=False
    r=session.get('https://rabbitmq:15671/api/queues',verify=str(ROOT/'pki/ca/ca.crt'),
        auth=('picturas_admin',secret('rabbit_admin')),timeout=2);r.raise_for_status()
    queues=[{'name':q['name'],'ready':q.get('messages_ready',0),'unacknowledged':q.get('messages_unacknowledged',0),
             'consumers':q.get('consumers',0)} for q in r.json()]
    return {'processes':len(records),'process_inventory':json.loads(json.dumps(records,default=str)),
        'broker_work':sum(q['ready']+q['unacknowledged'] for q in queues),'queues':queues}

def cut():
    targets=json.loads(os.environ['CUT_TARGETS'])
    def one(target):
        try:
            with socket.create_connection((target['address'],target['port']),timeout=.4):closed=False
        except OSError:closed=True
        return {**target,'closed':closed}
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:rows=list(pool.map(one,targets))
    return {'all_closed':bool(rows) and all(r['closed'] for r in rows),'rows':rows,'observed_at_ns':time.time_ns()}

def data_controls(check):
    import pymongo
    from pymongo.errors import OperationFailure
    import pika
    import re
    for name,host,port,db in [('users','users_mongoDB',27019,'user'),('projects','projects_mongoDB',27018,'project'),
                              ('subscriptions','subscriptions_mongoDB',27017,'subscription')]:
        for role,user,password,writable in [('service',name+'_svc',secret('mongo_'+name+'_service'),True),
                                            ('backup','backup_ro',secret('mongo_'+name+'_backup'),False)]:
            client=None
            try:
                client=pymongo.MongoClient(host,port,username=user,password=password,authSource='admin',tls=True,
                    tlsCAFile=str(ROOT/'pki/ca/ca.crt'),directConnection=True,serverSelectionTimeoutMS=2000,
                    socketTimeoutMS=2000,connectTimeoutMS=2000)
                client[db].maintenance_readiness.find_one({'_id':'pki-readiness-no-document'})
                privileges=client.admin.command('connectionStatus',showPrivileges=True)['authInfo']['authenticatedUserPrivileges']
                writes=[p for p in privileges if set(p['actions']) & {'insert','update','remove','dropCollection'}]
                scoped=all(p['resource'].get('db')==db for p in writes)
                check(role+' -> '+host,'native authenticated read and role scope',{'read':True,'has_write':bool(writes),'write_scoped':scoped},
                      bool(writes)==writable and scoped)
            except Exception as error:
                check(role+' -> '+host,'native authenticated read and role scope',{'error_type':type(error).__name__},False)
            finally:
                if client is not None:client.close()
        bad=pymongo.MongoClient(host,port,username=name+'_svc',password='invalid-readiness-password',authSource='admin',tls=True,
             tlsCAFile=str(ROOT/'pki/ca/ca.crt'),serverSelectionTimeoutMS=2000,socketTimeoutMS=2000)
        try:
            bad[db].maintenance_readiness.find_one();refused=False
        except OperationFailure as error:refused=error.code==18
        except Exception:refused=False
        finally:bad.close()
        check('invalid credential -> '+host,'native authentication refusal',{'refused':refused},refused)
    definitions=json.loads((ROOT/'rabbitmq/definitions.json').read_text())
    queues=[q['name'] for q in definitions['queues']]
    reads={p['user']:p['read'] for p in definitions['permissions']}
    principals={}
    for file in (ROOT/'env').glob('*.env'):
        env=dict(line.split('=',1) for line in file.read_text().splitlines() if '=' in line and not line.startswith('#'))
        user=env.get('RABBITMQ_USERNAME') or env.get('RABBITMQ_USER')
        password=env.get('RABBITMQ_PASSWORD') or env.get('RABBITMQ_PASS')
        if user and password:principals[user]=password
    for user,password in principals.items():
        connection=None
        try:
            permitted=next(q for q in queues if re.fullmatch(reads[user],q))
            connection=pika.BlockingConnection(pika.ConnectionParameters('rabbitmq',5671,
                credentials=pika.PlainCredentials(user,password),ssl_options=pika.SSLOptions(ctx(),'rabbitmq'),
                socket_timeout=2,connection_attempts=1,heartbeat=0))
            connection.channel().queue_declare(queue=permitted,passive=True)
            check(user+' -> rabbitmq','native AMQPS principal and own queue',{'authenticated':True,'queue_scope':True},True)
        except Exception as error:
            check(user+' -> rabbitmq','native AMQPS principal and own queue',{'error_type':type(error).__name__},False)
        finally:
            if connection and connection.is_open:connection.close()
    try:
        connection=pika.BlockingConnection(pika.ConnectionParameters('rabbitmq',5671,
            credentials=pika.PlainCredentials('projects','invalid-readiness-password'),
            ssl_options=pika.SSLOptions(ctx(),'rabbitmq'),socket_timeout=2,connection_attempts=1))
    except (pika.exceptions.ProbableAuthenticationError,pika.exceptions.ProbableAccessDeniedError):refused=True
    except Exception:refused=False
    else:refused=False;connection.close()
    check('invalid credential -> rabbitmq','native AMQPS authentication refusal',{'refused':refused},refused)

def verify():
    state=json.loads(Path('/state/state.json').read_text())
    old=None
    if state.get('ca_changed'):
        old=ROOT/state['pki_change']['old_archive_relative']
    rows=[]
    def check(channel,label,value,passed):rows.append({'channel':channel,'case':label,'observation':value,'passed':bool(passed)})
    endpoints=[(host,port) for host,ports in PORTS.items() for port in ports]
    for host,port in endpoints:
        peer=PEERS.get('seaweedfs-grpc' if host=='seaweedfs' and port==19000 else host)
        is_http=port not in (5671,19000,27017,27018,27019)
        result=transport(host,port,ctx(peer),http=is_http)
        expected=fingerprint(ROOT/'pki/services'/host/'service.crt')
        channel=(peer or 'tls-client')+' -> '+host+':'+str(port)
        check(channel,'current certificate actually served',result,
              result.get('peer')==expected and result['result'] in ('http','tls'))
        if peer:
            negative=transport(host,port,ctx(),http=is_http)
            check(channel,'no client certificate',negative,negative['result']=='tls_refused')
        wrong=transport(host,port,ctx(peer),hostname='wrong-maintenance-name.invalid',http=is_http)
        check(channel,'wrong server name',wrong,wrong['result']=='tls_refused' and wrong.get('reason')==62)
        if old:
            retired_trust=transport(host,port,ctx(peer,ca=old/'ca/ca.crt'),http=is_http)
            check(channel,'withdrawn server CA rejected',retired_trust,retired_trust['result']=='tls_refused')
            if peer:
                # TLS 1.2 exposes the server's client-authentication alert before
                # application I/O; some Node/OpenSSL TLS 1.3 paths only close/reset.
                retired_context=ctx(peer,certroot=old)
                if host in ('frontend','api_gateway','ws_gateway','projects','users','subscriptions','img_storage'):
                    retired_context.maximum_version=ssl.TLSVersion.TLSv1_2
                    current_context=ctx(peer)
                    current_context.maximum_version=ssl.TLSVersion.TLSv1_2
                    current_client=transport(host,port,current_context,http=is_http)
                    check(channel,'current client on the same TLS 1.2 control',current_client,
                          current_client.get('peer')==expected and current_client['result']=='http')
                retired_client=transport(host,port,retired_context,http=is_http)
                check(channel,'withdrawn client certificate rejected',retired_client,retired_client['result']=='tls_refused')
    # The same CA is insufficient: test an authenticated but disallowed caller.
    for host,port in [('frontend',3000),('api_gateway',8000),('ws_gateway',4000),('projects',9001),
                      ('users',10001),('subscriptions',11001),('img_storage',11000),('generative-mock',7860)]:
        bad=transport(host,port,ctx('seaweedfs'))
        check('seaweedfs -> '+host,'wrong principal refused',bad,bad['result']=='http' and bad.get('status')==403)
    for host,ports in [('rabbitmq',[5672,15672,4369,25672,15692]),('seaweedfs',[8888,18888,9333,19333,8080,18080])]:
        for port in ports:
            try:
                with socket.create_connection((host,port),timeout=.4):closed=False
            except OSError:closed=True
            check('network -> '+host+':'+str(port),'plaintext/admin bypass closed',{'closed':closed},closed)
    data_controls(check)
    return {'passed':bool(rows) and all(r['passed'] for r in rows),'rows':rows,'observed_at_ns':time.time_ns()}

if __name__=='__main__':
    try:
        result={'work':work,'cut':cut,'verify':verify}[sys.argv[1]]()
        print(json.dumps(result))
    except Exception:
        print(json.dumps({'error':'probe_failed_no_credentials_reported'}));sys.exit(1)
