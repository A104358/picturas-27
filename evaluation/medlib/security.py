"""Security metrics: S01-S05, S12, S16-S18, S21 (docs/planoMedicao.md §7)."""
from __future__ import annotations

import socket
import subprocess
import threading
import time
import uuid
from collections import Counter
from typing import Callable

import jwt as pyjwt

from . import actions, dockerctl
from .api import API, Account, Project, count, object_key, png_bytes, s3_admin_exists, s3_admin_keys, victim_fixture
from .config import GIT_DEFAULT_RABBIT, GIT_DEFAULT_S3, REPO, SETTINGS
from .util import Results, log, median, utc_now
from .ws import WS, op_version

ADMITIDO = "ADMITIDO"
REC_DOM = "RECUSADO_DOMINIO"
REC_TLS = "RECUSADO_TLS"
REC_REDE = "RECUSADO_REDE"
INCONC = "INCONCLUSIVO"
NA = "NAO_APLICAVEL"
REFUSED = {REC_DOM, REC_TLS, REC_REDE}
REFUSAL_CODES = {401, 403, 404, 410}


def classify(effect: bool | None, status: int | None = None, error_kind: str | None = None,
             allow_2xx_no_effect: bool = False) -> tuple[str, str]:
    """Effect decides admission; HTTP status alone never does (plan §5.8)."""
    if effect is True:
        return ADMITIDO, "efeito verificado"
    if error_kind:
        if error_kind == "tls":
            return REC_TLS, "handshake TLS recusado"
        if error_kind in ("refused", "dns"):
            return REC_REDE, "ligação recusada / porta não publicada"
        if error_kind == "auth":
            return REC_DOM, "credenciais recusadas"
        return INCONC, f"erro de transporte: {error_kind}"
    if effect is None:
        return INCONC, "efeito não verificável"
    if status in REFUSAL_CODES:
        return REC_DOM, f"HTTP {status}, sem efeito"
    if status is not None and 200 <= status < 300 and allow_2xx_no_effect:
        return REC_DOM, f"HTTP {status}, pedido ignorado (sem efeito verificado)"
    if status is None and effect is False:
        return REC_DOM, "operação recusada, sem efeito"
    return INCONC, f"HTTP {status} sem efeito"


class Matrix:
    """Collects attempts of one metric and writes raw records."""

    def __init__(self, metric: str, res: Results, campaign: str):
        self.metric, self.res, self.campaign = metric, res, campaign
        self.attempts: list[dict] = []
        self.controls: list[dict] = []

    def add(self, case: str, surface: str, rep: int, outcome: tuple[str, str], **obs) -> None:
        rec = {"metric": self.metric, "campaign": self.campaign, "case": case, "surface": surface,
               "rep": rep, "result": outcome[0], "reason": outcome[1], "t_utc": utc_now(), **obs}
        self.attempts.append(rec)
        self.res.raw(self.metric, rec)
        log(f"{self.metric} {case} [{surface}] rep{rep}: {outcome[0]} ({outcome[1]})")

    def control(self, name: str, rep: int, ok: bool, note: str = "") -> None:
        rec = {"metric": self.metric, "campaign": self.campaign, "control": name, "rep": rep,
               "ok": bool(ok), "note": note, "t_utc": utc_now()}
        self.controls.append(rec)
        self.res.raw(self.metric, rec)

    def summary(self) -> dict:
        counted = [a for a in self.attempts if a["result"] != NA]
        by = Counter(a["result"] for a in counted)
        surfaces: dict[str, dict] = {}
        for a in counted:
            s = surfaces.setdefault(a["surface"], {"tentativas": 0, "admitidos": 0, "inconclusivos": 0})
            s["tentativas"] += 1
            s["admitidos"] += a["result"] == ADMITIDO
            s["inconclusivos"] += a["result"] == INCONC
        return {
            "tentativas": len(counted),
            "admitidos": by.get(ADMITIDO, 0),
            "recusados": sum(by.get(k, 0) for k in REFUSED),
            "inconclusivos": by.get(INCONC, 0),
            "nao_aplicaveis": sum(1 for a in self.attempts if a["result"] == NA),
            "por_resultado": dict(by),
            "por_superficie": surfaces,
            "casos_admitidos": sorted({f'{a["case"]}[{a["surface"]}]' for a in counted if a["result"] == ADMITIDO}),
            "casos_inconclusivos": sorted({f'{a["case"]}[{a["surface"]}]' for a in counted if a["result"] == INCONC}),
            "controlos_ok": sum(c["ok"] for c in self.controls),
            "controlos_total": len(self.controls),
        }


def forged_jwt(user_id: str, *, expired: bool = False, none_alg: bool = False) -> str:
    payload = {"id": user_id, "type": "free", "iat": int(time.time()) - 10,
               "exp": int(time.time()) + (-3600 if expired else 3600)}
    if none_alg:
        return pyjwt.encode(payload, key="", algorithm="none")
    # Never the real secret: a random key unless MED_JWT_TEST_KEY is set for a specific test.
    import os
    key = os.environ.get("MED_JWT_TEST_KEY") or uuid.uuid4().hex
    return pyjwt.encode(payload, key=key, algorithm="HS256")


# ---------------------------------------------------------------------------
# Direct calls (host surface or Docker-network surface)
# ---------------------------------------------------------------------------

def direct_http(surface: str, service: str, method: str, path: str, headers: dict | None = None,
                json_body=None, files: dict | None = None) -> dict:
    svc = SETTINGS.service(service)
    schemes = [svc.scheme, "http" if svc.scheme == "https" else "https"]
    if surface == "host":
        port = dockerctl.published_port(service, svc.port)
        if port is None:
            return {"ok": False, "status": None, "error_kind": "refused", "note": "porta não publicada"}
        host = "127.0.0.1"
    else:
        port, host = svc.port, svc.host
    first = None
    for scheme in schemes:
        spec = {"action": "http", "method": method, "url": f"{scheme}://{host}:{port}{path}",
                "headers": headers or {}, "json": json_body, "files": files, "timeout": 20}
        r = actions.http(spec) if surface == "host" else dockerctl.probe(spec)
        r["scheme"] = scheme
        if first is None:
            first = r
        if r.get("status") is not None:
            return r
        if r.get("error_kind") in ("refused", "dns", "timeout"):
            break
    return first or {"ok": False, "error_kind": "other"}


