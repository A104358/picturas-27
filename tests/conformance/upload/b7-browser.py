"""Real UI upload: image, video, rejected free limit, premium and mid-transfer cancel."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import struct
import tempfile
import time
import urllib.error
import urllib.request
import uuid
import zlib

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
BASE = "https://localhost:8080"
SECRETS = Path(os.environ["PICTURAS_SECRETS_DIR"])
TLS = ssl.create_default_context(cafile=str(SECRETS / "pki/ca/ca.crt"))


def api(method, route, token=None, data=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(BASE + "/api-gateway/" + route, method=method,
        headers=headers, data=json.dumps(data).encode() if data is not None else None)
    try:
        with urllib.request.urlopen(request, context=TLS, timeout=30) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        error.read()
        return error.code, None


def count_media(uid, pid, token):
    status, images = api("GET", f"projects/{uid}/{pid}/imgs", token)
    assert status == 200, status
    return len(images)


def wait_media(uid, pid, token, expected):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if count_media(uid, pid, token) == expected:
            return
        time.sleep(0.2)
    raise AssertionError("Media count did not reach expected value")


def choose(page, path):
    page.get_by_role("button", name="Import", exact=True).click()
    page.locator('input[type="file"]').set_input_files(path)
    page.get_by_role("button", name="Add", exact=True).click()


status, account = api("POST", "users/", data={
    "name": "B7 browser", "email": f"b7-browser-{uuid.uuid4().hex}@example.invalid",
    "password": uuid.uuid4().hex, "type": "free",
})
assert status == 201, status
uid, token = account["user"]["_id"], account["jwt"]
status, project = api("POST", f"projects/{uid}", token, {"name": "B7 browser"})
assert status == 201, status
pid = project["_id"]
pub = subprocess.run(["openssl", "x509", "-in", str(SECRETS / "pki/services/nginx/service.crt"),
    "-pubkey", "-noout"], capture_output=True, check=True).stdout
der = subprocess.run(["openssl", "pkey", "-pubin", "-outform", "DER"],
    input=pub, capture_output=True, check=True).stdout
pin = base64.b64encode(hashlib.sha256(der).digest()).decode()

with tempfile.TemporaryDirectory(prefix="picturas-b7-browser-") as directory:
    os.chmod(directory, 0o700)
    png = Path(directory) / "fixture.png"
    invalid = Path(directory) / "invalid.txt"
    invalid.write_text("not media")
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(
            ">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    png.write_bytes(b"\x89PNG\r\n\x1a\n" +
        chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 0)) +
        chunk(b"IDAT", zlib.compress((b"\x00" + b"\x22\x55\x88" * 8) * 8)) +
        chunk(b"IEND", b""))
    large = Path(directory) / "cancel.mp4"
    with (ROOT / "samples/video/sample_10s_720p.mp4").open("rb") as source, large.open("wb") as target:
        shutil.copyfileobj(source, target)
        target.truncate(50 * 1024 * 1024)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True,
            args=["--ignore-certificate-errors-spki-list=" + pin])
        context = browser.new_context()
        page = context.new_page()
        responses = []
        page.on("response", lambda response: responses.append((response.request.method,
            response.url.split("?", 1)[0].split("/")[-1], response.status)))
        page.goto(BASE + "/login")
        page.evaluate("(value) => localStorage.setItem('session', value)",
            json.dumps({"user": account["user"], "token": token}))
        page.goto(BASE + "/dashboard/" + pid)
        page.get_by_role("button", name="Import", exact=True).wait_for(timeout=20000)

        page.get_by_role("button", name="Import", exact=True).click()
        page.locator('input[type="file"]').set_input_files(str(invalid))
        page.get_by_text("Invalid file type!").wait_for(timeout=10000)
        page.get_by_role("dialog").get_by_role("button", name="Close").click()
        assert count_media(uid, pid, token) == 0
        print("PASS UI invalid file rejected")

        choose(page, str(png))
        wait_media(uid, pid, token, 1)
        print("PASS UI image upload")

        choose(page, str(ROOT / "samples/video/sample_10s_720p.mp4"))
        wait_media(uid, pid, token, 2)
        page.wait_for_timeout(500)
        assert any(method == "PUT" and status in (200, 201, 204) for method, _, status in responses)
        assert any(method == "POST" and name == "confirm" and status == 204
            for method, name, status in responses)
        print("PASS UI video PUT and confirmation")

        before = len(responses)
        choose(page, str(ROOT / "samples/video/too_long_90s.mp4"))
        page.wait_for_timeout(1200)
        assert any(method == "POST" and name == "uploads" and status == 400
            for method, name, status in responses[before:])
        assert count_media(uid, pid, token) == 2
        print("PASS UI free duration limit")
        page.get_by_role("dialog").get_by_role("button", name="Close").click()

        card = {"cardHolderName": "B7 Fixture", "cardNumber": "4242424242424242",
            "expiryMonth": "12", "expiryYear": "29", "cvc": 123}
        status, _ = api("POST", "subscriptions/", token,
            {"subscription": {"user_id": uid, "interval": 1}, "card": card})
        assert status == 200, status
        page.reload()
        choose(page, str(ROOT / "samples/video/too_long_90s.mp4"))
        wait_media(uid, pid, token, 3)
        print("PASS UI premium duration limit")

        cdp = context.new_cdp_session(page)
        cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 0,
            "downloadThroughput": -1, "uploadThroughput": 512 * 1024})
        for attempt in range(6):
            before = len(responses)
            choose(page, str(large))
            try:
                page.get_by_text("Uploading video:", exact=False).wait_for(timeout=6000)
                break
            except Exception:
                if not any(method == "POST" and name == "uploads" and status == 429
                    for method, name, status in responses[before:]):
                    raise
                page.get_by_role("dialog").get_by_role("button", name="Close").click()
                page.wait_for_timeout(3000)
        else:
            raise AssertionError("Upload slot did not free after background hash")
        page.get_by_role("button", name="Cancel upload").click()
        page.wait_for_timeout(1500)
        assert any(method == "POST" and name == "cancel" and status == 204
            for method, name, status in responses)
        assert count_media(uid, pid, token) == 3
        print("PASS UI cancellation before commit")
        context.close()
        browser.close()
