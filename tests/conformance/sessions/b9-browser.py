"""Real Chromium + production UI + real users issuer, synthetic fixtures only.

Run from repo root with Playwright available. No tokens, IDs or URLs in results.
Browser trusts only the installation nginx public key; API TLS verifies its CA.
Private cases/delivery files are created in a mode-0700 /tmp directory.
"""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import ssl
import struct
import zlib
import urllib.parse
import subprocess
import tempfile
import time
import uuid
import urllib.error
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SECRETS = Path(os.environ['PICTURAS_SECRETS_DIR'])
BASE = 'https://localhost:8080'
TLS = ssl.create_default_context(cafile=str(SECRETS / 'pki/ca/ca.crt'))
INSTALL = 'FIXTURE-B9-installation'
DATASET = 'FIXTURE-B9-picturas-dev'
passed = 0

def check(label, value):
    global passed
    if not value:
        raise AssertionError(label)
    passed += 1
    print('PASS ' + label, flush=True)

def api(method, route, token=None, data=None, extra_headers=None):
    headers = {'Content-Type': 'application/json'}
    headers.update(extra_headers or {})
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(BASE + '/api-gateway/' + route, method=method,
        headers=headers, data=json.dumps(data).encode() if data is not None else None)
    try:
        with urllib.request.urlopen(req, context=TLS, timeout=15) as r:
            body = r.read()
            return r.status, json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        e.read()
        return e.code, None

def media_snapshot(uid, pid, token):
    status, images = api('GET', 'projects/' + uid + '/' + pid + '/imgs', token)
    assert status == 200
    result = []
    for item in images:
        url = urllib.parse.urljoin(BASE + '/', item['url'])
        with urllib.request.urlopen(url, context=TLS, timeout=10) as response:
            digest = hashlib.sha256(response.read()).hexdigest()
        result.append((item['_id'], item['name'], digest))
    return result

def upload_fixture(uid, pid, token):
    width = height = 8
    def chunk(kind, payload):
        return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0)) + chunk(b'IDAT',zlib.compress((b'\x00'+b'\x22\x55\x88'*width)*height))+chunk(b'IEND',b'')
    _, project = api('GET','projects/'+uid+'/'+pid,token)
    boundary = 'B9SyntheticBoundary'
    body = ('--'+boundary+'\r\nContent-Disposition: form-data; name="image"; filename="b9.png"\r\nContent-Type: image/png\r\n\r\n').encode()+png+('\r\n--'+boundary+'--\r\n').encode()
    req = urllib.request.Request(BASE+'/api-gateway/projects/'+uid+'/'+pid+'/img',data=body,method='POST',
        headers={'Authorization':'Bearer '+token,'Content-Type':'multipart/form-data; boundary='+boundary,
                 'X-Project-Version':str(project['version'])})
    with urllib.request.urlopen(req,context=TLS,timeout=30) as r:
        assert r.status in (200,201,204)

def issuer(command, file, output=None):
    args = [str(ROOT / 'ops/session-recovery.sh'), 'picturas-dev', command,
        str(file), INSTALL, DATASET]
    if output:
        args.append(output)
    p = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise AssertionError('administrative ' + command + ' failed (details kept private)')
    return json.loads(p.stdout)

def stored(page):
    return page.evaluate('localStorage.getItem("session")')

def seed(page, value):
    page.goto(BASE + '/session-recovery')
    page.evaluate('(s) => s === null ? localStorage.removeItem("session") : localStorage.setItem("session", s)', value)
    page.reload()
    page.get_by_label('Installation reference', exact=True).fill(INSTALL)
    page.get_by_label('Approved anonymous account ID', exact=True).fill(anon['user']['_id'])
    page.get_by_role('checkbox').check()
    page.get_by_label('Recovery file', exact=True).wait_for()
    page.wait_for_function('!document.querySelector("input[type=file]").disabled')

def upload(page, content, filename='recovery.json', mime='application/json'):
    page.get_by_label('Recovery file', exact=True).set_input_files({'name': filename,
        'mimeType': mime, 'buffer': content})

