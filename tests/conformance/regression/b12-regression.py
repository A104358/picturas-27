"""B12 functional regression (plan §3 B12 point 1, F01-F05), end to end through nginx.

Runs on the stack network: tests/conformance/in-network.sh <project> regression/b12-regression.py
Covers what the block suites do not exercise as one product walk-through:
  R01 accounts: register, login, anonymous session, premium by subscription
  R02 anonymous profile: images only
  R03 image pipeline with the 8 PIL tools, batch Apply on two images, ZIP export
  R04 watermark (derived image)
  R05 the 7 AI tools, one project each (expand_ai generative -> generative-mock over mTLS)
  R06 video: legacy POST and direct flow, trim/speed per video, 3 s preview, batch Apply,
      `video-progress`, `process-update` and `preview-ready` events
  R07 mixed project (image + video)
  R08 subtitles (speech sample)
  R09 frame extraction (count) and contact-sheet preview
  R10 quota: debit only on Apply, refund on cancellation (free profile)
  R11 shares read/edit, member events in the project room, presence, 409, revocation
  R12 presets own and shared
  R13 subscription cancel -> free
  R14 account deletion removes the projects
Only synthetic accounts. No JWT, share id or signed URL is printed.
"""
import io
import json
import os
import struct
import sys
import threading
import time
import uuid
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from b4_common import BASE, CA, Results, direct, internal_token, register  # noqa: E402

os.environ["SSL_CERT_FILE"] = CA
os.environ["REQUESTS_CA_BUNDLE"] = CA
import requests  # noqa: E402
import socketio  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SAMPLES = ROOT / "samples/video"
PUBLIC = BASE[: -len("/api-gateway/")]
res = Results("B12 regression")
http = requests.Session()
http.trust_env = False
http.verify = CA
CARD = {"cardHolderName": "B12 Fixture", "cardNumber": "4242424242424242",
        "expiryMonth": "12", "expiryYear": "29", "cvc": 123}


# ----------------------------------------------------------------------------- helpers
def api(method, path, token=None, query=None, **kw):
    headers = dict(kw.pop("headers", {}))
    if token:
        headers["Authorization"] = "Bearer " + token
    url = BASE + path + (("?" + query) if query else "")
    return http.request(method, url, headers=headers, timeout=kw.pop("timeout", 120), **kw)


def public_url(url):
    for prefix in ("https://localhost:8080", "https://localhost:28080"):
        if url.startswith(prefix):
            return PUBLIC + url[len(prefix):]
    return url


def fetch(url):
    r = http.get(public_url(url), timeout=120)
    return r.content if r.status_code == 200 else None


def png(w, h, seed=0):
    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xffffffff)
    raw = b"".join(b"\x00" + b"".join(bytes((((x + seed) * 5) % 256, ((y + seed) * 7) % 256, (x * y) % 256))
                                       for x in range(w)) for y in range(h))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def image_size(data):
    if not data:
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", data[16:24])
    if data.startswith(b"\xff\xd8"):
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return (w, h)
            i += 2 + length
    return None


def mp4_duration(data):
    """Seconds from the movie header (mvhd) of an MP4."""
    if not data:
        return None
    i = data.find(b"mvhd")
    if i < 0:
        return None
    version = data[i + 4]
    if version == 1:
        timescale, duration = struct.unpack(">IQ", data[i + 24:i + 36])
    else:
        timescale, duration = struct.unpack(">II", data[i + 16:i + 24])
    return round(duration / timescale, 2) if timescale else None


