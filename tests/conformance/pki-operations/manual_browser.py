"""Prepare native browser pages for interactive visual inspection without overrides.

All participants stay stopped. Only this labelled technical TLS fixture uses 8080.
The private profile's NSS is updated; personal/system trust is never changed.
This program never creates an inspection receipt. Screenshots must be reviewed.
"""
from pathlib import Path
import hashlib
import http.server
import json
import os
import re
import ssl
import subprocess
import sys
import threading
import time
from playwright.sync_api import sync_playwright

from pilot_paths import ROOT,PROJECT,PROFILE,CERTUTIL,CACHE
trial=ROOT/'pilot'/('trial-'+sys.argv[1]);state=json.loads((ROOT/'maintenance'/PROJECT/'state.json').read_text())
profile=PROFILE
certutil=str(CERTUTIL)
certdir=trial/'browser-certificates'
subprocess.run(['python3',str(Path(__file__).with_name('browser_certificates.py')),str(certdir)],check=True,stdout=subprocess.DEVNULL)
for args in [[certutil,'-D','-n','PictuRAS technical pilot CA','-d','sql:'+str(profile)],
 [certutil,'-A','-n','PictuRAS technical pilot CA','-t','C,,','-d','sql:'+str(profile),'-i',str(ROOT/'pki/ca/ca.crt')]]:
 subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
pem=subprocess.run([certutil,'-L','-n','PictuRAS technical pilot CA','-a','-d','sql:'+str(profile)],check=True,capture_output=True).stdout.decode()
new_ca=hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).hexdigest()
assert new_ca==state['certificates_expected']['nginx']['ca']
old=Path(state['pki_change']['old_archive'])
old_ca=hashlib.sha256(ssl.PEM_cert_to_DER_cert((old/'ca/ca.crt').read_text())).hexdigest()
assert old_ca!=new_ca

class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  body=b'<title>PictuRAS PKI CURRENT - technical fixture</title><h1>CURRENT: trusted pilot certificate</h1><p>Technical TLS fixture; no application data.</p>'
  self.send_response(200);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass

class Server(http.server.HTTPServer):allow_reuse_address=True
server=None;thread=None
phase='launch';case=None

def serve(cert,key):
 global server,thread
 if server:server.shutdown();server.server_close();thread.join()
 server=Server(('127.0.0.1',8080),Handler)
 ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.options|=ssl.OP_NO_TICKET
 ctx.load_cert_chain(str(cert),str(key));server.socket=ctx.wrap_socket(server.socket,server_side=True)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()

try:
 with sync_playwright() as p:
  browser=p.firefox.launch_persistent_context(str(profile),headless=False,ignore_https_errors=False,
   firefox_user_prefs={'security.enterprise_roots.enabled':False,'browser.startup.homepage':'about:blank',
    'browser.shell.checkDefaultBrowser':False,'datareporting.healthreport.uploadEnabled':False,
    'toolkit.telemetry.enabled':False})
  cases={};pages={}
  screenshots=CACHE/'screenshots'/('trial-'+sys.argv[1]);screenshots.mkdir(parents=True,exist_ok=True)
  for case,cert,key in [('CURRENT',ROOT/'pki/services/nginx/service.crt',ROOT/'pki/services/nginx/service.key'),
   ('OLD_CA',old/'services/nginx/service.crt',old/'services/nginx/service.key'),
   ('WRONG_NAME',certdir/'wrong_name.crt',certdir/'wrong_name.key'),('EXPIRED',certdir/'expired.crt',certdir/'expired.key')]:
   phase='navigation';serve(cert,key);page=browser.new_page();pages[case]=page
   try:
    response=page.goto('https://localhost:8080/?pki_trial='+sys.argv[1]+'&case='+case,timeout=10000)
    cases[case]={'accepted':True,'http_status':response.status}
   except Exception as error:
    codes=sorted(set(re.findall(r'(?:SEC_ERROR|SSL_ERROR|MOZILLA_PKIX_ERROR)_[A-Z_]+',str(error))))
    cases[case]={'accepted':False,'error_codes':codes}
   phase='bring_to_front';page.bring_to_front()
   if case=='CURRENT':page.locator('h1').wait_for(state='visible')
   page.wait_for_timeout(1000)
   if case!='CURRENT':
    phase='advanced_details'
    button=page.get_by_role('button',name='Advanced',exact=True)
    if button.count() and button.is_visible():button.click(timeout=3000)
    page.wait_for_timeout(300)
   phase='screenshot';page.screenshot(path=str(screenshots/(case+'.png')),timeout=5000)
  serve(ROOT/'pki/services/nginx/service.crt',ROOT/'pki/services/nginx/service.key')
  assert cases['CURRENT'].get('accepted') and cases['CURRENT'].get('http_status')==200
  assert not cases['OLD_CA']['accepted'] and any('ISSUER' in c for c in cases['OLD_CA']['error_codes'])
  assert not cases['WRONG_NAME']['accepted'] and 'SSL_ERROR_BAD_CERT_DOMAIN' in cases['WRONG_NAME']['error_codes']
  assert not cases['EXPIRED']['accepted'] and any('EXPIRED' in c for c in cases['EXPIRED']['error_codes'])
  results={'operation':state['operation'],'new_ca':new_ca,'old_ca':old_ca,'cases':cases,
    'automated_preparation':True,'manual':False,'old_ca_removed':True,'no_warning_override':True,'ready_at_ns':time.time_ns()}
  (trial/'browser-ready.json').write_text(json.dumps(results));(trial/'browser-ready.json').chmod(0o600)
  pages['CURRENT'].bring_to_front()
  print('READY_MANUAL_BROWSER: CURRENT accepted; OLD_CA/WRONG_NAME/EXPIRED refused; inspect the four Firefox tabs without bypassing warnings',flush=True)
  while not (trial/'browser-close').exists():
   browser.pages[0].wait_for_timeout(250)
  browser.close()
  (trial/'browser-closed').touch()
except Exception as error:
 failure={'error_type':type(error).__name__,'phase':phase,'case':case,'at_ns':time.time_ns(),
          'controlled_fixture_diagnostic':str(error)[:1500]}
 history=trial/'browser-failures.json'
 failures=json.loads(history.read_text()) if history.exists() else []
 previous=trial/'browser-failure.json'
 if previous.exists() and not failures:failures.append({**json.loads(previous.read_text()),'at_ns':previous.stat().st_mtime_ns})
 failures.append(failure);history.write_text(json.dumps(failures));history.chmod(0o600)
 (trial/'browser-failure.json').write_text(json.dumps(failure));(trial/'browser-failure.json').chmod(0o600)
 print('Browser preparation failed: '+type(error).__name__,flush=True);raise SystemExit(1)
finally:
 if server:server.shutdown();server.server_close()
