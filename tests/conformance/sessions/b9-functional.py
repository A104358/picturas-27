"""B9 S06/SEC-01/02: synthetic sessions only, actual gateway/users and WS."""
import json
import os
import secrets
import sys
import time
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from b4_common import (AUDIENCE, ISSUER, SESSION_SECRET, SESSION_TYP, BASE, CA, Results, call, register)
import jwt
import requests
import socketio

os.environ['SSL_CERT_FILE'] = CA
os.environ['REQUESTS_CA_BUNDLE'] = CA
res = Results('B9 sessions')
fixture = register('anonymous')
owner, token = fixture['id'], fixture['token']
now = int(time.time())
claims = {'id': owner, 'sub': owner, 'iat': now, 'exp': now + 604800, 'iss': ISSUER, 'aud': AUDIENCE}
for label, change, algorithm, typ, key in [
    ('expired', {'iat': now-604801, 'exp': now-1}, 'HS256', SESSION_TYP, SESSION_SECRET),
    ('old installation secret', {}, 'HS256', SESSION_TYP, secrets.token_hex(32)),
    ('wrong issuer', {'iss':'FIXTURE-wrong'}, 'HS256', SESSION_TYP, SESSION_SECRET),
    ('wrong audience', {'aud':'FIXTURE-wrong'}, 'HS256', SESSION_TYP, SESSION_SECRET),
    ('wrong type', {}, 'HS256', 'JWT', SESSION_SECRET),
    ('wrong algorithm', {}, 'HS512', SESSION_TYP, SESSION_SECRET),
    ('subject mismatch', {'sub':str(uuid.uuid4()).replace('-','')[:24]}, 'HS256', SESSION_TYP, SESSION_SECRET),
    ('over seven days', {'exp':now+604801}, 'HS256', SESSION_TYP, SESSION_SECRET),
    ('future issuance', {'iat':now+60}, 'HS256', SESSION_TYP, SESSION_SECRET),
]:
    candidate = jwt.encode({**claims, **change}, key, algorithm=algorithm, headers={'typ':typ})
    r = call('GET', 'users/validate/' + owner, candidate)
    res.check('S06/AR-05', label, r.status_code, {401,403})
res.check('S06', 'valid positive control', call('GET','users/validate/'+owner,token).status_code,200)
for route in ['users/session-recovery','users/'+owner+'/issue','users/recovery/issue']:
    r=call('POST',route,token,body={'subject_id':owner})
    res.check('AR-12','no public administrative issuer',r.status_code,{401,403,404})

email='b9-'+uuid.uuid4().hex+'@fixture.invalid'
r=call('POST','users/',body={'type':'free','name':'B9 synthetic','email':email,'password':'FixturePassword-1!'})
assert r.status_code==201
uid=r.json()['user']['_id']; registered=r.json()['jwt']
r=call('POST','users/'+uid+'/presets',registered,body={'name':'B9 preserved preset','tools':[
    {'procedure':'brightness','params':{'brightness':1.1}}, {'procedure':'contrast','params':{'contrastFactor':1.1}}]})
assert r.status_code==201
presets_before=call('GET','users/'+uid+'/presets',registered).json()
res.check('SEC-02','registered password update',call('PUT','users/'+uid,registered,body={'password':'FixturePassword-2!'}).status_code,204)
res.check('SEC-02','copied bearer remains valid after password change (declared limitation)',
    call('GET','users/validate/'+uid,registered).status_code,200)
r=call('POST','users/'+email+'/login',body={'password':'FixturePassword-2!'})
res.check('SEC-01','registered account signs in again without replacing account',
    r.status_code==201 and r.json()['user']['_id']==uid,True)
res.check('SEC-02','validation returns same bearer, without refresh',
    call('GET','users/validate/'+uid,registered).json()['token']==registered,True)

res.check('F06','registered reauthentication preserves presets and their tools',
    call('GET','users/'+uid+'/presets',r.json()['jwt']).json()==presets_before,True)

future=jwt.encode({**claims,'iat':int(time.time())+60},SESSION_SECRET,algorithm='HS256',headers={'typ':SESSION_TYP})
future_http=requests.Session();future_http.trust_env=False;future_http.verify=CA
future_ws=socketio.Client(http_session=future_http,reconnection=False)
try:
    future_ws.connect(BASE.removesuffix('/api-gateway/'),auth={'token':future},transports=['websocket'])
    future_connected=future_ws.connected
except Exception:
    future_connected=False
res.check('S06/SEC-02','future issuance is also refused by WS',future_connected,False)
future_ws.disconnect()

# A two-second signed fixture exercises the actual established-connection expiry.
short=jwt.encode({**claims,'iat':int(time.time()),'exp':int(time.time())+2},SESSION_SECRET,
                 algorithm='HS256',headers={'typ':SESSION_TYP})
http=requests.Session();http.trust_env=False;http.verify=CA
ws=socketio.Client(http_session=http,reconnection=False)
ws.connect(BASE.removesuffix('/api-gateway/'),auth={'token':short},transports=['websocket'])
assert ws.connected
limit=time.monotonic()+4
while ws.connected and time.monotonic()<limit: time.sleep(.05)
res.check('SEC-02','established WS disconnects at JWT expiry',ws.connected,False)
ws.disconnect()
res.finish()