class Project:
    def __init__(self, owner, name, query=None, token=None):
        self.owner, self.query = owner, query
        self.token = token or owner["token"]
        r = api("POST", f"projects/{owner['id']}", owner["token"], json={"name": name})
        assert r.status_code == 201, ("project", r.status_code)
        self.id = r.json()["_id"]
        self.path = f"projects/{owner['id']}/{self.id}"

    def version(self, token=None, query=None):
        return str(api("GET", self.path, token or self.token, query=query or self.query).json()["version"])

    def view(self):
        return api("GET", self.path, self.token, query=self.query).json()

    def call(self, method, sub, token=None, query=None, retry429=True, **kw):
        token, query = token or self.token, query if query is not None else self.query
        for _ in range(60):
            headers = dict(kw.get("headers", {}))
            headers.setdefault("X-Project-Version", self.version(token, query))
            kwargs = {k: v for k, v in kw.items() if k != "headers"}
            if "files_factory" in kwargs:
                kwargs["files"] = kwargs.pop("files_factory")()
            r = api(method, self.path + sub, token, query=query, headers=headers, **kwargs)
            if r.status_code != 429 or not retry429:
                return r
            time.sleep(1)
        return r

    def image(self, data, name):
        return self.call("POST", "/img", files_factory=lambda: {"image": (name, data, "image/png")}).status_code

    def video_legacy(self, sample, name):
        def files():
            return {"video": (name, (SAMPLES / sample).open("rb"), "video/mp4")}
        return self.call("POST", "/video", files_factory=files).status_code

    def video_direct(self, sample, name, duration, width, height, mime="video/mp4"):
        size = (SAMPLES / sample).stat().st_size
        meta = {"name": name, "size": size, "type": mime, "duration": duration, "width": width, "height": height}
        r = self.call("POST", "/video/uploads", json=meta)
        if r.status_code != 201:
            return ("request", r.status_code)
        token, upload = r.json()["token"], r.json()["uploadUrl"].removeprefix("/api-gateway/")
        with (SAMPLES / sample).open("rb") as body:
            put = api("PUT", upload, self.token, data=body,
                      headers={"Content-Length": str(size), "Content-Type": mime}, timeout=300)
        if put.status_code not in (200, 201, 204):
            return ("put", put.status_code)
        return api("POST", self.path + f"/video/uploads/{token}/confirm", self.token, query=self.query).status_code

    def media(self):
        return {m.get("name") or m["og_uri"].rsplit("/", 1)[-1]: m["_id"] for m in self.view()["imgs"]}

    def tool(self, procedure, params, token=None, query=None):
        return self.call("POST", "/tool", token=token, query=query,
                         json={"procedure": procedure, "params": params}).status_code

    def apply(self, token=None, query=None):
        return self.call("POST", "/process", token=token, query=query, json={}).status_code

    def results(self, want, timeout=300):
        end, body = time.monotonic() + timeout, {"imgs": [], "texts": []}
        while time.monotonic() < end:
            r = api("GET", self.path + "/process/url", self.token, query=self.query)
            if r.status_code == 200:
                body = r.json()
                if len(body.get("imgs", [])) + len(body.get("texts", [])) >= want:
                    return body
            time.sleep(2)
        return body


class Socket:
    def __init__(self, token):
        self.events, self.payloads = [], {}
        self.client = socketio.Client(reconnection=False, http_session=http)
        for name in ("process-update", "process-error", "video-progress", "preview-ready", "preview-error",
                     "project-op", "project-updated"):
            self.client.on(name, lambda data=None, _n=name: self._record(_n, data))
        self.client.connect(PUBLIC, transports=["websocket"], auth={"token": token}, wait_timeout=15)

    def _record(self, name, data):
        self.events.append(name)
        self.payloads.setdefault(name, []).append(data)

    def join(self, pid, access):
        return self.client.call("join-project", {"projectId": pid, "access": access}, timeout=5).get("status")

    def wait(self, name, timeout=120, count=1):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if self.events.count(name) >= count:
                return True
            time.sleep(0.2)
        return False

    def close(self):
        self.client.disconnect()


def remaining(acct):
    return api("GET", f"users/{acct['id']}", acct["token"]).json().get("remaining_operations")


