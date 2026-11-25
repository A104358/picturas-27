"""Probe the actual private Seaweed listeners in its network namespace.

Only this trusted harness shares the namespace. Other service containers cannot
reach these loopback listeners (independently checked by the normal network probe).
"""
import hashlib,json,socket,ssl,sys
from pathlib import Path
sys.path.insert(0,'/ops')
import maintenance_probe as p
state=json.loads(Path('/state/state.json').read_text())
old=p.ROOT/state['pki_change']['old_archive_relative']
expected=p.fingerprint(p.ROOT/'pki/services/seaweedfs/service.crt')
rows=[]
def observe(port,ctx,http):
 try:
  with ctx.wrap_socket(socket.create_connection(('127.0.0.1',port),timeout=2),server_hostname='seaweedfs') as tls:
   peer=hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest()
   if http:
    tls.sendall(b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
    data=tls.recv(1024)
    return {'result':'http' if data.startswith(b'HTTP/') else 'closed','peer':peer,
            'status':int(data.split(b' ')[1]) if data.startswith(b'HTTP/') else None}
   tls.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n'+b'\x00\x00\x00\x04\x00\x00\x00\x00\x00')
   data=tls.recv(9)
   return {'result':'h2' if len(data)==9 and data[3]==4 else 'closed','peer':peer}
 except ssl.SSLError as error:return {'result':'tls_refused','reason':getattr(error,'verify_code',None) or getattr(error,'reason',None)}
 except OSError as error:return {'result':'unavailable','error_type':type(error).__name__}
def check(channel,case,result,passed):rows.append({'channel':channel,'case':case,'observation':result,'passed':bool(passed)})
for role,port,http in [('master-https',9333,True),('volume-https',8080,True),('filer-https',8888,True),
                       ('master-grpc',19333,False),('volume-grpc',18080,False),('filer-grpc',18888,False),('s3-grpc',19000,False)]:
 channel='seaweedfs loopback '+role
 current=p.ctx('seaweedfs');current.set_alpn_protocols(['h2'] if not http else ['http/1.1'])
 positive=observe(port,current,http)
 check(channel,'current actual internal TLS listener',positive,positive.get('peer')==expected and positive['result'] in ('http','h2'))
 missing=observe(port,p.ctx(),http)
 check(channel,'no client certificate refused',missing,missing['result']=='tls_refused')
 obsolete=observe(port,p.ctx('seaweedfs',ca=old/'ca/ca.crt'),http)
 check(channel,'withdrawn server CA refused',obsolete,obsolete['result']=='tls_refused')
 obsolete_client=observe(port,p.ctx('seaweedfs',certroot=old),http)
 check(channel,'withdrawn client certificate refused',obsolete_client,obsolete_client['result']=='tls_refused')
print(json.dumps({'passed':all(r['passed'] for r in rows),'rows':rows}))
