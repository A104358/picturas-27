"""Trusted, independent observer. No Docker socket; credentials never leave memory.

Keeps one real connection of each type before isolation. Raw TLS sessions are held
in memory for an explicit stale-session attempt after replacement, never exported.
"""
import hashlib
import http.client
import json
import os
from pathlib import Path
import socket
import select
import ssl
import threading
import time
import traceback

import pika
import pymongo
import requests
import socketio
from botocore.auth import S3SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

ROOT=Path('/installation');PROOF=Path('/proof')
fixture=json.loads((PROOF/'fixture.json').read_text())
CA=str(ROOT/'pki/ca/ca.crt')
os.environ['SSL_CERT_FILE']=CA;os.environ['REQUESTS_CA_BUNDLE']=CA
lock=threading.Lock();halt=threading.Event();rows={};held={};contexts={};threads=[]

def value(name):return (ROOT/'values'/name).read_text().strip()
def context(peer=None):
 c=ssl.create_default_context(cafile=CA)
 if peer:c.load_cert_chain(ROOT/'pki/services'/peer/'service.crt',ROOT/'pki/services'/peer/'service.key')
 return c

def mark(name,success,error=None):
 with lock:
  row=rows.setdefault(name,{'successes':0,'last_success_ns':None,'first_cut_ns':None})
  if success:row['successes']+=1;row['last_success_ns']=time.time_ns()
  elif row['first_cut_ns'] is None:row['first_cut_ns']=time.time_ns();row['error_type']=type(error).__name__

def repeat(name,setup,step,close=lambda c:None):
 conn=None
 try:
  conn=setup()
  while not halt.is_set():
   step(conn);mark(name,True);time.sleep(.075)
 except Exception as error:
  mark(name,False,error)
  with lock:rows[name]['trace']=[{'function':f.name,'line':f.lineno} for f in traceback.extract_tb(error.__traceback__)];rows[name]['attribute']=getattr(error,'name',None)
 finally:
  if conn is not None:
   try:close(conn)
   except Exception:pass

def start(name,setup,step,close=lambda c:None):
 thread=threading.Thread(target=repeat,args=(name,setup,step,close),daemon=True);thread.start();threads.append(thread)

def http_setup(name,host,port,peer=None):
 ctx=context(peer);contexts[name]=(ctx,host,port)
 conn=http.client.HTTPSConnection(host,port,context=ctx,timeout=.75);conn.connect()
 rows.setdefault(name,{'successes':0,'last_success_ns':None,'first_cut_ns':None})['socket_identity']=id(conn.sock)
 held[name]=conn.sock.session
 return conn

def http_step(conn):
 name='http-internal' if conn.host=='api_gateway' else 'https-public'
 if conn.sock is None or id(conn.sock)!=rows[name]['socket_identity']:raise RuntimeError('persistent_http_socket_changed')
 conn.request('GET','/users/x' if conn.host=='api_gateway' else '/',headers={'Connection':'keep-alive'})
 response=conn.getresponse()
 transport_socket=conn.sock or getattr(getattr(response.fp,'raw',None),'_sock',None)
 if transport_socket is not None and getattr(transport_socket,'_sslobj',None) is not None:held['http-internal' if conn.host=='api_gateway' else 'https-public']=transport_socket.session
 response.read()
 if response.status not in (200,400,401,403):raise RuntimeError('unexpected_http_control')
 if conn.sock is not None and getattr(conn.sock,'_sslobj',None) is not None:held['http-internal' if conn.host=='api_gateway' else 'https-public']=conn.sock.session

def s3_step(conn):
 credentials=Credentials(value('s3_img_storage_access'),value('s3_img_storage_secret'))
 request=AWSRequest(method='HEAD',url='https://seaweedfs:9000/picturas')
 S3SigV4Auth(credentials,'s3','us-east-1').add_auth(request)
 conn.request('HEAD','/picturas',headers={**dict(request.headers),'Connection':'keep-alive'})
 response=conn.getresponse();response.read()
 if response.status!=200:raise RuntimeError('s3_positive_failed')
 if conn.sock is not None:held['s3']=conn.sock.session