# ----------------------------------------------------------------------------- R01 accounts
free = register("free")
r = api("POST", f"users/{free['email']}/login", json={"password": free["password"]})
res.check("R01", "login returns a session", r.status_code in (200, 201) and bool(r.json().get("jwt")), True)
res.check("R01", "session is accepted", api("GET", f"users/{free['id']}", free["token"]).status_code, 200)
res.check("R01", "invalid session refused", api("GET", f"users/{free['id']}", "x.y.z").status_code, {401, 403})
res.check("R01", "free profile starts with 5 operations", remaining(free), 5)
prem = register("free")
r = api("POST", "subscriptions/", prem["token"], json={"subscription": {"user_id": prem["id"], "interval": 1}, "card": CARD})
res.check("R01", "subscribe", r.status_code, 200)
res.check("R01", "subscription makes the profile premium",
          api("GET", f"users/{prem['id']}", prem["token"]).json().get("type"), "premium")
anon = register("anonymous")
res.check("R01", "anonymous session accepted", api("GET", f"users/{anon['id']}", anon["token"]).status_code, 200)

# ----------------------------------------------------------------------------- R02 anonymous
pa = Project(anon, "b12-anon")
res.check("R02", "anonymous uploads an image", pa.image(png(32, 24), "anon.png"), {200, 201, 204})
res.check("R02", "anonymous cannot upload a video (legacy POST)", pa.video_legacy("sample_10s_720p.mp4", "a.mp4"), {400, 403})
res.check("R02", "anonymous cannot request a direct video upload",
          pa.video_direct("sample_10s_720p.mp4", "a2.mp4", 10, 1280, 720), lambda v: v in (("request", 400), ("request", 403)))

# ----------------------------------------------------------------------------- R03 image PIL
p3 = Project(prem, "b12-pil")
for n in (1, 2):
    res.check("R03", f"upload image {n}", p3.image(png(64, 48, n), f"pil{n}.png"), {200, 201, 204})
for procedure, params in (("brightness", {"brightness": 1.2}), ("contrast", {"contrastFactor": 1.3}),
                          ("saturation", {"saturationFactor": 0.5}), ("rotate", {"degrees": 90}),
                          ("resize", {"width": 40, "height": 30}),
                          ("cut", {"left": 2, "top": 2, "right": 38, "bottom": 28}),
                          ("border", {"borderWidth": 3, "r": 255, "g": 0, "b": 0}),
                          ("binarization", {"threshold": 128})):
    res.check("R03", f"add {procedure}", p3.tool(procedure, params), {200, 201, 204})
res.check("R03", "batch Apply (2 images x 8 tools)", p3.apply(), {200, 201, 202, 204})
out = p3.results(2)
sizes = sorted(image_size(fetch(i["url"])) or (0, 0) for i in out["imgs"])
res.check("R03", "both results produced through the 8-step chain", len(out["imgs"]), 2)
res.check("R03", "results reflect resize -> cut -> border (42x32)", sizes, lambda v: v == [(42, 32), (42, 32)])
r = api("GET", p3.path + "/process", prem["token"], timeout=120)
names = zipfile.ZipFile(io.BytesIO(r.content)).namelist() if r.status_code == 200 and r.content[:2] == b"PK" else []
res.check("R03", "ZIP export holds both results", len(names), 2)

# ----------------------------------------------------------------------------- R04 watermark
p4 = Project(prem, "b12-watermark")
p4.image(png(96, 64, 3), "wm.png")
res.check("R04", "add watermark", p4.tool("watermark", {}), {200, 201, 204})
res.check("R04", "Apply", p4.apply(), {200, 201, 202, 204})
out = p4.results(1)
data = fetch(out["imgs"][0]["url"]) if out["imgs"] else None
res.check("R04", "watermarked image produced (size, differs from original)",
          (image_size(data), bool(data) and data != png(96, 64, 3)), lambda v: v[0] is not None and v[1])

# ----------------------------------------------------------------------------- R05 AI tools
AI = (("cut_ai", {}), ("upgrade_ai", {}), ("bg_remove_ai", {}), ("text_ai", {}), ("obj_ai", {}),
      ("people_ai", {}), ("expand_ai", {"mode": "generative", "left": 8, "right": 8, "top": 4, "bottom": 4, "steps": 5}))
