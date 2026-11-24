"""Real planned-drain and same-CA renewal on the private pilot installation."""
import hashlib,http.client,json,os,socket,ssl,subprocess,time
from pathlib import Path
import requests,socketio

from pilot_paths import ROOT,PROJECT,OVERRIDE
REPO=Path(__file__).resolve().parents[3]
ENV=dict(os.environ,PICTURAS_SECRETS_DIR=str(ROOT))
IDENTITY=json.loads((ROOT/'pilot/identity.json').read_text())
CA=str(ROOT/'pki/ca/ca.crt');ctx=ssl.create_default_context(cafile=CA)
os.environ['SSL_CERT_FILE']=CA;os.environ['REQUESTS_CA_BUNDLE']=CA

def command(args,timeout=600):return subprocess.run(args,cwd=REPO,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
def check(label,condition):
 if not condition:raise RuntimeError(label)
 print('PASS '+label,flush=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inventory():
 ids=command(['docker','ps','-aq','--filter','label=com.docker.compose.project='+PROJECT]).stdout.decode().split()
 return {p['Config']['Labels']['com.docker.compose.service']:p for p in json.loads(command(['docker','inspect',*ids]).stdout)}

try:
 old=inventory();old_ca=sha(ROOT/'pki/ca/ca.crt')
 connection=http.client.HTTPSConnection('localhost',8080,context=ctx,timeout=3)
 connection.request('GET','/');response=connection.getresponse()
 ss=connection.sock or getattr(getattr(response.fp,'raw',None),'_sock',None)
 session=ss.session;response.read()
 if ss._sslobj is not None:session=ss.session
 check('pre-existing TLS session captured',session is not None)
 session_http=requests.Session();session_http.trust_env=False;session_http.verify=CA
 ws=socketio.Client(http_session=session_http,reconnection=False);cut=[]
 ws.on('disconnect',lambda:cut.append(time.time_ns()))
 ws.connect('https://localhost:8080',auth={'token':IDENTITY['token']},transports=['websocket'])
 check('pre-existing authenticated WS',ws.call('join-project',{'projectId':IDENTITY['project'],'access':{'kind':'owner'}},timeout=3)['status']=='joined')
 slow=ctx.wrap_socket(socket.create_connection(('localhost',8080),timeout=2),server_hostname='localhost')
 headers=('POST /api-gateway/projects/'+IDENTITY['user']+'/'+IDENTITY['project']+'/img HTTP/1.1\r\nHost: localhost\r\n'
   'Authorization: Bearer '+IDENTITY['token']+'\r\nContent-Type: application/octet-stream\r\nContent-Length: 16777216\r\n\r\n')
 slow.sendall(headers.encode()+b'\x00'*1024);time.sleep(.3)
 args=['ops/pki.sh','renew','--project',PROJECT,'--service','nginx','--force','--compose-file',str(OVERRIDE)]
 deferred=command(args);state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
 after_defer=inventory()
 check('buffered request body defers maintenance without killing participants',deferred.returncode!=0 and state['phase']=='deferred_busy' and
  all(after_defer[name]['Id']==p['Id'] and after_defer[name]['State']['Running']==p['State']['Running'] for name,p in old.items()))
 control=http.client.HTTPSConnection('localhost',8080,context=ctx,timeout=3);control.request('GET','/');r=control.getresponse();r.read()
 check('new admissions are suspended at nginx',r.status==503);control.close()
 slow.close();time.sleep(.3)
 renewed=command(args)
 if renewed.returncode:
  error=json.loads(renewed.stderr.splitlines()[-1]);raise RuntimeError('renewal_'+error.get('error','failed'))
 state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text());now=inventory()
 check('all real processes and socket contexts are replaced',all(now[n]['Id']!=p['Id'] for n,p in old.items()) and bool(cut))
 check('normal renewal preserves the CA',old_ca==sha(ROOT/'pki/ca/ca.crt'))
 with ctx.wrap_socket(socket.create_connection(('localhost',8080),timeout=3),server_hostname='localhost',session=session) as current:
  current.sendall(b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n');current.recv(1024)
  check('old TLS session is not resumed by the new nginx process',not current.session_reused)
 old_archive=Path(state['pki_change']['old_archive'])
 check('nginx leaf key changed under the same CA',sha(old_archive/'services/nginx/service.key')!=sha(ROOT/'pki/services/nginx/service.key'))
 check('renewal reopens only after complete manifest and controls',state['phase']=='reopened' and state['channel_controls']['passed'])
 # Same-CA renewal deliberately does not revoke the earlier still-valid client certificate.
 test_state=ROOT/'probe-renew';test_state.mkdir(mode=0o700,exist_ok=True)
 relative=str(old_archive.relative_to(ROOT))
 code='import sys;sys.path.insert(0,"/ops");import maintenance_probe as p;from pathlib import Path;r=p.transport("api_gateway",8000,p.ctx("nginx",certroot=p.ROOT/"'+relative+'"));print(__import__("json").dumps({"accepted":r.get("status")==401}))'
 p=command(['docker','run','--rm','--network',PROJECT+'_elk','--user',str(os.getuid())+':'+str(os.getgid()),
  '-v',str(ROOT)+':/installation:ro','-v',str(REPO/'ops')+':/ops:ro','-e','PICTURAS_SECRETS_DIR=/installation',
  'picturas-maintenance-probe','python','-c',code])
 check('previous still-valid client certificate remains valid under the same CA',p.returncode==0 and json.loads(p.stdout)['accepted'])
 ws.disconnect();connection.close()
 print('Planned renewal: all checks passed',flush=True)
except Exception as e:
 print('FAIL planned renewal: '+(str(e) if isinstance(e,RuntimeError) else type(e).__name__),flush=True);raise SystemExit(1)
