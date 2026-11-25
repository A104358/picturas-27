"""Actual application + owner WSS after retirement, with isolated NSS trust."""
import hashlib,json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from pilot_paths import ROOT,PROJECT,PROFILE,CACHE
identity=json.loads((ROOT/'pilot/identity.json').read_text())
state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
assert state['phase']=='reopened'
session={'user':{'_id':identity['user'],'type':'anonymous','operations':[]},'token':identity['token']}
with sync_playwright() as p:
 browser=p.firefox.launch_persistent_context(str(PROFILE),headless=False,ignore_https_errors=False,
  firefox_user_prefs={'security.enterprise_roots.enabled':False})
 browser.add_init_script('localStorage.setItem("session",'+json.dumps(json.dumps(session))+');')
 page=browser.new_page();observed={'wss':False,'fresh_owner_join':False}
 def socket(ws):
  if ws.url.startswith('wss://localhost:8080/socket.io'):
   observed['wss']=True
   ws.on('framereceived',lambda frame:observed.update(fresh_owner_join=True) if isinstance(frame,str) and '"status":"joined"' in frame else None)
 page.on('websocket',socket)
 response=page.goto('https://localhost:8080/dashboard/'+identity['project'])
 assert response.status==200
 deadline=time.monotonic()+30
 while time.monotonic()<deadline and not observed['fresh_owner_join']:page.wait_for_timeout(200)
 assert observed['wss'] and observed['fresh_owner_join']
 assert 'B10 technical observer' in page.locator('body').inner_text()
 page.bring_to_front();page.wait_for_timeout(1000)
 screenshot=CACHE/'screenshots'/'B10-real-application.png';page.screenshot(path=str(screenshot))
 value={'origin':'https://localhost:8080','new_ca':state['certificates_loaded']['nginx']['ca'],
  'browser_version':browser.browser.version,'http_status':response.status,'application_visible':True,**observed,
  'isolated_nss_profile':True,'no_warning_override':True,'screenshots_sha256':hashlib.sha256(screenshot.read_bytes()).hexdigest()}
 page.evaluate('localStorage.removeItem("session")');browser.close()
 out=Path(__file__).resolve().parents[3]/'tests/conformance/results/2026-11-24/B10-browser-live.json'
 out.write_text(json.dumps(value,indent=2)+'\n')
 print('PASS real Firefox application, strict new-CA trust and fresh owner WSS join; credentials removed from test profile')