for procedure, params in AI:
    p = Project(prem, f"b12-{procedure}")
    p.image(png(128, 96, 5), f"{procedure}.png")
    res.check("R05", f"{procedure}: add", p.tool(procedure, params), {200, 201, 204})
    res.check("R05", f"{procedure}: Apply", p.apply(), {200, 201, 202, 204})
    out = p.results(1, timeout=600)
    kinds = [i.get("type") for i in out["imgs"]] + ["text"] * len(out["texts"])
    ok = bool(kinds)
    if procedure == "expand_ai" and out["imgs"]:
        ok = image_size(fetch(out["imgs"][0]["url"])) == (144, 104)
    res.check("R05", f"{procedure}: result produced" + (" (128x96 -> 144x104)" if procedure == "expand_ai" else ""),
              ok, True)

# ----------------------------------------------------------------------------- R06 video
p6 = Project(prem, "b12-video")
s6 = Socket(prem["token"])
res.check("R06", "owner joins the project room", s6.join(p6.id, {"kind": "owner"}), "joined")
res.check("R06", "video upload, legacy POST", p6.video_legacy("sample_10s_720p.mp4", "legacy.mp4"), 204)
res.check("R06", "video upload, direct flow", p6.video_direct("sample_10s_720p.mp4", "direct.mp4", 10, 1280, 720), 204)
media = p6.media()
vid = media.get("legacy.mp4")
res.check("R06", "both videos listed", sorted(media), lambda v: v == ["direct.mp4", "legacy.mp4"])
res.check("R06", "add brightness", p6.tool("brightness", {"brightness": 1.1}), {200, 201, 204})
res.check("R06", "add trim 1-5 s (legacy.mp4)", p6.tool("trim", {"start": 1, "end": 5, "imgId": vid}), {200, 201, 204})
res.check("R06", "add speed 2x (legacy.mp4)", p6.tool("speed", {"factor": 2, "imgId": vid}), {200, 201, 204})
res.check("R06", "preview request", p6.call("POST", f"/preview/{vid}", json={}).status_code, {200, 201})
res.check("R06", "preview-ready event (personal room)", s6.wait("preview-ready", 180), True)
preview = json.loads(s6.payloads["preview-ready"][-1]) if s6.payloads.get("preview-ready") else {}
dur = mp4_duration(fetch(preview.get("imageUrl", ""))) if preview.get("imageUrl") else None
res.check("R06", "video preview is an MP4 of at most 3 s (edited timeline 2 s)",
          preview.get("mediaType") == "video" and dur is not None and dur <= 3.05, True)
res.check("R06", "batch Apply", p6.apply(), {200, 201, 202, 204})
out = p6.results(2, timeout=600)
durations = {i["og_img_id"]: mp4_duration(fetch(i["url"])) for i in out["imgs"]}
res.check("R06", "trim+speed video lasts ~2 s", durations.get(vid), lambda d: d is not None and 1.8 <= d <= 2.3)
res.check("R06", "untouched-length video lasts ~10 s", durations.get(media.get("direct.mp4")),
          lambda d: d is not None and 9.5 <= d <= 10.5)
res.check("R06", "video-progress events received", s6.wait("video-progress", 30), True)
res.check("R06", "process-update events received", s6.wait("process-update", 30), True)
s6.close()

# ----------------------------------------------------------------------------- R07 mixed
p7 = Project(prem, "b12-mixed")
p7.image(png(64, 48, 7), "mixed.png")
res.check("R07", "video into an image project", p7.video_legacy("sample_10s_720p.mp4", "mixed.mp4"), 204)
p7.tool("brightness", {"brightness": 1.2})
p7.tool("contrast", {"contrastFactor": 1.2})
res.check("R07", "Apply", p7.apply(), {200, 201, 202, 204})
out = p7.results(2, timeout=600)
kinds = sorted("video" if mp4_duration(fetch(i["url"])) else ("image" if image_size(fetch(i["url"])) else "?")
               for i in out["imgs"])
res.check("R07", "one image and one video result", kinds, lambda v: v == ["image", "video"])

