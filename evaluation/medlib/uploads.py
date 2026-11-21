"""Upload metrics: U01, U04, U08, U09, U10, U15, U17, U18, U19, U20, U25 (plan §8)."""
from __future__ import annotations

import json
import threading
import time
from typing import Callable

from . import corpus, dockerctl, monitor
from .api import API, Account, Project
from .config import MIB, SETTINGS
from .security import forged_jwt
from .upload import upload
from .util import Results, log, maximum, median, utc_now

NODE = monitor.NODE_SERVICES
ZERO_ID = "000000000000000000000000"


class Uploader:
    def __init__(self, api: API, res: Results, campaign: str):
        self.api, self.res, self.campaign = api, res, campaign
        self.files = corpus.load()
        self.accounts: dict[str, Account] = {}

    # ---- helpers ------------------------------------------------------------
    def account(self, profile: str, fresh: bool = False) -> Account:
        if fresh or profile not in self.accounts:
            self.accounts[profile] = self.api.premium() if profile == "premium" else self.api.register()
        return self.accounts[profile]

    def project(self, profile: str) -> Project:
        try:
            return self.api.create_project(self.account(profile), "upl")
        except RuntimeError:
            return self.api.create_project(self.account(profile, fresh=True), "upl")

    def url(self, acct_id: str, pid: str) -> str:
        return f"{SETTINGS.gw}projects/{acct_id}/{pid}/video"

    def ensure_alive(self) -> None:
        """After a failure, always restart the Node services and nginx, then wait.

        Checking `running` is not enough: under nodemon an OOM-killed app leaves the
        container up and the service dead."""
        log("a reiniciar serviços Node + nginx após falha")
        dockerctl.restart_app()
        self.wait_api()

    def healthy(self) -> bool:
        try:
            r = self.api.req("GET", f"users/{self.account('premium').id}", timeout=10)
            return r.status is not None and r.status < 500
        except Exception:  # noqa: BLE001
            self.accounts.pop("premium", None)
            return False

    def ensure_healthy(self) -> None:
        if not self.healthy():
            self.ensure_alive()

    def wait_api(self, timeout: float = 300) -> None:
        """Wait until the API serves an authenticated request after a restart.

        Everything (including creating the account) is retried: right after a
        restart nginx answers 502 for a few seconds. If 502 persists for 60 s,
        nginx is restarted too (it may keep a stale upstream)."""
        start = time.time()
        nginx_restarted = False
        last = None
        while time.time() - start < timeout:
            try:
                a = self.account("premium")
                p = self.api.create_project(a, "ready")
                if self.api.get_project(a, a.id, p.id).ok:
                    return
            except Exception as exc:  # noqa: BLE001
                last = exc
                if "register" in repr(exc) or "premium fixture" in repr(exc):
                    self.accounts.pop("premium", None)
            if not nginx_restarted and time.time() - start > 60 and "502" in repr(last):
                log("502 persistente: a reiniciar o nginx do projeto isolado")
                dockerctl.restart(["nginx"])
                nginx_restarted = True
            time.sleep(3)
        raise RuntimeError(f"API not ready after restart ({last!r})")

    def verify(self, p: Project, sha: str) -> dict:
        """U17 (media associated as video) and U15 (SHA-256 of the stored original)."""
        view = self.api.owner_view(p) or {}
        media = view.get("imgs") or []
        ok17 = len(media) == 1 and media[0].get("media_type") == "video"
        ok15 = None
        if media:
            mu = self.api.media_url(p.owner, p.owner.id, p.id, str(media[0]["_id"]))
            url = mu.json.get("url") if mu.ok and isinstance(mu.json, dict) else None
            if url:
                f = self.api.fetch_sha(url)
                ok15 = f.get("sha256") == sha if f.get("ok") else False
        return {"u17_ok": ok17, "u15_ok": ok15, "media": len(media)}

    def measured(self, label: str, profile: str, fname: str, *, window: bool = True,
                 cgroup=("nginx", "seaweedfs"), headers: dict | None = None, rate: float | None = None,
                 project: Project | None = None, verify: bool = True, ctype: str = "video/mp4",
                 path_ids: tuple[str, str] | None = None) -> dict:
        meta = self.files[fname]
        p = project or (None if path_ids else self.project(profile))
        hdrs = dict(headers if headers is not None else {**p.owner.bearer, "X-Project-Version": str(p.version)})
        url = self.url(*(path_ids or (p.owner.id, p.id)))
        mems = monitor.node_reset_all()
        win = monitor.Window(cgroup_services=cgroup).start() if window else None
        rec = upload(url, field="video", filename=fname, ctype=ctype, path=corpus.path(fname),
                     headers=hdrs, rate_mib_s=rate)
        time.sleep(0.7)
        rec["mem"] = monitor.node_read_all(mems)
        if win:
            rec.update(win.stop())
        rec.update({"label": label, "profile": profile, "file": fname, "file_bytes": meta["bytes"],
                    "t_utc": utc_now(), "campaign": self.campaign})
        ok = rec.get("status") is not None and 200 <= rec["status"] < 300
        if ok and verify and p is not None:
            rec.update(self.verify(p, meta["sha256"]))
        rec["oom_any"] = any(v.get("oom") for v in rec["mem"].values())
        rec["restart_any"] = any(v.get("restarted") for v in rec["mem"].values())
        rec["project_id"] = None if p is None else p.id
        return rec

    # ---- strata: U01/U04/U08/U09/U10/U15/U17 --------------------------------
    def strata(self, attempts: int = 5, quick: bool = False) -> list[dict]:
        plan = [("free", 10), ("free", 100), ("premium", 10), ("premium", 100), ("premium", 500)]
        positions, states = ("H", "T"), ("frio", "aquecido")
        if quick:
            plan, positions, states, attempts = [("premium", 10)], ("H",), ("aquecido",), 1
        records = []
        for profile, size in plan:
            for pos in positions:
                for state in states:
                    stratum = f"{profile}-{size}-{pos}-{state}"
                    fname = f"pad_{size}MiB_{pos}.mp4"
                    snap0 = monitor.disk_snapshot_all()
                    if state == "aquecido":
                        warm = self.measured(f"{stratum}-warmup", profile, "pad_10MiB_H.mp4", window=False,
                                             verify=False)
                        self.res.raw("U_warmup", warm)
                    for i in range(1, attempts + 1):
                        if state == "frio":
                            dockerctl.restart_app()
                            self.wait_api()
                        rec = self.measured(stratum, profile, fname)
                        rec.update({"stratum": stratum, "attempt": i, "size_mib": size, "moov": pos,
                                    "state": state})
                        self.res.raw("U_strata", rec)
                        records.append(rec)
                        log(f"{stratum} #{i}: HTTP {rec.get('status')} post_send={_r(rec.get('post_send_ms'))} ms "
                            f"gw+{_r(rec['mem']['api_gateway'].get('delta_mib'))} MiB")
                        if rec["oom_any"] or not (rec.get("status") and 200 <= rec["status"] < 300):
                            time.sleep(8)
                            self.ensure_alive()
                        else:
                            time.sleep(1.5)
                    log(f"{stratum}: waiting 60 s for residual temp files")
                    time.sleep(60)
                    snap1 = monitor.disk_snapshot_all()
                    resid = {s: {"kib": _diff(snap1[s]["kib"], snap0[s]["kib"]),
                                 "files": _diff(snap1[s]["files"], snap0[s]["files"])} for s in snap0}
                    self.res.raw("U08_residuals", {"stratum": stratum, "residual": resid, "t_utc": utc_now()})
                    for r in records:
                        if r.get("stratum") == stratum:
                            r["residual"] = resid
        self.summarise_strata(records)
        return records

    def summarise_strata(self, records: list[dict]) -> None:
        summarise_strata(self.res, records)

    # ---- U04 -----------------------------------------------------------------
    def wait_s3(self, timeout: float = 180) -> None:
        """After a SeaweedFS restart its S3 API takes ~20 s to come up; an upload sent
        earlier fails with 501 "Error storing image" (seen in the first U04 attempt)."""
        from .api import s3_admin_keys
        start, last = time.time(), None
        while time.time() - start < timeout:
            try:
                s3_admin_keys("users/")
                return
            except Exception as exc:  # noqa: BLE001
                last = exc
            time.sleep(2)
        raise RuntimeError(f"SeaweedFS S3 not ready after restart ({last!r})")

    def seaweed_cold(self, samples: int = 5, max_attempts: int = 40, quick: bool = False) -> dict:
        """U04: extra anonymous memory of nginx and SeaweedFS for one 500 MiB upload.

        SeaweedFS (Go) keeps the memory it took for earlier uploads and reuses it, so
        a delta measured after other uploads is ~0 by chance. Every sample therefore
        starts from the same state: SeaweedFS, the Node services and nginx restarted.
        Only accepted uploads (2xx) count: if the gateway dies first, the file never
        reaches SeaweedFS."""
        if quick:
            samples, max_attempts = 1, 3
        fname = "pad_500MiB_H.mp4"
        # On --resume, samples already taken with this same method count (the base
        # gateway survives only a minority of 500 MiB uploads).
        prev = self.res.path / "raw" / "U04.jsonl"
        recs = [json.loads(l) for l in prev.read_text().splitlines() if l.strip()] if prev.exists() else []
        valid, attempt = sum(1 for r in recs if _ok(r)), len(recs)
        while valid < samples and attempt < max_attempts:
            attempt += 1
            dockerctl.restart(["seaweedfs"])
            self.wait_s3()
            dockerctl.restart_app()
            self.wait_api()
            time.sleep(5)  # let SeaweedFS settle before the idle reading
            rec = self.measured("U04-seaweedfs-frio", "premium", fname)
            rec.update({"attempt": attempt, "size_mib": 500})
            ok = _ok(rec)
            valid += ok
            self.res.raw("U04", rec)
            recs.append(rec)
            sw = rec.get("cgroup", {}).get("seaweedfs", {})
            log(f"U04 #{attempt}: HTTP {rec.get('status')} seaweedfs idle={sw.get('idle_anon_mib')} "
                f"pico={sw.get('peak_anon_mib')} delta={sw.get('delta_anon_mib')} MiB")
            if not ok:
                time.sleep(8)
        good = [r for r in recs if _ok(r)]
        sm = {"tentativas": attempt, "validas": len(good), "pedidas": samples, "estado_inicial": "reiniciado"}
        for c in ("nginx", "seaweedfs"):
            ds = [r.get("cgroup", {}).get(c, {}).get("delta_anon_mib") for r in good]
            idle = [r.get("cgroup", {}).get(c, {}).get("idle_anon_mib") for r in good]
            sm[c] = {"max_delta_anon_mib": maximum(ds), "mediana_delta_anon_mib": median(ds), "n": len(good),
                     "idle_min_mib": min((x for x in idle if x is not None), default=None),
                     "idle_max_mib": maximum(idle)}
        self.res.summary("U04", sm)
        return sm

    # ---- U18 -----------------------------------------------------------------
    def invalid(self, reps: int = 3) -> dict:
        cases = [("I1", "free", "pad_500MiB_H.mp4", "video/mp4"),
                 ("I2", "free", "too_long_90s.mp4", "video/mp4"),
                 ("I3", "free", "corrupted.mp4", "video/mp4"),
                 ("I4", "free", "empty.mp4", "video/mp4"),
                 ("I5", "free", "image.png", "image/png"),
                 ("I6", "premium", "pad_1024MiB_plus1_H.mp4", "video/mp4"),
                 ("I7", "free", "speech_mandela_177s_1080p.webm", "video/webm")]
        out = []
        for rep in range(1, reps + 1):
            for case, profile, fname, ctype in cases:
                p = self.project(profile)
                rec = self.measured(f"U18-{case}", profile, fname, ctype=ctype, project=p, verify=False)
                media = len((self.api.owner_view(p) or {}).get("imgs") or []) if not rec["restart_any"] else None
                status = rec.get("status")
                correct = (status is not None and 400 <= status < 500 and media == 0
                           and not rec["oom_any"] and not rec["restart_any"])
                rec.update({"case": case, "rep": rep, "media_after": media, "correct": correct})
                self.res.raw("U18", rec)
                out.append(rec)
                log(f"U18 {case} rep{rep}: HTTP {status} correct={correct} oom={rec['oom_any']}")
                if rec["restart_any"] or rec["oom_any"] or status is None or status >= 500:
                    time.sleep(8)
                    self.ensure_alive()
        sm = {"casos": len(out), "corretos": sum(r["correct"] for r in out),
              "fracao": _frac(sum(r["correct"] for r in out), len(out)),
              "oom": sum(r["oom_any"] for r in out),
              "falhas": sorted({f'{r["case"]}:HTTP {r.get("status")}' for r in out if not r["correct"]})}
        self.res.summary("U18", sm)
        return sm

    # ---- U19 -----------------------------------------------------------------
    def no_token(self, reps: int = 5, bad_sig_reps: int = 3) -> dict:
        out = []
        variants = [("sem_token", {}, reps),
                    ("assinatura_errada", {"Authorization": f"Bearer {forged_jwt(ZERO_ID)}"}, bad_sig_reps)]
        for name, hdrs, n in variants:
            for rep in range(1, n + 1):
                rec = self.measured(f"U19-{name}", "none", "pad_500MiB_H.mp4", headers=hdrs, rate=50,
                                    path_ids=(ZERO_ID, ZERO_ID), verify=False, cgroup=("nginx",))
                rec.update({"variant": name, "rep": rep})
                self.res.raw("U19", rec)
                out.append(rec)
                log(f"U19 {name} rep{rep}: HTTP {rec.get('status')} after_headers="
                    f"{_r(rec.get('response_after_headers_ms'))} ms gw+{_r(rec['mem']['api_gateway'].get('delta_mib'))} MiB")
                if rec["restart_any"] or rec["oom_any"] or rec.get("status") is None or rec["status"] >= 500:
                    self.ensure_alive()
                time.sleep(3)
        sm = {"tentativas": len(out),
              "status": sorted({str(r.get("status")) for r in out}),
              "todas_401_403": all(r.get("status") in (401, 403) for r in out),
              "gateway_delta_max_mib": maximum(r["mem"]["api_gateway"].get("delta_mib") for r in out),
              "resposta_apos_cabecalhos_max_ms": maximum(r.get("response_after_headers_ms") for r in out),
              "bytes_enviados_ate_resposta_max": maximum(r.get("bytes_sent_at_response") if r.get("early_response")
                                                         else r.get("bytes_sent") for r in out),
              "nginx_delta_anon_max_mib": maximum(r.get("cgroup", {}).get("nginx", {}).get("delta_anon_mib")
                                                  for r in out),
              "nginx_disco_pico_max_kib": maximum(r.get("disk", {}).get("nginx", {}).get("delta_peak_kib")
                                                  for r in out),
              "oom": sum(r["oom_any"] for r in out)}
        self.res.summary("U19", sm)
        return sm

    # ---- U20 -----------------------------------------------------------------
    def concurrent(self, rounds: int = 3) -> dict:
        accts = [self.api.premium() for _ in range(3)]
        fname = "pad_500MiB_H.mp4"
        meta = self.files[fname]
        out = []
        for rnd in range(1, rounds + 1):
            projects = [self.api.create_project(a, "c3") for a in accts]
            mems = monitor.node_reset_all()
            win = monitor.Window(cgroup_services=("nginx", "seaweedfs") + NODE).start()
            barrier = threading.Barrier(3)
            results: list[dict | None] = [None, None, None]

            def worker(i: int) -> None:
                p = projects[i]
                barrier.wait()
                results[i] = upload(self.url(p.owner.id, p.id), field="video", filename=fname, ctype="video/mp4",
                                    path=corpus.path(fname),
                                    headers={**p.owner.bearer, "X-Project-Version": str(p.version)})
            ths = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
            for t in ths:
                t.start()
            for t in ths:
                t.join()
            time.sleep(0.7)
            mem = monitor.node_read_all(mems)
            w = win.stop()
            per = []
            for i, r in enumerate(results):
                r = r or {"status": None}
                ok = r.get("status") is not None and 200 <= r["status"] < 300
                v = self.verify(projects[i], meta["sha256"]) if ok else {}
                per.append({"status": r.get("status"), "total_ms": r.get("total_ms"),
                            "post_send_ms": r.get("post_send_ms"), **v,
                            "sucesso": bool(ok and v.get("u17_ok") and v.get("u15_ok"))})
            rec = {"metric": "U20", "campaign": self.campaign, "round": rnd, "uploads": per, "mem": mem, **w,
                   "sucessos": sum(x["sucesso"] for x in per),
                   "oom": any(v.get("oom") for v in mem.values()),
                   "reinicios": any(v.get("restarted") for v in mem.values()), "t_utc": utc_now()}
            self.res.raw("U20", rec)
            out.append(rec)
            log(f"U20 round {rnd}: {rec['sucessos']}/3 oom={rec['oom']} restarts={rec['reinicios']}")
            if rec["oom"] or rec["reinicios"] or rec["sucessos"] < 3:
                self.ensure_alive()
            time.sleep(30)
        sm = {"rondas": [{"round": r["round"], "sucessos": r["sucessos"], "oom": r["oom"],
                          "reinicios": r["reinicios"]} for r in out],
              "rondas_3de3_sem_oom": sum(1 for r in out if r["sucessos"] == 3 and not r["oom"] and not r["reinicios"]),
              "oom_total": sum(r["oom"] for r in out),
              "pico_agregado_anon_mib": maximum(sum(c.get("peak_anon_mib") or 0 for c in r.get("cgroup", {}).values())
                                                for r in out)}
        self.res.summary("U20", sm)
        return sm

    # ---- U25 -----------------------------------------------------------------
    def coexistence(self, pairs: int = 3, n: int = 100, rate_hz: float = 10.0) -> dict:
        import requests
        light = self.api.premium()
        lp = self.api.create_project(light, "light")
        paths = [f"users/{light.id}", f"projects/{light.id}/{lp.id}"]
        uploaders = [self.api.premium() for _ in range(3)]
        fname = "pad_500MiB_H.mp4"

        def burst(active: Callable[[], bool] | None) -> list[dict]:
            """Control: exactly n requests. Load: keep going for the whole lifetime of
            the uploads (sending AND waiting for the response, when memory peaks)."""
            sess = requests.Session()
            sess.verify = SETTINGS.verify()
            out, i = [], 0
            while True:
                if active is None and len(out) >= n:
                    break
                if active is not None and not active():
                    break
                t = time.monotonic()
                r = self.api.req("GET", paths[i % 2], acct=light, session=sess, timeout=30)
                out.append({"ms": r.ms, "ok": r.status == 200, "status": r.status})
                i += 1
                time.sleep(max(0.0, 1 / rate_hz - (time.monotonic() - t)))
            return out

        results = []
        for pair in range(1, pairs + 1):
            self.ensure_healthy()
            control = burst(None)
            load: list[dict] = []
            uploads: list[dict] = []
            gw_before = dockerctl.state("api_gateway")
            for attempt in range(3):
                projects = [self.api.create_project(a, "u25") for a in uploaders]
                uploads = [{} for _ in projects]

                def run_upload(i: int, p: Project) -> None:
                    uploads[i] = upload(self.url(p.owner.id, p.id), field="video", filename=fname,
                                        ctype="video/mp4", path=corpus.path(fname), rate_mib_s=40,
                                        headers={**p.owner.bearer, "X-Project-Version": str(p.version)})
                threads = [threading.Thread(target=run_upload, args=(i, p)) for i, p in enumerate(projects)]
                for t in threads:
                    t.start()
                time.sleep(1)
                load = burst(lambda: any(t.is_alive() for t in threads))
                for t in threads:
                    t.join()
                if len(load) >= n:
                    break
                log(f"U25 pair {pair}: only {len(load)} requests during uploads, repeating")
                self.ensure_alive()
            change = dockerctl.state_change(gw_before, dockerctl.state("api_gateway"))
            app_dead = not self.healthy()
            med_c = median(x["ms"] for x in control)
            med_l = median(x["ms"] for x in load)
            rec = {"metric": "U25", "campaign": self.campaign, "pair": pair,
                   "controlo": {"n": len(control), "erros": sum(not x["ok"] for x in control), "mediana_ms": med_c},
                   "carga": {"n": len(load), "erros": sum(not x["ok"] for x in load), "mediana_ms": med_l,
                             "max_ms": maximum(x["ms"] for x in load),
                             "estados_erro": sorted({str(x["status"]) for x in load if not x["ok"]})},
                   "uploads": [{"status": u.get("status"), "total_ms": u.get("total_ms")} for u in uploads],
                   "gateway_oom": change["oom"], "gateway_reiniciado": change["restarted"],
                   "aplicacao_indisponivel_no_fim": app_dead,
                   "razao": None if not med_c or med_l is None else med_l / med_c,
                   "suficiente": len(load) >= n, "t_utc": utc_now()}
            self.res.raw("U25", rec)
            results.append(rec)
            log(f"U25 pair {pair}: ratio={_r(rec['razao'])} errors={rec['carga']['erros']} "
                f"uploads={[u['status'] for u in rec['uploads']]} gateway_oom={change['oom']}")
            if app_dead or change["oom"]:
                self.ensure_alive()
            time.sleep(10)
        sm = {"pares": [{"pair": r["pair"], "razao": r["razao"], "erros_carga": r["carga"]["erros"],
                         "n_carga": r["carga"]["n"], "suficiente": r["suficiente"],
                         "gateway_oom": r["gateway_oom"]} for r in results],
              "razao_max": maximum(r["razao"] for r in results),
              "erros_total": sum(r["carga"]["erros"] for r in results),
              "pares_insuficientes": sum(not r["suficiente"] for r in results)}
        self.res.summary("U25", sm)
        return sm



