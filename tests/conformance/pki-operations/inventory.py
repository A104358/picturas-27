"""Collect public runtime/image/certificate evidence; never inspect environment values."""
import concurrent.futures,hashlib,json,os,platform,subprocess
from pathlib import Path
from pilot_paths import ROOT,PROJECT,CACHE
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'tests/conformance/results/2026-11-24/B10-runtime-manifest.json'
def run(args):
 p=subprocess.run(args,capture_output=True,timeout=30)
 return p
ids=run(['docker','ps','-aq','--filter','label=com.docker.compose.project='+PROJECT]).stdout.decode().split()
items=json.loads(run(['docker','inspect',*ids]).stdout)
node_code='''const out={runtime:process.versions,libraries:{}};for(const p of ['express','axios','amqplib','mongoose','aws-sdk','next','socket.io','socket.io-client']){try{out.libraries[p]=require(p+'/package.json').version}catch{}}console.log(JSON.stringify(out));'''
python_code='''import sys,ssl,json,importlib.metadata as m
out={'runtime':sys.version,'ssl':ssl.OPENSSL_VERSION,'libraries':{}}
for p in ['pika','Pillow','requests','Flask','Werkzeug','cryptography','faster-whisper']:
 try:out['libraries'][p]=m.version(p)
 except m.PackageNotFoundError:pass
print(json.dumps(out))'''
def collect(item):
 service=item['Config']['Labels']['com.docker.compose.service']
 image=json.loads(run(['docker','image','inspect',item['Image']]).stdout)[0]
 out={'service':service,'image_id':item['Image'],'repo_digests':image.get('RepoDigests',[]),
      'container_id':item['Id'],'pid':item['State']['Pid'],'started_at':item['State']['StartedAt']}
 if service in ['frontend','api_gateway','projects','users','subscriptions','img_storage','ws_gateway','s3-bootstrap']:
  args=['node','-e',node_code]
 elif service in ['rabbitmq']:args=['rabbitmq-diagnostics','server_version','--quiet']
 elif service.endswith('_mongoDB'):args=['mongod','--version']
 elif service=='seaweedfs':args=['weed','version']
 elif service=='nginx':args=['nginx','-V']
 elif service=='mongo-backup':args=['mongodump','--version']
 else:args=['python','-c',python_code]
 p=run(['docker','exec',item['Id'],*args] if item['State']['Running'] else
       ['docker','run','--rm','--network','none','--entrypoint',args[0],item['Image'],*args[1:]])
 value=(p.stdout+p.stderr).decode().strip()
 try:value=json.loads(value)
 except ValueError:pass
 out['versions']=value;out['version_command_exit']=p.returncode
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:services=list(pool.map(collect,items))
hardware=json.loads(run(['docker','info','--format','{{json .}}']).stdout)
firefox=run([str(CACHE/'.venv/bin/python'),'-c',
 'from playwright.sync_api import sync_playwright\nwith sync_playwright() as p:\n b=p.firefox.launch();print(b.version);b.close()'])
state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
value={'project':PROJECT,'commit':state['commit'],'working_tree':'B10 uncommitted',
 'host':{'os':platform.system(),'architecture':platform.machine(),'python':platform.python_version(),'cpu_count':hardware['NCPU'],'memory_bytes':hardware['MemTotal'],
         'docker':hardware['ServerVersion']},
 'browser':{'engine':'Firefox Playwright isolated NSS','version':firefox.stdout.decode().strip(),'version_command_exit':firefox.returncode},
 'services':sorted(services,key=lambda p:p['service']),'certificates':state['certificates_loaded']}
value['verification_images']={}
for tag in ['picturas-maintenance-probe','picturas-pki-observer']:
 img=json.loads(run(['docker','image','inspect',tag]).stdout)[0]
 value['verification_images'][tag]={'image_id':img['Id'],'repo_digests':img.get('RepoDigests',[])}
value['source_sha256']={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest()
 for folder in ['ops','tests/conformance/pki-operations'] for p in (REPO/folder).iterdir() if p.is_file()}
OUT.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'runtime_services':len(services),'version_failures':sum(p['version_command_exit']!=0 for p in services),'public_manifest':str(OUT.relative_to(REPO))}))