# ----------------------------------------------------------------------------- R08 subtitles
p8 = Project(prem, "b12-subtitles")
res.check("R08", "speech video upload (webm, 177 s, premium)",
          p8.video_legacy("speech_mandela_177s_1080p.webm", "speech.webm"), 204)
res.check("R08", "add subtitles", p8.tool("subtitles", {}), {200, 201, 204})
res.check("R08", "Apply", p8.apply(), {200, 201, 202, 204})
out = p8.results(1, timeout=1500)
dur = mp4_duration(fetch(out["imgs"][0]["url"])) if out["imgs"] else None
res.check("R08", "captioned MP4 keeps the duration (~177 s)", dur, lambda d: d is not None and 170 <= d <= 180)

# ----------------------------------------------------------------------------- R09 frames
p9 = Project(prem, "b12-frames")
s9 = Socket(prem["token"])
s9.join(p9.id, {"kind": "owner"})
p9.video_legacy("sample_10s_720p.mp4", "frames.mp4")
fid = p9.media()["frames.mp4"]
res.check("R09", "add extract_frames (count 5, PNG)",
          p9.tool("extract_frames", {"mode": "count", "count": 5, "interval": 1, "format": "png"}), {200, 201, 204})
p9.call("POST", f"/preview/{fid}", json={})
ok = s9.wait("preview-ready", 180)
sheet = json.loads(s9.payloads["preview-ready"][-1]) if ok else {}
res.check("R09", "preview is a contact-sheet image", bool(image_size(fetch(sheet.get("imageUrl", ""))))
          if sheet.get("imageUrl") else False, True)
res.check("R09", "Apply", p9.apply(), {200, 201, 202, 204})
out = p9.results(5, timeout=600)
res.check("R09", "five PNG frames saved as image results of the video",
          [image_size(fetch(i["url"])) is not None and i["og_img_id"] == fid for i in out["imgs"]],
          lambda v: v == [True] * 5)
s9.close()

# ----------------------------------------------------------------------------- R10 quota
p10 = Project(free, "b12-quota")
p10.image(png(32, 24, 9), "q.png")
img = list(p10.media().values())[0]
p10.tool("upgrade_ai", {})
res.check("R10", "adding an advanced (AI) tool does not debit", remaining(free), 5)
p10.call("POST", f"/preview/{img}", json={})
time.sleep(3)
res.check("R10", "preview does not debit", remaining(free), 5)
p10.apply()
p10.results(1)
res.check("R10", "Apply debits one operation (1 image x 1 AI tool)", remaining(free), 4)
p10b = Project(free, "b12-cancel")
p10b.video_legacy("sample_10s_720p.mp4", "cancel.mp4")
p10b.tool("brightness", {"brightness": 1.1})
p10b.tool("contrast", {"contrastFactor": 1.1})
res.check("R10", "Apply (1 video x 2 effects)", p10b.apply(), {200, 201, 202, 204})
debited = remaining(free)
res.check("R10", "Apply debits two operations", debited, 2)
r = p10b.call("DELETE", "/process")
res.check("R10", "cancel accepted", r.status_code, {200, 202, 204})
end = time.monotonic() + 60
while remaining(free) != 4 and time.monotonic() < end:
    time.sleep(1)
res.check("R10", "cancellation refunds the two operations", remaining(free), 4)

# ----------------------------------------------------------------------------- R11 shares
p11 = Project(prem, "b12-share")
p11.image(png(32, 24, 11), "share.png")
links = {}
for perm in ("edit", "read"):
    r = p11.call("POST", "/share", json={"permission": perm})
    res.check("R11", f"owner creates a {perm} link", r.status_code, 201)
    links[perm] = r.json()["id"]
