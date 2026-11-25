"""B11 normal Apply/cancel over the public API, with a distinct executor."""
import sys,time
import uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from b4_common import BASE,CA,Results,call,project_version,register,png_bytes

res=Results('B11 Apply and cancellation')
owner,editor=register(),register()
base='projects/'+owner['id']
response=call('POST',base,owner['token'],body={'name':'B11 cancel executor fixture'})
assert response.status_code==201
pid=response.json()['_id'];base+='/'+pid
def headers():return {'X-Project-Version':project_version(owner,pid)}
def mutate(method,suffix,body=None,token=None,query=None):
 return call(method,base+suffix,token or owner['token'],body=body,query=query,headers=headers())
def remaining(account):return call('GET','users/'+account['id'],account['token']).json()['remaining_operations']
sample=Path('/repo/samples/video/sample_10s_720p.mp4')
with sample.open('rb') as stream:
 response=call('POST',base+'/video',owner['token'],headers=headers(),files={'video':('fixture.mp4',stream,'video/mp4')})
res.check('AP01','video admitted without a quota debit',response.status_code,204)
res.check('AP02','owner quota unchanged by upload',remaining(owner),5)
res.check('AP03','video effect configured',mutate('POST','/tool',{'procedure':'brightness','params':{'brightness':1.1}}).status_code,201)
share=mutate('POST','/share',{'permission':'edit'}).json()['id']
query=f"owner={owner['id']}&share={share}"
res.check('AP04','editor explicitly starts the run',mutate('POST','/process',{},editor['token'],query).status_code,201)
res.check('AP05','actual editor is debited',remaining(editor),4)
res.check('AP06','owner is not debited for editor work',remaining(owner),5)
res.check('AP07','owner cancels the editor run',mutate('DELETE','/process').status_code,204)
res.check('AP08','cancellation compensates the original editor',remaining(editor),5)
res.check('AP09','cancellation never credits the owner',remaining(owner),5)
res.check('AP10','repeated explicit cancel does not repeat compensation',mutate('DELETE','/process').status_code,204)
res.check('AP11','editor balance stays unchanged on repeated cancellation',remaining(editor),5)
res.check('AP12','cancelled output is not visible',len(call('GET',base+'/process/url',owner['token']).json()['imgs']),0)
res.check('AP13','new user Apply is required and admitted',mutate('POST','/process',{},editor['token'],query).status_code,201)
rows=[]
for _ in range(240):
 rows=call('GET',base+'/process/url',owner['token']).json()['imgs']
 if rows:break
 time.sleep(.5)
res.check('AP14','exactly one new video result is committed',len(rows),1)
res.check('AP15','new Apply has exactly one new debit',remaining(editor),4)
res.check('AP16','owner balance remains unchanged',remaining(owner),5)
image_project=call('POST','projects/'+owner['id'],owner['token'],body={'name':'B11 server-owned paths'}).json()['_id']
image_base='projects/'+owner['id']+'/'+image_project
def image_headers():return {'X-Project-Version':project_version(owner,image_project)}
response=call('POST',image_base+'/img',owner['token'],headers=image_headers(),files={'image':('fixture.png',png_bytes(),'image/png')})
assert response.status_code==204
response=call('POST',image_base+'/tool',owner['token'],headers=image_headers(),body={'procedure':'resize',
 'params':{'width':16,'height':16,'inputImageURI':'/nonexistent/input.png','outputImageURI':'/tmp/forged-output.png'}})
assert response.status_code==201
res.check('AP17','forged path parameters do not change Apply admission',
 call('POST',image_base+'/process',owner['token'],headers=image_headers(),body={}).status_code,201)
image_rows=[]
for _ in range(120):
 image_rows=call('GET',image_base+'/process/url',owner['token']).json()['imgs']
 if image_rows:break
 time.sleep(.25)
res.check('AP18','worker uses its own run paths despite forged parameters',len(image_rows),1)
if image_rows:
 import requests,struct
 url=image_rows[0]['url'].replace('https://localhost:8080',BASE[:-len('/api-gateway/')])
 session=requests.Session();session.trust_env=False
 data=session.get(url,verify=CA,timeout=30).content
 res.check('AP19','result comes from the legitimate resized source',struct.unpack('>II',data[16:24]),lambda dims:dims==(16,16))
res.check('AP20','password change remains available',call('PUT','users/'+editor['id'],editor['token'],
 body={'password':uuid.uuid4().hex}).status_code,204)
res.check('AP21','password update preserves the current quota',remaining(editor),4)
res.finish()