def _r(x) -> str:
    return "-" if x is None else f"{x:.1f}"


def _diff(a, b):
    return None if a is None or b is None else a - b


def _frac(a: int, b: int):
    return None if not b else a / b


def _ok(r: dict) -> bool:
    return bool(r.get("status")) and 200 <= r["status"] < 300


def summarise_strata(res: Results, records: list[dict]) -> None:
    """U01/U04/U08/U09/U10/U15/U17 from the stratum records (also used by
    `med.py report --resummarise`, which rebuilds them from raw/)."""
    # U01
    u01 = {}
    for svc in NODE:
        per_size = {}
        for size in sorted({r["size_mib"] for r in records}):
            ds = [r["mem"][svc].get("delta_mib") for r in records if r["size_mib"] == size]
            died = sum(1 for r in records if r["size_mib"] == size and r["mem"][svc].get("process_died"))
            per_size[str(size)] = {"max_mib": maximum(ds), "mediana_mib": median(ds), "n": len(ds),
                                   "processo_morreu": died}
        u01[svc] = {"max_mib": maximum(v["max_mib"] for v in per_size.values()), "por_tamanho": per_size,
                    "reset_hwm_ok": all(r["mem"][svc].get("hwm_reset") for r in records)}
    res.summary("U01", {"por_servico": u01, "oom": sum(r["oom_any"] for r in records)})
    # U04 has its own step (Uploader.seaweed_cold): SeaweedFS keeps memory between uploads.
    # U08
    u08 = {}
    disk_services = list(dict.fromkeys(k for r in records for k in r.get("disk", {})))
    for svc in disk_services:
        rows = []
        for r in records:
            d = r.get("disk", {}).get(svc, {})
            if d.get("delta_peak_kib") is not None:
                rows.append((r["file_bytes"], d["delta_peak_kib"] * 1024))
        ratio = [b / (f + 16 * MIB) for f, b in rows if f]
        u08[svc] = {"pico_max_mib": round(max((b for _, b in rows), default=0) / MIB, 1),
                    "max_razao_pico_sobre_F_mais_16MiB": round(max(ratio), 3) if ratio else None,
                    "residuo_max_kib": maximum(r.get("residual", {}).get(svc, {}).get("kib") for r in records),
                    "residuo_max_ficheiros": maximum(r.get("residual", {}).get(svc, {}).get("files")
                                                     for r in records)}
    res.summary("U08", {"por_componente": u08, "concorrencia": 1})
    # U09: only accepted uploads have an acceptance time; failures are counted apart
    big500 = [r for r in records if r["size_mib"] == 500 and r["profile"] == "premium"]
    u09 = [r.get("post_send_ms") for r in big500 if _ok(r)]
    other = {str(s): median(r.get("post_send_ms") for r in records if r["size_mib"] == s and _ok(r))
             for s in sorted({r["size_mib"] for r in records})}
    res.summary("U09", {"amostras_500_ms": u09, "max_500_ms": maximum(u09), "mediana_500_ms": median(u09),
                        "tentativas_500": len(big500), "falhas_500": len(big500) - len(u09),
                        "estados_falhas_500": sorted(str(r.get("status") or r.get("error")) for r in big500
                                                     if not _ok(r)),
                        "mediana_por_tamanho_ms": other})
    # U10: median over accepted uploads only (a fast 502 is not a fast upload)
    strata_ids = sorted({r["stratum"] for r in records})
    res.summary("U10", {
        "mediana_total_ms_por_estrato": {
            s: median(r.get("total_ms") for r in records if r["stratum"] == s and _ok(r)) for s in strata_ids},
        "aceites_por_estrato": {
            s: f'{sum(1 for r in records if r["stratum"] == s and _ok(r))}/'
               f'{sum(1 for r in records if r["stratum"] == s)}' for s in strata_ids}})
    # U15 / U17
    accepted = [r for r in records if _ok(r)]
    res.summary("U15", {"verificados": sum(r.get("u15_ok") is not None for r in accepted),
                        "iguais": sum(bool(r.get("u15_ok")) for r in accepted), "aceites": len(accepted),
                        "fracao": _frac(sum(bool(r.get("u15_ok")) for r in accepted), len(accepted))})
    good = sum(1 for r in records if _ok(r) and r.get("u17_ok"))
    res.summary("U17", {"tentativas": len(records), "aceites_corretamente": good,
                        "fracao": _frac(good, len(records))})