def lan_ip() -> str | None:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))  # no packet is sent for UDP connect
        ip = s.getsockname()[0]
        s.close()
        return None if ip.startswith("127.") else ip
    except OSError:
        return None


def _body_id(r: dict | object) -> str | None:
    body = r.get("body") if isinstance(r, dict) else None
    return str(body.get("_id")) if isinstance(body, dict) and body.get("_id") is not None else None


def _resp_id(r) -> str | None:
    j = r.json
    return str(j.get("_id")) if isinstance(j, dict) and j.get("_id") is not None else None


def _project_listed(api: API, owner: Account, pid: str) -> bool | None:
    r = api.req("GET", f"projects/{owner.id}", acct=owner)
    if not r.ok or not isinstance(r.json, list):
        return None
    return any(str(p.get("_id")) == pid for p in r.json if isinstance(p, dict))


def _user_type(api: API, acct: Account) -> str | None:
    r = api.user(acct)
    return r.json.get("type") if r.ok and isinstance(r.json, dict) else None


def _remaining_ops(api: API, acct: Account):
    r = api.user(acct)
    return r.json.get("remaining_operations") if r.ok and isinstance(r.json, dict) else None


# ---------------------------------------------------------------------------
# S01 - public entry
# ---------------------------------------------------------------------------

def run_s01(api: API, res: Results, campaign: str, reps: int) -> dict:
    m = Matrix("S01", res, campaign)
    for rep in range(1, reps + 1):
        v = victim_fixture(api)
        o, x, p = v.owner, v.outsider, v.project
        q = {"owner": o.id}

        r = api.get_project(x, o.id, p.id)
        m.add("G01", "publica", rep, classify(r.ok and _resp_id(r) == p.id, r.status, r.error_kind), status=r.status)

        r = api.get_project(x, x.id, p.id, params=q)
        m.add("G02", "publica", rep, classify(r.ok and _resp_id(r) == p.id, r.status, r.error_kind), status=r.status)

        before = count(api.owner_view(p), "tools")
        r = api.add_tool(x, p, path_user=x.id, query=q, version=p.version)
        after = count(api.owner_view(p), "tools")
        eff = None if before is None or after is None else after > before
        m.add("G03", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status, tools=[before, after])

        before = count(api.owner_view(p), "imgs")
        r = api.upload_small(x, p, "img", "intruder.png", png_bytes(seed=9), "image/png", path_user=x.id, query=q)
        after = count(api.owner_view(p), "imgs")
        eff = None if before is None or after is None else after > before
        m.add("G04", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status, imgs=[before, after])

        r = api.media_url(x, x.id, p.id, v.img_id, query=q)
        eff = False
        if r.ok and isinstance(r.json, dict) and r.json.get("url"):
            f = api.fetch_sha(r.json["url"])
            eff = f.get("sha256") == v.png_sha if f.get("ok") else None
        m.add("G10", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status)

        api.owner_view(p)
        r = api.req("PUT", f"projects/{x.id}/{p.id}", acct=x, params=q,
                    headers={"X-Project-Version": str(p.version)}, json={"name": "med-pwn"})
        view = api.owner_view(p)
        eff = None if view is None else view.get("name") == "med-pwn"
        m.add("G11", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status)

        r = api.req("GET", f"projects/{o.id}/{p.id}/share", acct=x)
        body = r.json
        eff = r.ok and (v.read_share in str(body))
        m.add("G14", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status)

        before = count(api.owner_view(p), "tools")
        r = api.add_tool(v.reader, p, query={"share": v.read_share}, version=p.version)
        after = count(api.owner_view(p), "tools")
        eff = None if before is None or after is None else after > before
        m.add("G15", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status, tools=[before, after])

        r = api.req("GET", f"users/{o.id}")
        eff = r.ok and isinstance(r.json, dict) and bool({"email", "type"} & set(r.json))
        m.add("G05", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status)

        email = f"med-{uuid.uuid4().hex[:12]}@example.invalid"
        r = api.req("POST", "users/", json={"name": "med", "email": email, "password": uuid.uuid4().hex,
                                            "type": "premium"})
        eff = None
        if r.status == 201 and isinstance(r.json, dict):
            u = r.json["user"]
            na = Account(u["_id"], r.json["jwt"], email, "", u.get("type", ""))
            t = _user_type(api, na)
            eff = None if t is None else t == "premium"
        elif r.status is not None:
            eff = False
        m.add("G06", "publica", rep, classify(eff, r.status, r.error_kind, allow_2xx_no_effect=True), status=r.status)

        r = api.req("PUT", f"users/{x.id}", acct=x, json={"type": "premium"})
        t = _user_type(api, x)
        eff = None if t is None else t == "premium"
        m.add("G07", "publica", rep, classify(eff, r.status, r.error_kind, allow_2xx_no_effect=True), status=r.status)

        s = api.register()
        if api.subscription_fixture(s):
            r = api.req("GET", f"subscriptions/{s.id}/status")
            eff = r.ok and isinstance(r.json, dict) and "status" in r.json
            m.add("G08", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status)
            r = api.req("PUT", f"subscriptions/{s.id}/cancel")
            st = api.req("GET", f"subscriptions/{s.id}/status", acct=s)
            eff = (st.json.get("status") == "canceled") if st.ok and isinstance(st.json, dict) else None
            m.add("G09", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status)
        else:
            m.add("G08", "publica", rep, (INCONC, "fixture de subscrição falhou"))
            m.add("G09", "publica", rep, (INCONC, "fixture de subscrição falhou"))

        before = count(api.owner_view(p), "imgs")
        r = api.req("DELETE", f"projects/{x.id}/{p.id}/img/{v.img_id}", acct=x, params=q,
                    headers={"X-Project-Version": str(p.version)})
        after = count(api.owner_view(p), "imgs")
        eff = None if before is None or after is None else after < before
        m.add("G12", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status, imgs=[before, after])

        api.owner_view(p)
        r = api.req("DELETE", f"projects/{x.id}/{p.id}", acct=x, params=q,
                    headers={"X-Project-Version": str(p.version)})
        listed = _project_listed(api, o, p.id)
        eff = None if listed is None else not listed
        m.add("G13", "publica", rep, classify(eff, r.status, r.error_kind), status=r.status)

        # Positive control: the owner still reaches a fresh project of its own.
        p2 = api.create_project(o)
        m.control("dono_le_projeto", rep, api.get_project(o, o.id, p2.id).ok)
    sm = m.summary()
    res.summary("S01", sm)
    return sm


