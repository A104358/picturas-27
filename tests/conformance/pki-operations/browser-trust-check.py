"""Preparatory real NSS/Firefox trust check. This is automated, never a manual receipt."""
from pathlib import Path
import http.server
import os
import ssl
import subprocess
import tempfile
import sys
import threading
from playwright.sync_api import sync_playwright

from pilot_paths import ROOT,PROFILE,CERTUTIL
root=str(ROOT)
profile=PROFILE;profile.mkdir(mode=0o700,exist_ok=True)
certutil=str(CERTUTIL)
for args in [[certutil,'-N','--empty-password','-d','sql:'+str(profile)],
 [certutil,'-A','-n','PictuRAS technical pilot CA','-t','C,,','-d','sql:'+str(profile),'-i',root+'/pki/ca/ca.crt']]:
 subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  body=b'<title>PictuRAS PKI technical fixture</title><h1>Controlled TLS fixture</h1>'
  self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
server=None
if '--live' not in sys.argv:
 server=http.server.HTTPServer(('127.0.0.1',8080),Handler)
 ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(root+'/pki/services/nginx/service.crt',root+'/pki/services/nginx/service.key')
 server.socket=ctx.wrap_socket(server.socket,server_side=True)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 with sync_playwright() as p:
  browser=p.firefox.launch_persistent_context(str(profile),headless=True,ignore_https_errors=False,
    firefox_user_prefs={'security.enterprise_roots.enabled':False})
  page=browser.new_page();response=page.goto('https://localhost:8080')
  assert response.status==200 and 'PictuRAS' in page.title()
  browser.close()
 print('PASS automated Firefox: isolated NSS CA accepted, no TLS warning override')

except Exception as error:
 print('FAIL automated Firefox trust setup: '+type(error).__name__);raise SystemExit(1)
finally:
 if server:server.shutdown();server.server_close()