def amqp_setup():
 ctx=context();contexts['amqp']=(ctx,'rabbitmq',5671)
 c=pika.BlockingConnection(pika.ConnectionParameters('rabbitmq',5671,
  credentials=pika.PlainCredentials('video_tool',value('rabbit_video_tool')),
  ssl_options=pika.SSLOptions(ctx,'rabbitmq'),heartbeat=0,socket_timeout=.75,connection_attempts=1))
 return c,c.channel()

def mongo_setup():
 return pymongo.MongoClient('projects_mongoDB',27018,username='projects_svc',password=value('mongo_projects_service'),
  authSource='admin',tls=True,tlsCAFile=CA,maxPoolSize=1,minPoolSize=1,heartbeatFrequencyMS=500,
  serverSelectionTimeoutMS=500,connectTimeoutMS=500,socketTimeoutMS=500)

def grpc_setup():
 ctx=context('seaweedfs');ctx.set_alpn_protocols(['h2']);contexts['grpc']=(ctx,'seaweedfs',19000)
 c=ctx.wrap_socket(socket.create_connection(('seaweedfs',19000),timeout=.75),server_hostname='seaweedfs')
 c.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n'+b'\x00\x00\x00\x04\x00\x00\x00\x00\x00')
 grpc_step(c)
 held['grpc']=c.session
 return c

def recv_exact(conn,count):
 data=b''
 while len(data)<count:
  chunk=conn.recv(count-len(data))
  if not chunk:raise EOFError('peer_closed')
  data+=chunk
 return data

grpc_primed=set()
def grpc_step(conn):
 if id(conn) in grpc_primed:
  if not conn.pending() and not select.select([conn],[],[],.01)[0]:return
  head=recv_exact(conn,9);body=recv_exact(conn,int.from_bytes(head[:3],'big'))
  if head[3]==6 and not head[4]&1:conn.sendall(b'\x00\x00\x08\x06\x01\x00\x00\x00\x00'+body)
  if head[3]==7:raise EOFError('grpc_goaway')
  return
 payload=b'PKIPILOT'
 conn.sendall(b'\x00\x00\x08\x06\x00\x00\x00\x00\x00'+payload)
 while True:
  head=recv_exact(conn,9);body=recv_exact(conn,int.from_bytes(head[:3],'big'))
  if head[3]==4 and not head[4]&1:conn.sendall(b'\x00\x00\x00\x04\x01\x00\x00\x00\x00')
  if head[3]==6 and head[4]&1 and body==payload:break
 held['grpc']=conn.session
 grpc_primed.add(id(conn))