# ---------------------------------------------------------------------------
# S02 - internal APIs called directly
# ---------------------------------------------------------------------------

def run_s02(api: API, res: Results, campaign: str, reps: int) -> dict:
    m = Matrix("S02", res, campaign)
    for rep in range(1, reps + 1):
        for surface in ("host", "rede"):
            v = victim_fixture(api)
            o, x, p = v.owner, v.outsider, v.project
            path = f"/{o.id}/{p.id}"
            variants = [
                ("D01", {}),
                ("D02", {"X-Caller-Id": o.id}),
                ("D03", {"Authorization": f"Bearer {x.jwt}"}),
                ("D04a", {"Authorization": f"Bearer {forged_jwt(o.id)}"}),
                ("D04b", {"Authorization": f"Bearer {forged_jwt(o.id, none_alg=True)}"}),
            ]
            for case, hdr in variants:
                r = direct_http(surface, "projects", "GET", path, hdr)
                eff = r.get("ok") and _body_id(r) == p.id
                m.add(case, surface, rep, classify(eff, r.get("status"), r.get("error_kind")),
                      status=r.get("status"), scheme=r.get("scheme"))

            before = count(api.owner_view(p), "tools")
            r = direct_http(surface, "projects", "POST", path + "/tool",
                            {"X-Caller-Id": o.id, "X-Project-Version": str(p.version)},
                            {"procedure": "brightness", "params": {"brightness": 1.3}})
            after = count(api.owner_view(p), "tools")
            eff = None if before is None or after is None else after > before
            m.add("D05", surface, rep, classify(eff, r.get("status"), r.get("error_kind")), status=r.get("status"))

            vu = api.register()
            r = direct_http(surface, "users", "PUT", f"/{vu.id}", {}, {"type": "premium"})
            t = _user_type(api, vu)
            eff = None if t is None else t == "premium"
            m.add("D09", surface, rep, classify(eff, r.get("status"), r.get("error_kind"), allow_2xx_no_effect=True),
                  status=r.get("status"))

            vq = api.register()
            before = _remaining_ops(api, vq)
            r = direct_http(surface, "users", "GET", f"/{vq.id}/process/1")
            after = _remaining_ops(api, vq)
            eff = None if before is None or after is None else after < before
            m.add("D13", surface, rep, classify(eff, r.get("status"), r.get("error_kind")), status=r.get("status"),
                  ops=[before, after])

            s = api.register()
            if api.subscription_fixture(s):
                r = direct_http(surface, "subscriptions", "GET", f"/{s.id}/status")
                body = r.get("body")
                eff = bool(r.get("ok") and isinstance(body, dict) and "status" in body)
                m.add("D14", surface, rep, classify(eff, r.get("status"), r.get("error_kind")), status=r.get("status"))
            else:
                m.add("D14", surface, rep, (INCONC, "fixture de subscrição falhou"))

            api.owner_view(p)
            r = direct_http(surface, "projects", "DELETE", path,
                            {"X-Caller-Id": o.id, "X-Project-Version": str(p.version)})
            listed = _project_listed(api, o, p.id)
            eff = None if listed is None else not listed
            m.add("D06", surface, rep, classify(eff, r.get("status"), r.get("error_kind")), status=r.get("status"))
        m.control("dono_le_projeto", rep, api.get_project(v.owner, v.owner.id,
                                                          api.create_project(v.owner).id).ok)
    sm = m.summary()
    res.summary("S02", sm)
    return sm


# ---------------------------------------------------------------------------
# S03 - storage service
# ---------------------------------------------------------------------------

def _probe_sha(url: str) -> dict:
    return dockerctl.probe({"action": "fetch_sha", "url": url, "timeout": 60})


def run_s03(api: API, res: Results, campaign: str, reps: int) -> dict:
    m = Matrix("S03", res, campaign)
    for rep in range(1, reps + 1):
        for surface in ("host", "rede"):
            v = victim_fixture(api)
            o, p = v.owner, v.project
            if not v.og_key:
                for case in ("D06", "D07", "D15", "D08"):
                    m.add(case, surface, rep, (INCONC, "chave do original não encontrada"))
                continue
            src_key = object_key(o.id, p.id, "src", v.og_key)

            r = direct_http(surface, "img_storage", "GET", f"/image/internal/{o.id}/{p.id}/src/{v.og_key}")
            eff = False
            body = r.get("body")
            if r.get("ok") and isinstance(body, dict) and body.get("url"):
                f = _probe_sha(body["url"])
                eff = f.get("sha256") == v.png_sha if f.get("ok") else None
            m.add("D06", surface, rep, classify(eff, r.get("status"), r.get("error_kind")), status=r.get("status"))

            prefix = f"users/{o.id}/projects/{p.id}/out/"
            before = set(s3_admin_keys(prefix))
            r = direct_http(surface, "img_storage", "POST", f"/upload/{o.id}/{p.id}/out",
                            files=actions.to_files("file", f"med-{uuid.uuid4().hex[:6]}.png", png_bytes(seed=3),
                                                   "image/png"))
            after = set(s3_admin_keys(prefix))
            m.add("D07", surface, rep, classify(bool(after - before), r.get("status"), r.get("error_kind")),
                  status=r.get("status"))

            out_key = object_key(o.id, p.id, "out", v.og_key)
            existed = s3_admin_exists(out_key)
            r = direct_http(surface, "img_storage", "POST", f"/copy/{o.id}/{p.id}/src/out/{v.og_key}")
            exists = s3_admin_exists(out_key)
            eff = None if existed is None or exists is None or existed else exists
            m.add("D15", surface, rep, classify(eff, r.get("status"), r.get("error_kind")), status=r.get("status"))

            r = direct_http(surface, "img_storage", "DELETE", f"/delete/{o.id}/{p.id}/src/{v.og_key}")
            exists = s3_admin_exists(src_key)
            eff = None if exists is None else not exists
            m.add("D08", surface, rep, classify(eff, r.get("status"), r.get("error_kind")), status=r.get("status"))
        # Positive control: the owner downloads its original through a signed URL.
        v2 = victim_fixture(api)
        mu = api.media_url(v2.owner, v2.owner.id, v2.project.id, v2.img_id)
        ok = mu.ok and isinstance(mu.json, dict) and api.fetch_sha(mu.json.get("url", "")).get("sha256") == v2.png_sha
        m.control("dono_descarrega_original", rep, ok)
    sm = m.summary()
    res.summary("S03", sm)
    return sm


