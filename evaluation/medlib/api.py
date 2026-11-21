"""Client for the public entry (nginx -> api_gateway), plus fixtures."""
from __future__ import annotations

import struct
import time
import uuid
import zlib
from dataclasses import dataclass, field
from typing import Any

import requests
import urllib3

from . import dockerctl
from .config import SETTINGS
from .util import log, sha256_bytes

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class Account:
    id: str
    jwt: str
    email: str
    password: str
    type: str

    @property
    def bearer(self) -> dict:
        return {"Authorization": f"Bearer {self.jwt}"}


@dataclass
class Project:
    id: str
    owner: Account
    version: int = 0
    extra: dict = field(default_factory=dict)


class Resp:
    """Uniform view of a response or a transport failure."""

    def __init__(self, r: requests.Response | None = None, exc: BaseException | None = None,
                 ms: float | None = None):
        self.r, self.exc, self.ms = r, exc, ms
        self.status = r.status_code if r is not None else None
        self.headers = {k.lower(): v for k, v in r.headers.items()} if r is not None else {}
        self._json: Any = None
        if r is not None:
            try:
                self._json = r.json()
            except ValueError:
                self._json = None

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300

    @property
    def json(self) -> Any:
        return self._json

    @property
    def error_kind(self) -> str | None:
        if self.exc is None:
            return None
        from .actions import classify_exception
        return classify_exception(self.exc)


def png_bytes(size: int = 64, seed: int = 128) -> bytes:
    def chunk(t: bytes, d: bytes) -> bytes:
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes([seed % 256]) * (size * 3)
    raw = row * size
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


