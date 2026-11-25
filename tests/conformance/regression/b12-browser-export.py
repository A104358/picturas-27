"""B12 regression: ZIP and PDF export through the real frontend (PDF is built in the browser).

Runs on the host with the stack on https://localhost:8080 and Playwright + Chromium, like
upload/b7-browser.py: the browser trusts only the installation's nginx key (SPKI pin).
  X1 edit mode: "Download images (PDF)" gives a PDF with one page per image
  X2 results mode: "Download results (PDF)" after Apply, one page per result
  X3 results mode ZIP download
  X4 a project with a video hides the PDF entry
No token or signed URL is printed.
"""
import base64
import hashlib
import json
import os
import re
import ssl
import struct
import subprocess
import time
import urllib.error
import urllib.request
import uuid
import zlib
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
BASE = "https://localhost:8080"
SECRETS = Path(os.environ["PICTURAS_SECRETS_DIR"])
TLS = ssl.create_default_context(cafile=str(SECRETS / "pki/ca/ca.crt"))
failures = []


def check(case, label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} {case} {label}{(': ' + str(detail)) if detail != '' else ''}", flush=True)
    if not ok:
        failures.append(case)


def api(method, route, token=None, data=None, raw=None, ctype=None, headers=None):
    h = dict(headers or {})
    if token:
        h["Authorization"] = "Bearer " + token
    body = None
    if data is not None:
        body, h["Content-Type"] = json.dumps(data).encode(), "application/json"
    elif raw is not None:
        body, h["Content-Type"] = raw, ctype
    request = urllib.request.Request(BASE + "/api-gateway/" + route, method=method, headers=h, data=body)
    try:
        with urllib.request.urlopen(request, context=TLS, timeout=120) as response:
            content = response.read()
            try:
                return response.status, json.loads(content) if content else None
            except ValueError:
                return response.status, None
    except urllib.error.HTTPError as error:
        error.read()
        return error.code, None


def png(w, h, seed):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"".join(bytes(((x * 9 + seed) % 256, (y * 5 + seed) % 256, 90)) for x in range(w))
                   for y in range(h))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def multipart(field, name, data, ctype):
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def version(uid, pid, token):
    return str(api("GET", f"projects/{uid}/{pid}", token)[1]["version"])


def pdf_pages(data):
    """Page objects, also inside compressed object streams (pdf-lib writes those)."""
    if not data or not data.startswith(b"%PDF"):
        return -1
    text = data
    for body in re.findall(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            text += zlib.decompress(body)
        except zlib.error:
            pass
    return len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", text))


status, account = api("POST", "users/", data={
    "name": "B12 export", "email": f"b12-export-{uuid.uuid4().hex}@example.invalid",
    "password": uuid.uuid4().hex, "type": "free"})
assert status == 201, status
uid, token = account["user"]["_id"], account["jwt"]
status, project = api("POST", f"projects/{uid}", token, {"name": "B12 export"})
pid = project["_id"]
for n in (1, 2):
    body, ctype = multipart("image", f"x{n}.png", png(40, 30, n * 40), "image/png")
    s, _ = api("POST", f"projects/{uid}/{pid}/img", token, raw=body, ctype=ctype,
               headers={"X-Project-Version": version(uid, pid, token)})
    assert s in (200, 201, 204), s
s, _ = api("POST", f"projects/{uid}/{pid}/tool", token, {"procedure": "brightness", "params": {"brightness": 1.3}},
           headers={"X-Project-Version": version(uid, pid, token)})
assert s in (200, 201, 204), s
s, _ = api("POST", f"projects/{uid}/{pid}/process", token, {}, headers={"X-Project-Version": version(uid, pid, token)})
assert s in (200, 201, 202, 204), s
end = time.monotonic() + 120
while time.monotonic() < end:
    s, body = api("GET", f"projects/{uid}/{pid}/process/url", token)
    if s == 200 and len(body.get("imgs", [])) == 2:
        break
    time.sleep(2)
status, vproject = api("POST", f"projects/{uid}", token, {"name": "B12 export video"})
vpid = vproject["_id"]
body, ctype = multipart("video", "v.mp4", (ROOT / "samples/video/sample_10s_720p.mp4").read_bytes(), "video/mp4")
s, _ = api("POST", f"projects/{uid}/{vpid}/video", token, raw=body, ctype=ctype,
           headers={"X-Project-Version": version(uid, vpid, token)})
assert s == 204, s

pub = subprocess.run(["openssl", "x509", "-in", str(SECRETS / "pki/services/nginx/service.crt"),
                      "-pubkey", "-noout"], capture_output=True, check=True).stdout
der = subprocess.run(["openssl", "pkey", "-pubin", "-outform", "DER"], input=pub,
                     capture_output=True, check=True).stdout
pin = base64.b64encode(hashlib.sha256(der).digest()).decode()


def download(page, item):
    page.get_by_title("Download project").click()
    with page.expect_download(timeout=60000) as info:
        page.get_by_role("menuitem", name=item).click()
    return Path(info.value.path()).read_bytes()


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True, args=["--ignore-certificate-errors-spki-list=" + pin])
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    page.goto(BASE + "/login")
    page.evaluate("(value) => localStorage.setItem('session', value)",
                  json.dumps({"user": account["user"], "token": token}))
    page.goto(BASE + "/dashboard/" + pid)
    page.get_by_title("Download project").wait_for(timeout=20000)
    data = download(page, "Download images (PDF)")
    check("X1", "edit-mode PDF with one page per image", pdf_pages(data) == 2, pdf_pages(data))
    page.goto(BASE + "/dashboard/" + pid + "?mode=results")
    page.get_by_title("Download project").wait_for(timeout=20000)
    data = download(page, "Download results (PDF)")
    check("X2", "results-mode PDF with one page per result", pdf_pages(data) == 2, pdf_pages(data))
    data = download(page, "Download results (ZIP)")
    check("X3", "results-mode ZIP", data[:2] == b"PK", len(data))
    page.goto(BASE + "/dashboard/" + vpid)
    page.get_by_title("Download project").wait_for(timeout=20000)
    page.get_by_title("Download project").click()
    page.get_by_role("menuitem", name="Download media (ZIP)").wait_for(timeout=10000)
    check("X4", "video project hides the PDF entry",
          page.get_by_role("menuitem", name=re.compile("PDF")).count() == 0)
    context.close()
    browser.close()
api("DELETE", f"users/{uid}", token)
print(f"B12 browser export: {'all checks passed' if not failures else 'FAILED ' + ','.join(failures)}")
raise SystemExit(1 if failures else 0)