# ---------------------------------------------------------------------------
# S04 - WebSocket admission
# ---------------------------------------------------------------------------

def _edits(api: API, p: Project, n: int = 3, gap: float = 0.5) -> list[int]:
    versions = []
    api.owner_view(p)
    for i in range(n):
        r = api.add_tool(p.owner, p, params={"brightness": 1 + (i + 1) / 100}, version=p.version)
        if r.ok:
            versions.append(p.version)
        time.sleep(gap)
    return versions


def _wait_projects_ready(api: API, p: Project, timeout: float = 180) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if api.get_project(p.owner, p.owner.id, p.id).ok:
            return True
        time.sleep(2)
    return False


def run_s04(api: API, res: Results, campaign: str, reps: int) -> dict:
    m = Matrix("S04", res, campaign)
    for rep in range(1, reps + 1):
        v = victim_fixture(api)
        p = v.project
        owner_ws, reader_ws = WS("owner"), WS("reader")
        owner_ws.connect(v.owner.jwt)
        owner_ws.join(p.id)
        reader_ws.connect(v.reader.jwt)
        reader_ws.join(p.id)
        time.sleep(0.5)
        cases: list[tuple[str, Callable[[], str | None], bool]] = [
            ("W01", lambda: None, False),
            ("W02", lambda: v.outsider.jwt, False),
            ("W03", lambda: forged_jwt(v.outsider.id), False),
            ("W04", lambda: forged_jwt(v.outsider.id, expired=True), False),
            ("W05", lambda: v.outsider.jwt, True),
        ]
        for case, token_fn, stop_projects in cases:
            if stop_projects:
                dockerctl.stop("projects")
            atk = WS(case)
            connected = atk.connect(token_fn())
            atk.join(p.id)
            if stop_projects:
                time.sleep(2)
                dockerctl.start("projects")
                if not _wait_projects_ready(api, p):
                    m.add(case, "ws", rep, (INCONC, "projects não recuperou"))
                    atk.close()
                    continue
            time.sleep(0.5)
            t_start = time.monotonic() * 1000
            versions = _edits(api, p)
            time.sleep(3)
            got = atk.project_events(p.id, since=t_start)
            owner_got = len(owner_ws.project_events(p.id, since=t_start))
            reader_got = len(reader_ws.project_events(p.id, since=t_start))
            controls_ok = bool(versions) and owner_got >= len(versions) and reader_got >= len(versions)
            if got:
                outcome = (ADMITIDO, f"{len(got)} eventos protegidos recebidos")
            elif not controls_ok:
                outcome = (INCONC, "controlos não receberam os eventos")
            elif not connected:
                outcome = (REC_DOM, "ligação WS recusada")
            else:
                outcome = (REC_DOM, "sem eventos protegidos")
            m.add(case, "ws", rep, outcome, connected=connected, eventos=len(got), edicoes=len(versions),
                  controlo_dono=owner_got, controlo_leitor=reader_got)
            m.control(f"{case}_dono_e_leitor_recebem", rep, controls_ok)
            atk.close()
            if stop_projects:
                # reconnect controls after the restart, for the next repetition
                owner_ws.close(); reader_ws.close()
                owner_ws, reader_ws = WS("owner"), WS("reader")
                owner_ws.connect(v.owner.jwt); owner_ws.join(p.id)
                reader_ws.connect(v.reader.jwt); reader_ws.join(p.id)
        owner_ws.close()
        reader_ws.close()
    sm = m.summary()
    res.summary("S04", sm)
    return sm


# ---------------------------------------------------------------------------
# S12 - revocation cut-off (QS-07)
# ---------------------------------------------------------------------------

def run_s12(api: API, res: Results, campaign: str, reps: int, window_s: float = 30.0,
            period_s: float = 0.25) -> dict:
    out = []
    for rep in range(1, reps + 1):
        owner = api.premium()
        p = api.create_project(owner, "s12")
        a, b = api.register(), api.register()
        share_a, share_b = api.share_create(p, "read"), api.share_create(p, "read")
        api.share_resolve(a, share_a)
        api.share_resolve(b, share_b)
        sockets = {"owner": WS("owner"), "A": WS("A"), "B": WS("B")}
        sockets["owner"].connect(owner.jwt)
        sockets["A"].connect(a.jwt)
        sockets["B"].connect(b.jwt)
        for s in sockets.values():
            s.join(p.id)
        time.sleep(1)

        emitted: dict[int, float] = {}
        stop = threading.Event()
        api.owner_view(p)

        prod_api = API()  # separate HTTP session for the producer thread

        def producer() -> None:
            seq = 0
            while not stop.is_set():
                seq += 1
                r = prod_api.add_tool(owner, p, params={"brightness": 1 + seq / 10000}, version=p.version)
                if r.ok:
                    emitted[p.version] = time.monotonic() * 1000
                elif r.status == 409:
                    prod_api.owner_view(p)
                time.sleep(period_s)

        th = threading.Thread(target=producer, daemon=True)
        th.start()
        time.sleep(2.0)
        pre = {op_version(d) for _, _, d in sockets["A"].project_events(p.id)}
        rv = api.share_revoke(p, share_a)
        t_ack = time.monotonic() * 1000
        time.sleep(window_s)
        stop.set()
        th.join(timeout=5)
        time.sleep(2.0)

        def versions_of(ws: WS) -> set[int]:
            vs = set()
            for _, ev, d in ws.project_events(p.id):
                if ev == "project-op":
                    vs.add(op_version(d))
                elif isinstance(d, dict) and d.get("version") is not None:
                    try:
                        vs.add(int(d["version"]))
                    except (TypeError, ValueError):
                        pass
            return vs

        got_a, got_owner, got_b = versions_of(sockets["A"]), versions_of(sockets["owner"]), versions_of(sockets["B"])
        post = sorted((t - t_ack, ver) for ver, t in emitted.items() if t > t_ack)
        received_post = [d for d, ver in post if ver in got_a]
        lower = max(received_post) if received_post else 0.0
        upper = None
        for i, (d, ver) in enumerate(post):
            if ver not in got_a and all(v2 not in got_a for _, v2 in post[i:]):
                upper = d
                break
        censored = upper is None
        after_limit = sum(1 for d in received_post if d > 5000)
        window_versions = {ver for _, ver in post}
        controls_ok = bool(window_versions) and window_versions <= got_owner and window_versions <= got_b
        valid = rv.ok and len(pre - {None}) >= 3
        rec = {"metric": "S12", "campaign": campaign, "rep": rep, "revoke_status": rv.status,
               "pre_revocation_events_A": len(pre - {None}), "emitted_after_ack": len(post),
               "received_after_ack_A": len(received_post), "lower_ms": round(lower, 1),
               "upper_ms": None if censored else round(upper, 1), "censored_gt_ms": window_s * 1000 if censored else None,
               "uncertainty_ms": period_s * 1000, "eventos_apos_limite": after_limit,
               "disconnect_A_ms": None if sockets["A"].disconnected_at is None
               else round(sockets["A"].disconnected_at - t_ack, 1),
               "controlos_ok": controls_ok, "valida": valid, "t_utc": utc_now()}
        res.raw("S12", rec)
        log(f"S12 rep{rep}: upper={rec['upper_ms']} censored={censored} after_limit={after_limit} "
            f"controls={controls_ok} valid={valid}")
        out.append(rec)
        for s in sockets.values():
            s.close()
    sm = {"repeticoes": out,
          "limite_superior_max_ms": None if any(r["upper_ms"] is None for r in out)
          else max(r["upper_ms"] for r in out),
          "censurado": any(r["upper_ms"] is None for r in out),
          "eventos_apos_limite": sum(r["eventos_apos_limite"] for r in out),
          "controlos_ok": all(r["controlos_ok"] for r in out),
          "invalidas": sum(not r["valida"] for r in out)}
    res.summary("S12", sm)
    return sm