class API:
    def __init__(self) -> None:
        self.s = requests.Session()
        self.s.verify = SETTINGS.verify()
        self.gw = SETTINGS.gw

    # ---- generic ----------------------------------------------------------
    def req(self, method: str, path: str, *, acct: Account | None = None, headers: dict | None = None,
            json: Any = None, params: dict | None = None, files: dict | None = None,
            timeout: float = 30, session: requests.Session | None = None) -> Resp:
        h = dict(headers or {})
        if acct is not None:
            h.update(acct.bearer)
        t0 = time.monotonic()
        try:
            r = (session or self.s).request(method, self.gw + path.lstrip("/"), headers=h, json=json,
                                            params=params, files=files, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            return Resp(exc=exc, ms=(time.monotonic() - t0) * 1000)
        return Resp(r, ms=(time.monotonic() - t0) * 1000)

    def wait_ready(self, timeout: float = 900) -> None:
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            r = self.req("GET", "users/000000000000000000000000", timeout=5)
            if r.status is not None and r.status not in (502, 503, 504):
                try:
                    a = self.register()
                    p = self.create_project(a)
                    if self.get_project(a, a.id, p.id).ok:
                        return
                except Exception as exc:  # noqa: BLE001
                    last = exc
            time.sleep(5)
        raise SystemExit(f"Application not ready after {timeout}s ({last!r})")

    # ---- accounts ---------------------------------------------------------
    def register(self, type_: str = "free") -> Account:
        email = f"med-{uuid.uuid4().hex[:12]}@example.invalid"
        password = uuid.uuid4().hex
        r = self.req("POST", "users/", json={"name": "med", "email": email, "password": password, "type": type_})
        if r.status != 201 or not r.json:
            raise RuntimeError(f"register failed: HTTP {r.status}")
        u = r.json["user"]
        return Account(u["_id"], r.json["jwt"], email, password, u.get("type", type_))

    def login(self, acct: Account) -> None:
        r = self.req("POST", f"users/{acct.email}/login", json={"password": acct.password})
        if r.ok and r.json and r.json.get("jwt"):
            acct.jwt = r.json["jwt"]

    def make_premium(self, acct: Account) -> None:
        """Controlled fixture (same in BF and MF): set type=premium in the users DB."""
        res = dockerctl.probe({"action": "mongo", "uri": SETTINGS.admin_mongo_uri("users"), "db": "user",
                               "coll": "users", "op": "update_one", "filter": {"_id": acct.id},
                               "set": {"type": "premium"}})
        if not res.get("ok"):
            raise RuntimeError(f"premium fixture failed: {res.get('error_kind')} {res.get('error', '')}")
        acct.type = "premium"
        self.login(acct)

    def premium(self) -> Account:
        a = self.register("free")
        self.make_premium(a)
        return a

    def user(self, acct: Account, target: str | None = None, with_token: bool = True) -> Resp:
        return self.req("GET", f"users/{target or acct.id}", acct=acct if with_token else None)

    # ---- projects ---------------------------------------------------------
    def create_project(self, acct: Account, name: str = "med") -> Project:
        r = self.req("POST", f"projects/{acct.id}", acct=acct, json={"name": name})
        if r.status != 201 or not r.json:
            raise RuntimeError(f"create project failed: HTTP {r.status}")
        return Project(r.json["_id"], acct, int(r.json.get("version") or 0))

    def get_project(self, acct: Account, owner_id: str, pid: str, params: dict | None = None) -> Resp:
        return self.req("GET", f"projects/{owner_id}/{pid}", acct=acct, params=params)

    def owner_view(self, p: Project) -> dict | None:
        r = self.get_project(p.owner, p.owner.id, p.id)
        if r.ok and isinstance(r.json, dict):
            if r.json.get("version") is not None:
                p.version = int(r.json["version"])
            return r.json
        return None

    def version(self, p: Project) -> int:
        self.owner_view(p)
        return p.version

    def add_tool(self, acct: Account, p: Project, procedure: str = "brightness", params: dict | None = None,
                 path_user: str | None = None, query: dict | None = None, version: int | None = None) -> Resp:
        v = self.version(p) if version is None else version
        r = self.req("POST", f"projects/{path_user or p.owner.id}/{p.id}/tool", acct=acct,
                     headers={"X-Project-Version": str(v)},
                     json={"procedure": procedure, "params": params or {"brightness": 1.2}}, params=query)
        if r.headers.get("x-project-version"):
            try:
                p.version = int(r.headers["x-project-version"])
            except ValueError:
                pass
        return r

    def upload_small(self, acct: Account, p: Project, kind: str, name: str, data: bytes, ctype: str,
                     path_user: str | None = None, query: dict | None = None) -> Resp:
        field_name = "image" if kind == "img" else "video"
        v = self.version(p)
        return self.req("POST", f"projects/{path_user or p.owner.id}/{p.id}/{kind}", acct=acct,
                        headers={"X-Project-Version": str(v)}, params=query,
                        files={field_name: (name, data, ctype)}, timeout=120)

    def media_url(self, acct: Account, owner_id: str, pid: str, img_id: str, query: dict | None = None) -> Resp:
        return self.req("GET", f"projects/{owner_id}/{pid}/img/{img_id}", acct=acct, params=query)

    def fetch_sha(self, url: str) -> dict:
        import hashlib
        h, n = hashlib.sha256(), 0
        try:
            with self.s.get(url, stream=True, timeout=300) as r:
                if r.status_code != 200:
                    return {"ok": False, "status": r.status_code}
                for c in r.iter_content(1 << 20):
                    h.update(c)
                    n += len(c)
        except Exception as exc:  # noqa: BLE001
            from .actions import classify_exception
            return {"ok": False, "status": None, "error_kind": classify_exception(exc)}
        return {"ok": True, "status": 200, "sha256": h.hexdigest(), "bytes": n}

    # ---- sharing ----------------------------------------------------------
    def share_create(self, p: Project, permission: str) -> str:
        v = self.version(p)
        r = self.req("POST", f"projects/{p.owner.id}/{p.id}/share", acct=p.owner,
                     headers={"X-Project-Version": str(v)}, json={"permission": permission})
        if not r.ok or not r.json or not r.json.get("id"):
            raise RuntimeError(f"share create failed: HTTP {r.status}")
        return r.json["id"]

    def share_resolve(self, acct: Account, share_id: str) -> Resp:
        return self.req("GET", f"projects/share/{share_id}/project", acct=acct)

    def share_revoke(self, p: Project, share_id: str) -> Resp:
        """Retries on 409: a concurrent producer may bump the version (S12)."""
        r = None
        for _ in range(10):
            v = self.version(p)
            r = self.req("DELETE", f"projects/{p.owner.id}/{p.id}/share/{share_id}", acct=p.owner,
                         headers={"X-Project-Version": str(v)})
            if r.status != 409:
                return r
        return r

    # ---- subscriptions ------------------------------------------------------
    def subscription_fixture(self, acct: Account) -> bool:
        body = {"subscription": {"user_id": acct.id, "interval": 1},
                "card": {"cardNumber": "4242424242424242", "expiryMonth": "12",
                         "expiryYear": "30", "cvc": "123"}}
        r = self.req("POST", "subscriptions/", acct=acct, json=body)
        return r.ok


@dataclass
class Victim:
    owner: Account
    outsider: Account
    reader: Account
    editor: Account
    project: Project
    img_id: str
    og_key: str
    png_sha: str
    read_share: str
    edit_share: str


def s3_admin_keys(prefix: str) -> list[str]:
    """Verification channel (admin credentials, inside the network)."""
    access, secret = SETTINGS.s3_admin()
    res = dockerctl.probe({"action": "s3", "endpoint": "http://seaweedfs:9000", "access": access,
                           "secret": secret, "bucket": SETTINGS.s3_bucket, "op": "list_prefix",
                           "prefix": prefix})
    if not res.get("ok"):
        raise RuntimeError(f"S3 admin listing failed: {res.get('error_kind')} {res.get('error', '')}")
    return res.get("keys_list", [])


def s3_admin_exists(key: str) -> bool | None:
    access, secret = SETTINGS.s3_admin()
    res = dockerctl.probe({"action": "s3", "endpoint": "http://seaweedfs:9000", "access": access,
                           "secret": secret, "bucket": SETTINGS.s3_bucket, "op": "head", "key": key})
    return res.get("exists") if res.get("ok") else None


def object_key(owner_id: str, pid: str, stage: str, name: str) -> str:
    """Same layout as imageStorageService/services/storage.js."""
    return f"users/{owner_id}/projects/{pid}/{stage}/{name}"


def victim_fixture(api: API, owner_type: str = "premium") -> Victim:
    """Owner project with 1 PNG and 1 tool, plus outsider, reader and editor.

    The owner is premium by default: GET /:user/:project registers the caller as an
    editor and a free owner has only 2 editor slots, which would turn later cases
    into 429 responses unrelated to authorization."""
    owner = api.premium() if owner_type == "premium" else api.register()
    outsider, reader, editor = api.register(), api.register(), api.register()
    p = api.create_project(owner, "victim")
    png = png_bytes(seed=int(time.time()) % 200 + 20)
    r = api.upload_small(owner, p, "img", "victim.png", png, "image/png")
    if not r.ok:
        raise RuntimeError(f"fixture image upload failed: HTTP {r.status}")
    if not api.add_tool(owner, p).ok:
        raise RuntimeError("fixture tool failed")
    view = api.owner_view(p) or {}
    imgs = view.get("imgs") or []
    if not imgs:
        raise RuntimeError("fixture: project has no media")
    src_keys = s3_admin_keys(f"users/{owner.id}/projects/{p.id}/src/")
    og_key = src_keys[0].rsplit("/", 1)[1] if src_keys else ""
    read_share = api.share_create(p, "read")
    edit_share = api.share_create(p, "edit")
    api.share_resolve(reader, read_share)
    api.share_resolve(editor, edit_share)
    return Victim(owner, outsider, reader, editor, p, str(imgs[0]["_id"]),
                  og_key, sha256_bytes(png), read_share, edit_share)


def count(view: dict | None, key: str) -> int | None:
    if view is None:
        return None
    return len(view.get(key) or [])


def note(msg: str) -> None:
    log(msg)