try:
 start('http-internal',lambda:http_setup('http-internal','api_gateway',8000,'nginx'),http_step,lambda c:c.close())
 start('https-public',lambda:http_setup('https-public','nginx',443),http_step,lambda c:c.close())
 start('s3',lambda:http_setup('s3','seaweedfs',9000),s3_step,lambda c:c.close())
 start('amqp',amqp_setup,lambda c:c[1].queue_declare(queue='video_queue',passive=True),lambda c:c[0].close())
 start('mongo',mongo_setup,lambda c:c.project.processes.find_one({'msg_id':'technical-observer-no-result'}),lambda c:c.close())
 start('grpc',grpc_setup,grpc_step,lambda c:c.close())
 http_session=requests.Session();http_session.trust_env=False;http_session.verify=CA
 ws=socketio.Client(http_session=http_session,reconnection=False)
 ws.on('disconnect',lambda:mark('websocket',False,EOFError()))
 ws.on('video-progress',lambda data:mark('video-progress',True))
 ws.connect('https://nginx',auth={'token':fixture['token']},transports=['websocket'])
 ack=ws.call('join-project',{'projectId':fixture['project'],'access':{'kind':'owner'}},timeout=3)
 if ack.get('status')!='joined':raise RuntimeError('owner_join_failed')
 mark('websocket',True)
 deadline=time.monotonic()+12
 while time.monotonic()<deadline:
  with lock:prepared=all(rows.get(k,{}).get('successes',0)>=3 and rows[k]['first_cut_ns'] is None for k in ['http-internal','https-public','s3','amqp','mongo','grpc'])
  if prepared:break
  time.sleep(.1)
 if not prepared:raise RuntimeError('persistent_preconditions_failed')
 # Explicit SSL-session objects for every TLS endpoint, held in memory only.
 for name,host,port,peer in [('mongo-session','projects_mongoDB',27018,None),('amqp-session','rabbitmq',5671,None)]:
  ctx=context(peer);contexts[name]=(ctx,host,port)
  with ctx.wrap_socket(socket.create_connection((host,port),timeout=1),server_hostname=host) as conn:
   conn.settimeout(.25)
   try:conn.recv(1)
   except socket.timeout:pass
   held[name]=conn.session
 (PROOF/'ready.json').write_text(json.dumps({'prepared':True,'at_ns':time.time_ns(),'rows':rows}));(PROOF/'ready.json').chmod(0o600)
 while not (PROOF/'cut-complete').exists():
  with lock:already_cut=all(rows.get(k,{}).get('first_cut_ns') for k in ['http-internal','https-public','s3','amqp','mongo','grpc','websocket'])
  if already_cut:break
  time.sleep(.05)
 deadline=time.monotonic()+4
 while time.monotonic()<deadline:
  with lock:cut=all(rows.get(k,{}).get('first_cut_ns') for k in ['http-internal','https-public','s3','amqp','mongo','grpc','websocket'])
  if cut:break
  time.sleep(.05)
 halt.set()
 for thread in threads:thread.join(timeout=2)
 # The read-only shared-volume witness is independent of Docker/PID inspection.
 effect_path=Path('/images/pki-fixture')/fixture['message_id']
 def effects():
  return [{'name':p.name,'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
          for p in sorted(effect_path.glob('output*')) if p.is_file()]
 samples=[]
 for _ in range(4):samples.append({'at_ns':time.time_ns(),'files':effects()});time.sleep(.1)
 stable=bool(samples[0]['files']) and all(s['files']==samples[0]['files'] for s in samples)
 state=json.loads((ROOT/'maintenance'/json.loads((ROOT/'fixture-installation.json').read_text())['project']/'state.json').read_text())
 snapshot={'operation':state['operation'],'all_persistent_cut':bool(cut) and stable,'rows':rows,'at_ns':time.time_ns(),
           'local_effects':{'stable_after_cut':stable,'samples':samples}}
 (PROOF/'cut.json').write_text(json.dumps(snapshot));(PROOF/'cut.json').chmod(0o600)
 while not (PROOF/'stop').exists():
  state=json.loads((ROOT/'maintenance'/json.loads((ROOT/'fixture-installation.json').read_text())['project']/'state.json').read_text())
  if state.get('ca_changed') and state.get('phase') in ('verifying_isolated','verified_admissions_closed'):break
  time.sleep(.1)
 if not (PROOF/'stop').exists():
  resume=[]
  for name,session in held.items():
   ctx,host,port=contexts[name]
   try:
    with ctx.wrap_socket(socket.create_connection((host,port),timeout=2),server_hostname=host,session=session) as conn:
     conn.sendall(b'GET / HTTP/1.1\r\nHost: fixture\r\nConnection: close\r\n\r\n');conn.recv(1024)
     result={'name':name,'refused':False,'resumed':conn.session_reused}
   except ssl.SSLError as error:result={'name':name,'refused':True,'tls_reason':getattr(error,'verify_code',None) or getattr(error,'reason',None)}
   except Exception as error:result={'name':name,'refused':False,'error_type':type(error).__name__}
   result.update(has_ticket=session.has_ticket,session_age_seconds=time.time()-session.time,session_timeout_seconds=session.timeout)
   resume.append(result)
  valid_ticket=any(r['has_ticket'] and r['session_age_seconds']<r['session_timeout_seconds'] for r in resume)
  current_ca=hashlib.sha256(ssl.PEM_cert_to_DER_cert((ROOT/'pki/ca/ca.crt').read_text())).hexdigest()
  (PROOF/'resumption.json').write_text(json.dumps({'operation':state['operation'],'new_ca':current_ca,'all_persistent_cut':bool(cut),'valid_old_ticket_tested':valid_ticket,'all_refused':all(r['refused'] for r in resume),'rows':resume}));(PROOF/'resumption.json').chmod(0o600)
 ws.disconnect()
 print(json.dumps({'observer':'complete','persistent_types':7,'secrets_reported':False}))
except Exception as error:
 halt.set();(PROOF/'failure.json').write_text(json.dumps({'error_type':type(error).__name__,
  'control':str(error) if isinstance(error,RuntimeError) else None,'rows':rows}));(PROOF/'failure.json').chmod(0o600)
 print(json.dumps({'observer':'failed','error_type':type(error).__name__}));raise SystemExit(1)