# ---------------------------------------------------------------------------
# S16 - databases
# ---------------------------------------------------------------------------

DBS = [  # (service owning the DB, compose service, port, db name, collection)
    ("projects", "projects_mongoDB", 27018, "project", "projects"),
    ("users", "users_mongoDB", 27019, "user", "users"),
    ("subscriptions", "subscriptions_mongoDB", 27017, "subscription", "subscriptions"),
]
OTHER = {"projects": "users", "users": "projects", "subscriptions": "projects"}


def _git_mongo_creds() -> list[tuple[str, str]]:
    r = subprocess.run(["git", "-C", str(REPO), "grep", "-h", "-o", "-E",
                        r"mongodb://[^:/@\" ]+:[^@/\" ]+@"], capture_output=True, text=True)
    found = set()
    for line in r.stdout.splitlines():
        cred = line[len("mongodb://"):-1]
        user, _, pw = cred.partition(":")
        if user and not user.startswith("$"):
            found.add((user, pw))
    return sorted(found)


def _mongo_uri(host: str, port: int, cred: tuple[str, str] | None) -> str:
    from urllib.parse import quote_plus
    auth = f"{quote_plus(cred[0])}:{quote_plus(cred[1])}@" if cred else ""
    src = SETTINGS_AUTHSOURCE()
    return f"mongodb://{auth}{host}:{port}/" + (f"?authSource={src}" if cred else "")


def SETTINGS_AUTHSOURCE() -> str:  # noqa: N802 - small accessor kept next to its use
    import os
    return os.environ.get("MED_MONGO_AUTHSOURCE", "admin")


def _mongo(surface: str, compose_svc: str, port: int, spec: dict) -> dict:
    def uri_with_tls(uri: str) -> str:
        if not SETTINGS.mongo_ca_file:
            return uri
        from urllib.parse import quote
        sep = "&" if "?" in uri else "?"
        return uri + sep + "tls=true&tlsCAFile=" + quote(SETTINGS.data_ca("mongo", surface))

    if surface == "host":
        hp = dockerctl.published_port(compose_svc, port)
        if hp is None:
            return {"ok": False, "error_kind": "refused", "note": "porta não publicada"}
        host = compose_svc if SETTINGS.mongo_ca_file else "127.0.0.1"
        spec = {**spec, "uri": uri_with_tls(spec["uri_fn"](host, hp))}
        spec.pop("uri_fn")
        return actions.run_action({"action": "mongo", **spec,
                                   "connect_host": compose_svc if SETTINGS.mongo_ca_file else None})
    spec = {**spec, "uri": uri_with_tls(spec["uri_fn"](compose_svc, port))}
    spec.pop("uri_fn")
    return dockerctl.probe({"action": "mongo", **spec})


def _cred_or_status(kind: str, service: str, campaign: str) -> tuple[tuple[str, str] | None, str | None]:
    cred = SETTINGS.svc_cred(kind, service)
    if cred is None and campaign == "MF":
        return None, "credencial de serviço não configurada (MED_SVC_CRED_*)"
    return cred, None


def _admitted_db(r: dict) -> tuple[str, str]:
    if r.get("ok"):
        return ADMITIDO, "operação aceite"
    return classify(False if r.get("error_kind") in ("auth",) else None, None, r.get("error_kind"))