editor, reader = register("free"), register("free")
qe, qr = f"owner={prem['id']}&share={links['edit']}", f"owner={prem['id']}&share={links['read']}"
res.check("R11", "reader opens the project", api("GET", p11.path, reader["token"], query=qr).status_code, 200)
res.check("R11", "reader cannot edit the pipeline", p11.tool("brightness", {"brightness": 1.1}, reader["token"], qr), 403)
so, se = Socket(prem["token"]), Socket(editor["token"])
res.check("R11", "owner joins", so.join(p11.id, {"kind": "owner"}), "joined")
res.check("R11", "editor (member) joins with the edit link",
          se.join(p11.id, {"kind": "share", "shareId": links["edit"]}), "joined")
res.check("R11", "presence (editor)", p11.call("POST", "/presence", editor["token"], qe, json={}).status_code, {200, 201, 204})
res.check("R11", "editor adds a tool", p11.tool("brightness", {"brightness": 1.1}, editor["token"], qe), {200, 201, 204})
res.check("R11", "owner and member get the project-room update",
          so.wait("project-updated", 15) or so.wait("project-op", 1), True)
res.check("R11", "member gets the project-room update", se.wait("project-updated", 15) or se.wait("project-op", 1), True)
stale = api("POST", p11.path + "/tool", prem["token"], headers={"X-Project-Version": "0"},
            json={"procedure": "contrast", "params": {"contrastFactor": 1.1}})
res.check("R11", "stale version answers 409", stale.status_code, 409)
img = list(p11.media().values())[0]
p11.call("POST", f"/preview/{img}", editor["token"], qe, json={})
res.check("R11", "member who previews gets preview-ready (personal room)", se.wait("preview-ready", 120), True)
res.check("R11", "presence leave", p11.call("DELETE", "/presence", editor["token"], qe).status_code, {200, 204})
res.check("R11", "owner revokes the edit link", p11.call("DELETE", f"/share/{links['edit']}").status_code, {200, 204})
res.check("R11", "revoked link no longer opens the project",
          api("GET", p11.path, editor["token"], query=qe).status_code, {403, 404, 410})
so.close()
se.close()

# ----------------------------------------------------------------------------- R12 presets
preset = {"name": f"B12 {uuid.uuid4().hex[:6]}", "tools": [{"procedure": "brightness", "params": {"brightness": 1.2}},
                                                        {"procedure": "contrast", "params": {"contrastFactor": 1.1}}]}
r = api("POST", f"users/{prem['id']}/presets", prem["token"], json=preset)
res.check("R12", "own preset created", r.status_code, 201)
pid = r.json()["_id"]
listed = api("GET", f"users/{prem['id']}/presets", prem["token"]).json()
if isinstance(listed, dict):
    listed = listed.get("userPresets", [])
res.check("R12", "own preset listed", any(p.get("_id") == pid for p in listed), True)
res.check("R12", "another account cannot list it", api("GET", f"users/{prem['id']}/presets", free["token"]).status_code, 403)
r = api("POST", f"users/{prem['id']}/presets/{pid}/share", prem["token"])
res.check("R12", "preset shared", r.status_code, {200, 201})
share = r.json().get("shareId") or r.json().get("id")
res.check("R12", "shared preset readable by its share id",
          api("GET", f"users/presets/share/{share}").status_code, 200)

# ----------------------------------------------------------------------------- R13 subscription
r = api("PUT", f"subscriptions/{prem['id']}/cancel", prem["token"], json={})
res.check("R13", "cancel subscription", r.status_code, 200)
res.check("R13", "profile back to free", api("GET", f"users/{prem['id']}", prem["token"]).json().get("type"), "free")

# ----------------------------------------------------------------------------- R14 deletion
victim = register("free")
Project(victim, "b12-delete")
res.check("R14", "holder deletes the account", api("DELETE", f"users/{victim['id']}", victim["token"]).status_code, 204)
after = direct("projects", "GET", f"/{victim['id']}", peer="api_gateway",
               token=internal_token("projects", "GET", f"/{victim['id']}", victim["id"]), want_body=True)
res.check("R14", "no project left for the deleted account", after[1] if after[0] == 200 else after[0], lambda v: v == [])

res.finish(required_ids=[f"R{n:02d}" for n in range(1, 15)])