try:
    status, anon = api('POST', 'users/', data={'type': 'anonymous'})
    assert status == 201
    status, other = api('POST', 'users/', data={'type': 'anonymous'})
    assert status == 201
    original = {'user': anon['user'], 'token': anon['jwt']}
    old = json.dumps({**original, 'token': anon['jwt'] + '.invalid'})
    status, project = api('POST', 'projects/' + anon['user']['_id'], anon['jwt'], {'name': 'B9-fixture-preserved'})
    assert status == 201
    upload_fixture(anon['user']['_id'], project['_id'], anon['jwt'])
    before_media = media_snapshot(anon['user']['_id'], project['_id'], anon['jwt'])
    assert len(before_media) == 1
    _, before_user = api('GET', 'users/' + anon['user']['_id'], anon['jwt'])
    _, before_projects = api('GET', 'projects/' + anon['user']['_id'], anon['jwt'])
    with tempfile.TemporaryDirectory(prefix='picturas-b9-case-') as directory:
        os.chmod(directory, 0o700)
        case = json.loads((ROOT / 'docs/templates/anonymous-session-recovery-case.template.json').read_text())
        case.update(template_only=False, case_ref='FIXTURE-B9-case', installation_ref=INSTALL,
            dataset_ref=DATASET, administrator_ref='FIXTURE-admin', browser_profile_ref='FIXTURE-Chromium',
            subject_id=anon['user']['_id'], state='pending_evidence')
        file = Path(directory) / 'case.json'
        file.write_text(json.dumps(case)); file.chmod(0o600)
        inspection = issuer('inspect', file)
        case['evidence'].update(existence_status='verified', source_ref='SYNTHETIC-TEST-ONLY',
            trusted_provenance_basis='Synthetic fixture creation in this test',
            independent_association_basis='Test owns the synthetic browser/account association',
            verified_by='FIXTURE-admin', verified_at='2026-11-24T00:00:00Z',
            account_fingerprint=inspection['account_fingerprint'])
        case['approval'].update(status='approved', approved_by='FIXTURE-admin', approved_at='2026-11-24T00:00:00Z')
        issuer_value = (SECRETS / 'values/jwt_issuer').read_text().strip()
        case['target'].update(issuer=issuer_value, expected_subject_id=anon['user']['_id'],
            controlled_destination_verified_at='2026-11-24T00:00:00Z')
        case['state'] = 'approved'
        file.write_text(json.dumps(case))
        result = issuer('issue', file, 'delivery.json')
        delivery = Path(directory) / 'delivery.json'
        bundle_bytes = delivery.read_bytes()
        bundle = json.loads(bundle_bytes)
        check('AR-02 actual users issuer creates private delivery for the existing account',
            result['state'] == 'issued' and delivery.stat().st_mode & 0o777 == 0o600)
        check('AR-12 journal/status/stdout contain no bearer or HS256 secret',
            bundle['token'] not in file.read_text() and bundle['token'] not in json.dumps(result)
            and (SECRETS / 'values/jwt_hs256').read_text().strip() not in file.read_text()
            and issuer('status', file)['state'] == 'issued')
        status, validated = api('GET', 'users/validate/' + anon['user']['_id'], bundle['token'])
        check('S06 actual emitted JWT validates for the same anonymous subject',
            status == 200 and validated['user']['_id'] == anon['user']['_id'])
        pub = subprocess.run(['openssl', 'x509', '-in', str(SECRETS / 'pki/services/nginx/service.crt'),
            '-pubkey', '-noout'], capture_output=True, check=True).stdout
        der = subprocess.run(['openssl', 'pkey', '-pubin', '-outform', 'DER'], input=pub,
            capture_output=True, check=True).stdout
        pin = base64.b64encode(hashlib.sha256(der).digest()).decode()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=['--ignore-certificate-errors-spki-list=' + pin])
            for initial in [None, old]:
                context = browser.new_context()
                page = context.new_page()
                observations = []
                sockets = []
                authorizations = []
                def on_socket(ws):
                    sockets.append(True)
                    def received(frame):
                        if isinstance(frame,str) and frame.startswith('43') and '[' in frame:
                            try:
                                result=json.loads(frame[frame.index('['):])
                                if result and isinstance(result[0],dict): authorizations.append(result[0].get('status'))
                            except (ValueError,TypeError): pass
                    ws.on('framereceived',received)
                context.on('request', lambda req: observations.append((req.method, req.url)))
                page.on('websocket', on_socket)
                seed(page, initial)
                observations.clear()
                page.wait_for_timeout(300)
                check('AR-09 recovery mount has no registration, old validation or socket (' + ('absent' if initial is None else 'invalid') + ')',
                    not any('/api-gateway/' in url for _, url in observations) and not sockets and stored(page) == initial)
                upload(page, bundle_bytes)
                page.get_by_role('button', name='Confirm import', exact=True).wait_for()
                check('AR-05 candidate remains in memory until explicit confirmation', stored(page) == initial)
                page.get_by_role('button', name='Confirm import', exact=True).click()
                page.get_by_role('button', name='Continue and reconnect', exact=True).wait_for()
                imported = json.loads(stored(page))
                check('AR-02/06 import preserves subject, server profile and original issuance expiry',
                    imported['user']['_id'] == anon['user']['_id'] and imported['token'] == bundle['token'])
                page.get_by_role('button', name='Continue and reconnect', exact=True).click()
                page.wait_for_url('**/dashboard')
                page.wait_for_timeout(500)
                check('AR-11 normal bootstrap resumes with the imported identity',
                    json.loads(stored(page))['token'] == bundle['token'] and not any(method == 'POST' and url.endswith('/users/') for method,url in observations))
                page.goto(BASE+'/dashboard/'+project['_id'])
                deadline=time.monotonic()+8
                while 'joined' not in authorizations and time.monotonic()<deadline: page.wait_for_timeout(100)
                check('AR-11 imported session obtains a fresh owner room authorization over wss','joined' in authorizations)
                context.close()

            context = browser.new_context(); page = context.new_page(); seed(page, old)
            # Exact byte limit and +1 through a real file input.
            padded = bundle_bytes + b' ' * (16384 - len(bundle_bytes))
            upload(page, padded + b' ')
            page.locator('main [role=alert]').wait_for()
            check('AR-07 real file +1 boundary is refused without writing', stored(page) == old)
            upload(page, padded)
            page.get_by_role('button', name='Confirm import', exact=True).wait_for()
            check('AR-07 exact 16 KiB file reaches server validation', stored(page) == old)
            # Wrong MIME, schema and other installation signatures.
            for content, mime in [(b'{', 'application/json'), (bundle_bytes, 'text/html'),
                    (json.dumps({**bundle, 'token': bundle['token'] + 'bad'}).encode(), 'application/json')]:
                upload(page, content, mime=mime)
                page.locator('main [role=alert]').wait_for()
                check('AR-05/07 invalid candidate is refused without altering storage', stored(page) == old)
            # Recovery keeps an exclusive Web Lock across validation and confirmation.
            tab = context.new_page(); tab.goto(BASE + '/session-recovery')
            tab.locator('main [role=alert]').wait_for()
            check('AR-10 a second importer cannot obtain the same session lock',
                'Another tab' in tab.locator('main [role=alert]').inner_text())
            # An older client that ignores the lock must invalidate the importer.
            tab.evaluate('localStorage.setItem("session", "changed-by-old-client")')
            page.locator('main [role=alert]').wait_for()
            check('AR-10 uncooperative storage change invalidates pending validation',
                not page.get_by_role('button', name='Confirm import', exact=True).is_visible()
                and stored(page) == 'changed-by-old-client')
            context.close()

            context = browser.new_context(); page = context.new_page()
            other_raw = json.dumps({'user': other['user'], 'token': other['jwt']})
            seed(page, other_raw); upload(page, bundle_bytes)
            page.get_by_role('button', name='Confirm import', exact=True).click()
            page.locator('main [role=alert]').wait_for()
            check('AR-10 another saved subject is never overwritten', stored(page) == other_raw)
            context.close()

            context = browser.new_context(); page = context.new_page(); seed(page, old)
            page.route('**/api-gateway/users/validate/**', lambda route: route.abort())
            upload(page, bundle_bytes); page.locator('main [role=alert]').wait_for()
            check('AR-08 network failure before validation writes nothing', stored(page) == old)
            page.unroute('**/api-gateway/users/validate/**')
            upload(page, bundle_bytes); page.get_by_role('button', name='Confirm import', exact=True).wait_for()
            page.evaluate('() => { Storage.prototype.setItem = function(){ throw new DOMException("fixture", "QuotaExceededError"); }; }')
            page.get_by_role('button', name='Confirm import', exact=True).click(); page.locator('main [role=alert]').wait_for()
            check('AR-08 storage refusal preserves the previous session', stored(page) == old)
            context.close()

            context = browser.new_context(); page = context.new_page(); seed(page, old)
            header, payload, _ = bundle['token'].split('.')
            claims = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
            claims.update(iat=int(time.time()), exp=int(time.time())+3)
            payload = base64.urlsafe_b64encode(json.dumps(claims,separators=(',',':')).encode()).rstrip(b'=').decode()
            signing = (header+'.'+payload).encode()
            key = (SECRETS/'values/jwt_hs256').read_text().strip().encode()
            signature = base64.urlsafe_b64encode(hmac.new(key,signing,hashlib.sha256).digest()).rstrip(b'=').decode()
            short_bundle = {**bundle,'token':header+'.'+payload+'.'+signature}
            upload(page,json.dumps(short_bundle).encode())
            page.get_by_role('button',name='Confirm import',exact=True).wait_for()
            page.wait_for_timeout(3200)
            page.get_by_role('button',name='Confirm import',exact=True).click()
            page.locator('main [role=alert]').wait_for()
            check('AR-06 expired candidate is revalidated and refused at confirmation',stored(page)==old)
            context.close()

            context = browser.new_context(); page = context.new_page(); seed(page, old)
            page.goto(BASE + '/dashboard')
            page.get_by_text('Your session needs attention', exact=True).wait_for()
            check('SEC-01 rejected stored session displays an explicit choice without replacement', stored(page) == old)
            page.get_by_role('link', name='Sign in', exact=True).click()
            page.get_by_role('button', name='Login', exact=True).wait_for()
            check('SEC-01 sign-in remains reachable from a rejected session', stored(page) == old)
            context.close()
            context = browser.new_context(); page = context.new_page()
            seed(page,json.dumps({'user':validated['user'],'token':bundle['token']}))
            saved = stored(page)
            page.route('**/api-gateway/users/validate/**', lambda route: route.abort())
            page.goto(BASE+'/dashboard')
            page.get_by_text('Cannot check your session',exact=True).wait_for()
            check('SEC-02 ordinary bootstrap network failure preserves the saved identity',stored(page)==saved)
            page.unroute('**/api-gateway/users/validate/**')
            page.get_by_role('button',name='Retry',exact=True).click()
            page.get_by_text('Cannot check your session',exact=True).wait_for(state='hidden')
            check('SEC-02 retry resumes the same identity without registration',stored(page)==saved)
            context.close()

            context = browser.new_context(); page = context.new_page(); seed(page,old)
            registrations=[]
            context.on('request',lambda req: registrations.append(True) if req.method=='POST' and req.url.endswith('/api-gateway/users/') else None)
            page.goto(BASE+'/dashboard')
            page.get_by_text('Your session needs attention',exact=True).wait_for()
            page.wait_for_timeout(200)
            check('SEC-01 rejection never registers automatically',not registrations and stored(page)==old)
            page.on('dialog',lambda dialog: dialog.accept())
            page.get_by_role('button',name='Start a new anonymous session',exact=True).click()
            page.wait_for_function('(old) => localStorage.getItem("session") !== old',arg=old)
            check('SEC-01 new anonymous identity requires explicit action and registers once',
                len(registrations)==1 and json.loads(stored(page))['user']['_id']!=anon['user']['_id'])
            context.close()

            email='b9-browser-'+uuid.uuid4().hex+'@fixture.invalid';password='Synthetic-'+uuid.uuid4().hex
            code, registered=api('POST','users/',data={'type':'free','name':'B9 fixture browser','email':email,'password':password})
            assert code==201
            context=browser.new_context();page=context.new_page()
            page.goto(BASE+'/login');page.get_by_label('Email',exact=True).fill(email)
            page.get_by_label('Password',exact=True).fill(password)
            page.get_by_role('button',name='Login',exact=True).click();page.wait_for_url('**/dashboard')
            page.locator('[data-sidebar="menu-button"]').filter(has_text='B9 fixture browser').click()
            page.get_by_role('menuitem',name='Logout',exact=True).click()
            page.get_by_text('Welcome to PictuRAS',exact=True).wait_for()
            check('SEC-02 explicit logout clears local bearer without anonymous registration',stored(page) is None)
            check('SEC-02 server copy remains valid after logout (declared limitation)',
                api('GET','users/validate/'+registered['user']['_id'],registered['jwt'])[0]==200)
            context.close()
            browser.close()
        _, after_user = api('GET', 'users/' + anon['user']['_id'], bundle['token'])
        _, after_projects = api('GET', 'projects/' + anon['user']['_id'], bundle['token'])
        # Project GET heartbeats may update presence, so compare stable domain fields.
        check('F06 recovery preserves quota and account profile', before_user == after_user)
        check('F06 recovery preserves project identities and owner access',
            [(p['_id'],p['name']) for p in before_projects] == [(p['_id'],p['name']) for p in after_projects])
        check('F06 media references and actual bytes are preserved', before_media == media_snapshot(anon['user']['_id'], project['_id'], bundle['token']))
        print('B9 browser: ' + str(passed) + ' checks passed', flush=True)
except Exception as error:
    # Playwright/HTTP exceptions can include uploaded buffers or headers.
    import traceback
    frames = traceback.extract_tb(error.__traceback__)
    print('FAIL B9 browser: ' + (str(error) if type(error) is AssertionError else type(error).__name__) + ' at ' + ','.join(str(f.lineno) for f in frames if f.filename == __file__), flush=True)
    if type(error).__name__ in ('Error','TimeoutError'):
        first = str(error).splitlines()[0]
        if len(first) < 250 and not any(marker in first for marker in ('eyJ','Bearer','token','[','{')):
            print('Browser diagnostic: ' + first, flush=True)
    raise SystemExit(1)