def run_s16(api: API, res: Results, campaign: str, reps: int) -> dict:
    m = Matrix("S16", res, campaign)
    git_creds = _git_mongo_creds()
    by_name = {d[0]: d for d in DBS}
    for rep in range(1, reps + 1):
        for surface in ("rede", "host"):
            for owner_svc, csvc, port, dbname, coll in DBS:
                # (a) no credentials
                r = _mongo(surface, csvc, port, {"uri_fn": lambda h, pt: _mongo_uri(h, pt, None),
                                                 "db": dbname, "coll": coll, "op": "find_one"})
                m.add(f"a:{dbname}", surface, rep, _admitted_db(r), error_kind=r.get("error_kind"))
                # (b) credentials committed to Git
                if not git_creds:
                    m.add(f"b:{dbname}", surface, rep, (NA, "nenhuma credencial Mongo encontrada no Git"))
                for cred in git_creds:
                    r = _mongo(surface, csvc, port, {"uri_fn": lambda h, pt, c=cred: _mongo_uri(h, pt, c),
                                                     "db": dbname, "coll": coll, "op": "find_one"})
                    m.add(f"b:{dbname}", surface, rep, _admitted_db(r), error_kind=r.get("error_kind"))
            # (c) credential of another service reads this DB; (d) own credential beyond privilege
            for reader, target in OTHER.items():
                cred, missing = _cred_or_status("mongo", reader, campaign)
                _, csvc, port, dbname, coll = by_name[target]
                if missing:
                    m.add(f"c:{reader}->{dbname}", surface, rep, (INCONC, missing))
                else:
                    r = _mongo(surface, csvc, port, {"uri_fn": lambda h, pt, c=cred: _mongo_uri(h, pt, c),
                                                     "db": dbname, "coll": coll, "op": "find_one"})
                    m.add(f"c:{reader}->{dbname}", surface, rep, _admitted_db(r), error_kind=r.get("error_kind"),
                          cred_configured=cred is not None)
            for owner_svc, csvc, port, dbname, coll in DBS:
                cred, missing = _cred_or_status("mongo", owner_svc, campaign)
                if missing:
                    m.add(f"d1:{owner_svc}", surface, rep, (INCONC, missing))
                    m.add(f"d2:{owner_svc}", surface, rep, (INCONC, missing))
                    continue
                other_db = by_name[OTHER[owner_svc]][3]
                r = _mongo(surface, csvc, port, {"uri_fn": lambda h, pt, c=cred: _mongo_uri(h, pt, c),
                                                 "db": other_db, "op": "insert_canary"})
                m.add(f"d1:{owner_svc}", surface, rep, _admitted_db(r), error_kind=r.get("error_kind"))
                r = _mongo(surface, csvc, port, {"uri_fn": lambda h, pt, c=cred: _mongo_uri(h, pt, c),
                                                 "db": dbname, "op": "list_dbs"})
                foreign = [n for n in r.get("names", []) if n not in (dbname, "admin", "config", "local")]
                outcome = (ADMITIDO, f"vê outras BD: {foreign}") if r.get("ok") and foreign else \
                    ((REC_DOM, "só vê a sua BD") if r.get("ok") else _admitted_db(r))
                m.add(f"d2:{owner_svc}", surface, rep, outcome, error_kind=r.get("error_kind"))
        # cleanup canaries with admin credentials
        for owner_svc, csvc, port, dbname, coll in DBS:
            dockerctl.probe({"action": "mongo", "uri": SETTINGS.admin_mongo_uri(owner_svc), "db": dbname,
                             "op": "drop_canary"})
        # controls: legitimate services still use their databases
        try:
            a = api.register()
            pr = api.create_project(a)
            m.control("users_e_projects_usam_bd", rep, api.get_project(a, a.id, pr.id).ok)
        except Exception as exc:  # noqa: BLE001
            m.control("users_e_projects_usam_bd", rep, False, repr(exc)[:100])
        m.control("subscriptions_usa_bd", rep, api.subscription_fixture(api.register()))
    sm = m.summary()
    sm["credenciais_git_encontradas"] = len(git_creds)
    res.summary("S16", sm)
    return sm


# ---------------------------------------------------------------------------
# S17 - RabbitMQ and S3
# ---------------------------------------------------------------------------

def _endpoint(surface: str, service: str, port: int) -> tuple[str, int] | None:
    if surface == "host":
        hp = dockerctl.published_port(service, port)
        return None if hp is None else ("127.0.0.1", hp)
    return service, port


def _run(surface: str, spec: dict) -> dict:
    return actions.run_action(spec) if surface == "host" else dockerctl.probe(spec)


def _admitted(r: dict) -> tuple[str, str]:
    if r.get("ok"):
        return ADMITIDO, "operação aceite"
    ek = r.get("error_kind")
    if ek in ("auth", "http"):
        return REC_DOM, f"recusado ({r.get('status') or r.get('error') or ek})"
    return classify(None, None, ek)


def run_s17(api: API, res: Results, campaign: str, reps: int) -> dict:
    m = Matrix("S17", res, campaign)
    for rep in range(1, reps + 1):
        worker_cred = SETTINGS.svc_cred("rabbit", "brightness_tool")
        if worker_cred is None and campaign != "MF":
            worker_cred = GIT_DEFAULT_RABBIT
        storage_cred = SETTINGS.svc_cred("s3", "img_storage")
        if storage_cred is None and campaign != "MF":
            storage_cred = GIT_DEFAULT_S3
        for surface in ("rede", "host"):
            amqp_ep = _endpoint(surface, "rabbitmq", SETTINGS.amqp_port)
            mgmt_ep = _endpoint(surface, "rabbitmq", SETTINGS.rabbit_mgmt_port)
            s3_ep = _endpoint(surface, "seaweedfs", 9000)
            if surface == "host":
                if amqp_ep and (SETTINGS.amqp_ca_file or SETTINGS.amqp_port != 5672):
                    amqp_ep = ("rabbitmq", amqp_ep[1])
                if mgmt_ep and SETTINGS.rabbit_mgmt_scheme == "https":
                    mgmt_ep = ("rabbitmq", mgmt_ep[1])
                if s3_ep and SETTINGS.s3_scheme == "https":
                    s3_ep = ("seaweedfs", s3_ep[1])

            def amqp(case: str, cred, op: str, **kw) -> None:
                if amqp_ep is None:
                    m.add(case, surface, rep, (REC_REDE, "porta não publicada"))
                    return
                if cred is None:
                    m.add(case, surface, rep, (INCONC, "credencial de serviço não configurada"))
                    return
                r = _run(surface, {"action": "amqp", "host": amqp_ep[0], "port": amqp_ep[1], "user": cred[0],
                                   "password": cred[1], "op": op,
                                   "tls": SETTINGS.amqp_port != 5672 or bool(SETTINGS.amqp_ca_file),
                                   "ca_file": SETTINGS.data_ca("amqp", surface),
                                   "server_name": "rabbitmq" if surface == "host" else amqp_ep[0],
                                   "connect_host": "rabbitmq" if surface == "host" and
                                   amqp_ep[0] == "rabbitmq" else None, **kw})
                m.add(case, surface, rep, _admitted(r), error_kind=r.get("error_kind"))

            def mgmt(case: str, cred) -> None:
                if mgmt_ep is None:
                    m.add(case, surface, rep, (REC_REDE, "porta não publicada"))
                    return
                if cred is None:
                    m.add(case, surface, rep, (INCONC, "credencial de serviço não configurada"))
                    return
                r = _run(surface, {"action": "rabbit_mgmt", "url":
                                   f"{SETTINGS.rabbit_mgmt_scheme}://{mgmt_ep[0]}:{mgmt_ep[1]}/api/overview",
                                   "ca_file": SETTINGS.data_ca("rabbit_mgmt", surface),
                                   "connect_host": "rabbitmq" if surface == "host" and
                                   mgmt_ep[0] == "rabbitmq" else None,
                                   "user": cred[0], "password": cred[1]})
                m.add(case, surface, rep, _admitted(r), status=r.get("status"), error_kind=r.get("error_kind"))

            amqp("R1", GIT_DEFAULT_RABBIT, "connect")
            mgmt("R2", GIT_DEFAULT_RABBIT)
            amqp("R3", worker_cred, "get", queue="ws_queue")
            amqp("R4", worker_cred, "declare_delete")
            mgmt("R5", worker_cred)

            def s3(case: str, cred, op: str, **kw) -> dict:
                if s3_ep is None:
                    m.add(case, surface, rep, (REC_REDE, "porta não publicada"))
                    return {}
                if cred is None:
                    m.add(case, surface, rep, (INCONC, "credencial de serviço não configurada"))
                    return {}
                r = _run(surface, {"action": "s3", "endpoint": SETTINGS.s3_endpoint(*s3_ep),
                                   "ca_file": SETTINGS.data_ca("s3", surface), "access": cred[0],
                                   "connect_host": "seaweedfs" if surface == "host" and
                                   s3_ep[0] == "seaweedfs" else None,
                                   "secret": cred[1], "op": op, **kw})
                m.add(case, surface, rep, _admitted(r), error_kind=r.get("error_kind"))
                return r

            s3("B1", GIT_DEFAULT_S3, "list", bucket=SETTINGS.s3_bucket)
            canary = f"med-canary-{uuid.uuid4().hex[:8]}"
            r = s3("B2", storage_cred, "create_bucket", bucket=canary)
            if r.get("ok"):
                access, secret = SETTINGS.s3_admin()
                dockerctl.probe({"action": "s3", "endpoint": SETTINGS.s3_endpoint(),
                                 "ca_file": SETTINGS.data_ca("s3"), "access": access,
                                 "secret": secret, "bucket": canary, "op": "delete_bucket"})

        # B3: anonymous read of an original through the public /s3/ path
        v = victim_fixture(api)
        if v.og_key:
            key = object_key(v.owner.id, v.project.id, "src", v.og_key)
            f = api.fetch_sha(f"{SETTINGS.base_url}/s3/{SETTINGS.s3_bucket}/{key}")
            eff = f.get("sha256") == v.png_sha if f.get("ok") else False
            m.add("B3", "publica", rep, classify(eff, f.get("status"), f.get("error_kind")), status=f.get("status"))
        else:
            m.add("B3", "publica", rep, (INCONC, "chave do original não encontrada"))
        mu = api.media_url(v.owner, v.owner.id, v.project.id, v.img_id)
        ok = mu.ok and isinstance(mu.json, dict) and api.fetch_sha(mu.json.get("url", "")).get("sha256") == v.png_sha
        m.control("url_assinada_legitima", rep, ok)
    sm = m.summary()
    res.summary("S17", sm)
    return sm


# ---------------------------------------------------------------------------
# S18 - published ports
# ---------------------------------------------------------------------------

LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def run_s18(res: Results, campaign: str) -> dict:
    cfg = dockerctl.delivered_config()
    bindings = []
    for name, svc in sorted(cfg.get("services", {}).items()):
        if name == "nginx":
            continue
        for p in svc.get("ports") or []:
            if p.get("published") in (None, ""):
                continue
            host_ip = p.get("host_ip") or ""
            iface = "loopback" if host_ip in LOOPBACK else "todas"
            bindings.append({"service": name, "published": str(p["published"]), "target": p["target"],
                             "host_ip": host_ip or "0.0.0.0", "interface": iface})
    ip = lan_ip()
    for b in bindings:
        port = int(b["published"].split("-")[0]) + SETTINGS.port_offset
        b["isolated_port"] = port
        b["reach_loopback"] = actions.tcp({"host": "127.0.0.1", "port": port}).get("ok")
        b["reach_lan"] = actions.tcp({"host": ip, "port": port}).get("ok") if ip else None
        res.raw("S18", {"metric": "S18", "campaign": campaign, **b, "t_utc": utc_now()})
    sm = {"todas": sum(b["interface"] == "todas" for b in bindings),
          "loopback": sum(b["interface"] == "loopback" for b in bindings),
          "servicos": sorted({b["service"] for b in bindings}),
          "alcancaveis_lan": sum(bool(b.get("reach_lan")) for b in bindings),
          "lan_ip_testado": ip is not None,
          "lista": [f'{b["service"]}:{b["published"]}->{b["target"]} ({b["host_ip"]})' for b in bindings]}
    res.summary("S18", sm)
    log(f"S18: todas={sm['todas']} loopback={sm['loopback']}")
    return sm


# ---------------------------------------------------------------------------
# S05 - legitimate operations
# ---------------------------------------------------------------------------

def _wait_results(api: API, o: Account, pid: str, n: int, timeout: float = 300) -> list:
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = api.req("GET", f"projects/{o.id}/{pid}/process/url", acct=o)
        if r.ok and isinstance(r.json, dict) and len(r.json.get("imgs") or []) >= n:
            return r.json["imgs"]
        time.sleep(3)
    return []


def run_s05(api: API, res: Results, campaign: str, reps: int, video_path) -> dict:
    steps: list[dict] = []

    def step(name: str, rep: int, ok: bool, note: str = "", policy: bool = False) -> None:
        rec = {"metric": "S05", "campaign": campaign, "rep": rep, "step": name, "ok": bool(ok),
               "note": note, "policy": policy, "t_utc": utc_now()}
        steps.append(rec)
        res.raw("S05", rec)
        log(f"S05 rep{rep} {name}: {'OK' if ok else 'FALHA'} {note}")

    for rep in range(1, reps + 1):
        o = api.register()
        ows = WS("owner")
        ows.connect(o.jwt)
        try:
            p = api.create_project(o, "s05")
            step("L1_criar_projeto", rep, True)
        except Exception as exc:  # noqa: BLE001
            step("L1_criar_projeto", rep, False, repr(exc)[:100])
            continue
        q0 = _remaining_ops(api, o)
        r = api.upload_small(o, p, "img", "a.png", png_bytes(seed=50), "image/png")
        step("L2_upload_imagem", rep, r.ok, f"HTTP {r.status}")
        r = api.upload_small(o, p, "video", "v.mp4", video_path.read_bytes(), "video/mp4")
        step("L3_upload_video", rep, r.ok, f"HTTP {r.status}")
        q1 = _remaining_ops(api, o)
        step("L12a_upload_nao_debita_quota", rep, q0 is not None and q0 == q1, f"{q0}->{q1}")
        r = api.add_tool(o, p)
        step("L4_adicionar_ferramenta", rep, r.ok, f"HTTP {r.status}")
        view = api.owner_view(p) or {}
        n_media = len(view.get("imgs") or [])
        t_proc = time.monotonic() * 1000
        r = api.req("POST", f"projects/{o.id}/{p.id}/process", acct=o,
                    headers={"X-Project-Version": str(p.version)}, json={})
        results = _wait_results(api, o, p.id, n_media) if r.ok else []
        step("L5_aplicar_pipeline", rep, r.ok and len(results) >= n_media, f"HTTP {r.status}, {len(results)}/{n_media}")
        ok = bool(results) and api.fetch_sha(results[0].get("url", "")).get("ok")
        step("L6_descarregar_resultado", rep, bool(ok))
        step("L7_evento_process_update", rep, bool(ows.named("process-update", since=t_proc)))
        q2 = _remaining_ops(api, o)
        step("L12b_apply_debita_quota", rep, q0 is not None and q2 is not None and q2 < q0, f"{q0}->{q2}")
        img_id = next((str(i["_id"]) for i in (api.owner_view(p) or {}).get("imgs", [])
                       if i.get("media_type") != "video"), None)
        t_prev = time.monotonic() * 1000
        r = api.req("POST", f"projects/{o.id}/{p.id}/preview/{img_id}", acct=o,
                    headers={"X-Project-Version": str(p.version)}, json={}) if img_id else None
        got = False
        deadline = time.time() + 120
        while r is not None and r.ok and time.time() < deadline and not got:
            got = bool(ows.named("preview-ready", since=t_prev))
            time.sleep(1)
        step("L8_preview", rep, got, "" if r is None else f"HTTP {r.status}")

        reader, editor = api.register(), api.register()
        rs, es = api.share_create(p, "read"), api.share_create(p, "edit")
        api.share_resolve(reader, rs)
        api.share_resolve(editor, es)
        r = api.get_project(reader, o.id, p.id, params={"share": rs})
        step("L9_leitor_le", rep, r.ok and _resp_id(r) == p.id, f"HTTP {r.status}")
        before = count(api.owner_view(p), "tools")
        r = api.add_tool(editor, p, query={"share": es}, version=p.version)
        after = count(api.owner_view(p), "tools")
        step("L10_editor_edita", rep, r.ok and after is not None and before is not None and after > before,
             f"HTTP {r.status}")
        view = api.owner_view(p) or {}
        mid = str(view["imgs"][0]["_id"]) if view.get("imgs") else None
        before = count(view, "imgs")
        r = api.req("DELETE", f"projects/{o.id}/{p.id}/img/{mid}", acct=editor, params={"share": es},
                    headers={"X-Project-Version": str(p.version)}) if mid else None
        after = count(api.owner_view(p), "imgs")
        step("L11_editor_remove_media", rep, r is not None and r.ok and after is not None and after < (before or 0),
             "" if r is None else f"HTTP {r.status}")
        s = api.register()
        okf = api.subscription_fixture(s)
        r = api.req("GET", f"subscriptions/{s.id}/status", acct=s)
        step("L13_subscricao_propria", rep, okf and r.ok, f"HTTP {r.status}")
        api.owner_view(p)
        r = api.req("DELETE", f"projects/{o.id}/{p.id}", acct=o, headers={"X-Project-Version": str(p.version)})
        listed = _project_listed(api, o, p.id)
        step("L14_dono_elimina_projeto", rep, r.ok and listed is False, f"HTTP {r.status}")
        # ACL-C1 policy change: recorded, not counted.
        p3 = api.create_project(o, "policy")
        es3 = api.share_create(p3, "edit")
        ed3 = api.register()
        api.share_resolve(ed3, es3)
        api.owner_view(p3)
        r = api.req("DELETE", f"projects/{o.id}/{p3.id}", acct=ed3, params={"share": es3},
                    headers={"X-Project-Version": str(p3.version)})
        listed = _project_listed(api, o, p3.id)
        step("P1_editor_elimina_projeto", rep, listed is False, f"HTTP {r.status}; eliminado={listed is False}",
             policy=True)
        ows.close()
    counted = [s for s in steps if not s["policy"]]
    sm = {"total": len(counted), "ok": sum(s["ok"] for s in counted),
          "fracao": (sum(s["ok"] for s in counted) / len(counted)) if counted else None,
          "falhas": sorted({s["step"] for s in counted if not s["ok"]}),
          "politica_acl_editor_elimina": [s["ok"] for s in steps if s["policy"]]}
    res.summary("S05", sm)
    return sm


# ---------------------------------------------------------------------------
# S21 - light-request latency
# ---------------------------------------------------------------------------

def run_s21(api: API, res: Results, campaign: str, n: int = 100, warmup: int = 10) -> dict:
    import requests
    a = api.premium()
    p = api.create_project(a, "s21")
    sess = requests.Session()
    sess.verify = SETTINGS.verify()
    kinds = {"get_project": f"projects/{a.id}/{p.id}", "get_user": f"users/{a.id}"}
    out = {}
    for kind, path in kinds.items():
        for _ in range(warmup):
            api.req("GET", path, acct=a, session=sess)
        times, errors = [], 0
        for i in range(n):
            r = api.req("GET", path, acct=a, session=sess)
            if not r.ok:
                errors += 1
            times.append(r.ms)
            res.raw("S21", {"metric": "S21", "campaign": campaign, "kind": kind, "i": i,
                            "ms": round(r.ms, 3), "status": r.status})
        out[kind] = {"mediana_ms": round(median(times), 3), "max_ms": round(max(times), 3),
                     "min_ms": round(min(times), 3), "erros": errors, "n": n}
        log(f"S21 {kind}: mediana {out[kind]['mediana_ms']} ms")
    res.summary("S21", out)
    return out
