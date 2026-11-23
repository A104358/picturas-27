#!/usr/bin/env python3
"""PictuRAS Phase 2 measurement tool (specification: docs/planoMedicao.md).

    python evaluation/med.py preflight [--campaign BF|MF|EXP]
    python evaluation/med.py stack up|down|status|purge [--corpus]
    python evaluation/med.py corpus
    python evaluation/med.py run --campaign BF|MF|EXP [--suite security|upload|all] [--metrics S01,U01] [--quick]
    python evaluation/med.py report <results_dir>
    python evaluation/med.py compare <dir_BF> <dir_MF>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import traceback
import weakref
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from medlib import VERSION, corpus, dockerctl, report  # noqa: E402
from medlib.config import (APP_PATHS, CASES_FILE, CORPUS_DIR, CRITERIA_FILE, EVAL_DIR, REPO,  # noqa: E402
                           RESULTS_DIR, SETTINGS)
from medlib.util import Results, log, sha256_file, utc_now, utc_stamp  # noqa: E402

UPLOAD_STRATA = {"U01", "U08", "U09", "U10", "U15", "U17"}
SECURITY_ORDER = ["S18", "S01", "S02", "S03", "S04", "S16", "S17", "S12", "S05", "S21"]
UPLOAD_ORDER = ["STRATA", "U04", "U18", "U19", "U20", "U25"]


# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------

def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True).stdout.strip()


def preflight(campaign: str = "EXP", strict: bool | None = None) -> dict:
    strict = campaign in ("BF", "MF") if strict is None else strict
    checks: dict[str, dict] = {}

    def check(name: str, ok: bool, detail: str, fatal: bool = True) -> None:
        checks[name] = {"ok": ok, "detail": detail, "fatal": fatal}
        log(f"preflight {name}: {'OK' if ok else ('FALHA' if fatal else 'AVISO')} - {detail}")

    try:
        dockerctl.guard_project()
        check("projeto_isolado", True, SETTINGS.project)
    except SystemExit as exc:
        check("projeto_isolado", False, str(exc))
    for channel in ("s3", "amqp", "rabbit_mgmt", "mongo"):
        path = getattr(SETTINGS, f"{channel}_ca_file")
        if path:
            check(f"ca_{channel}", Path(path).is_file(), "CA disponível" if Path(path).is_file() else "CA ausente")
    check("esquemas_dados", SETTINGS.s3_scheme in ("http", "https") and
          SETTINGS.rabbit_mgmt_scheme in ("http", "https"), "S3/RabbitMQ management")
    free_gib = shutil.disk_usage(REPO).free / 2**30
    check("disco_livre", free_gib >= SETTINGS.min_free_gib, f"{free_gib:.1f} GiB (mínimo {SETTINGS.min_free_gib})")
    info = _docker_info()
    check("docker", bool(info), "docker info" if info else "docker indisponível")
    if info:
        check("docker_cpus", info.get("NCPU", 0) >= 8, f"{info.get('NCPU')} CPUs")
        check("docker_mem", info.get("MemTotal", 0) >= 8 * 2**30 * 0.95, f"{info.get('MemTotal', 0) / 2**30:.1f} GiB")
    check("ffmpeg", bool(shutil.which("ffmpeg") and shutil.which("ffprobe")), "ffmpeg/ffprobe no PATH")
    dirty = _git("status", "--porcelain", "--", *APP_PATHS)
    check("arvore_limpa", not dirty, "sem alterações locais na aplicação" if not dirty else dirty[:300],
          fatal=strict)
    if campaign == "BF":
        diff = _git("diff", "--stat", SETTINGS.base_commit, "--", *APP_PATHS)
        check("codigo_base", not diff, f"igual a {SETTINGS.base_commit}" if not diff else diff[-300:])
    failed = [k for k, v in checks.items() if not v["ok"] and v["fatal"]]
    return {"ok": not failed, "failed": failed, "checks": checks}


def _docker_info() -> dict:
    r = subprocess.run(["docker", "info", "--format", "{{json .}}"], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------

def _cpu_model() -> str:
    if sys.platform == "darwin":
        r = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True)
        return r.stdout.strip()
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor()


def _nginx_config() -> dict:
    out = dockerctl.exec_sh("nginx", "nginx -T 2>/dev/null", check=False, timeout=30)
    body = re.findall(r"client_max_body_size\s+([^;]+);", out)
    buf = re.findall(r"proxy_request_buffering\s+([^;]+);", out)
    from medlib.monitor import nginx_temp_dir
    return {"client_max_body_size": body, "proxy_request_buffering": buf or ["on (omissão)"],
            "client_body_temp_path": nginx_temp_dir()}


def manifest(campaign: str, pre: dict) -> dict:
    info = _docker_info()
    corpus_files = corpus.load() if (CORPUS_DIR / "corpus.json").exists() else {}
    head = _git("rev-parse", "HEAD")
    return {
        "campaign": campaign,
        "started_at": utc_now(),
        "med_version": VERSION,
        "git": {"head": head, "app_dirty": _git("status", "--porcelain", "--", *APP_PATHS),
                "base_commit": SETTINGS.base_commit,
                "diff_stat_vs_base": _git("diff", "--stat", SETTINGS.base_commit, "--", *APP_PATHS)[-2000:]},
        "instrumento": instrument_hashes(),
        "hashes": {
            "med_py": sha256_file(Path(__file__)),
            "medlib": _dir_hash(EVAL_DIR / "medlib"),
            "criteria": sha256_file(CRITERIA_FILE),
            "cases": sha256_file(CASES_FILE),
            "compose": sha256_file(REPO / "docker-compose.yaml"),
            "override": sha256_file(dockerctl.OVERRIDE_FILE) if dockerctl.OVERRIDE_FILE.exists() else None,
            "override_limits": hashlib.sha256(
                f"{dockerctl.LIMITED_SERVICES}:cpus=2:mem=2g:offset={SETTINGS.port_offset}".encode()).hexdigest(),
        },
        "host": {"uname": " ".join(platform.uname()), "machine": platform.machine(), "cpu": _cpu_model(),
                 "python": platform.python_version(),
                 "disk_free_gib": round(shutil.disk_usage(REPO).free / 2**30, 1)},
        "docker": {"ncpu": info.get("NCPU"), "mem_total": info.get("MemTotal"), "kernel": info.get("KernelVersion"),
                   "cgroup_version": info.get("CgroupVersion"), "driver": info.get("Driver"),
                   "server_version": info.get("ServerVersion"), "os": info.get("OperatingSystem")},
        "images": dockerctl.image_ids(),
        "corpus": {k: {kk: v[kk] for kk in ("bytes", "sha256", "kind") if kk in v} | {"moov": v.get("moov")}
                   for k, v in corpus_files.items()},
        "corpus_sha": hashlib.sha256(json.dumps({k: v["sha256"] for k, v in sorted(corpus_files.items())})
                                     .encode()).hexdigest() if corpus_files else None,
        "nginx": _nginx_config(),
        "tls_client_verification": "cacert" if SETTINGS.cacert else "desligada (nginx autoassinado)",
        "data_channels": {"s3_scheme": SETTINGS.s3_scheme, "s3_ca": bool(SETTINGS.s3_ca_file),
                          "amqp_port": SETTINGS.amqp_port, "amqp_ca": bool(SETTINGS.amqp_ca_file),
                          "rabbit_mgmt_scheme": SETTINGS.rabbit_mgmt_scheme,
                          "rabbit_mgmt_port": SETTINGS.rabbit_mgmt_port,
                          "rabbit_mgmt_ca": bool(SETTINGS.rabbit_mgmt_ca_file),
                          "mongo_ca": bool(SETTINGS.mongo_ca_file)},
        "compose_project": SETTINGS.project,
        "ws_join_format": os.environ.get("MED_WS_JOIN_FORMAT", "legacy"),
        "preflight": pre,
    }


def instrument_hashes() -> dict:
    """Version of the measuring instrument: code, criteria, frozen cases and probe image.
    `compare` refuses to classify when BF and MF were taken with different versions."""
    files = [Path(__file__), CRITERIA_FILE, CASES_FILE, EVAL_DIR / "probe.Dockerfile",
             EVAL_DIR / "requirements.txt"] + sorted((EVAL_DIR / "medlib").glob("*.py"))
    out = {str(f.relative_to(EVAL_DIR)): sha256_file(f) for f in files if f.exists()}
    total = hashlib.sha256("".join(f"{k}:{v};" for k, v in sorted(out.items())).encode()).hexdigest()
    return {"ficheiros": out, "total": total}


def freeze(out_dir: Path, reason: str) -> dict:
    """Record the current instrument version as the one the BF must be compared with.

    Only for a BF whose raw data stays valid under the new version (changes limited to
    summaries/evaluation, or steps re-measured with --resume). Logged in the manifest."""
    path = out_dir / "manifest.json"
    man = json.loads(path.read_text())
    if man.get("campaign") != "BF":
        raise SystemExit("freeze só se aplica a uma campanha BF")
    inst = instrument_hashes()
    man.setdefault("instrumento_historico", []).append(
        {"em": utc_now(), "motivo": reason, "total": inst["total"],
         "anterior": (man.get("instrumento_final") or man.get("instrumento") or {}).get("total")})
    man["instrumento_final"] = inst
    path.write_text(json.dumps(man, indent=1, ensure_ascii=False))
    return inst


def _dir_hash(d: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(d.glob("*.py")):
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def _wanted(metrics: str | None, suite: str) -> list[str]:
    order = []
    if suite in ("security", "all"):
        order += SECURITY_ORDER
    if suite in ("upload", "all"):
        order += UPLOAD_ORDER
    if not metrics:
        return order
    req = {m.strip().upper() for m in metrics.split(",") if m.strip()}
    out = []
    for step in SECURITY_ORDER + UPLOAD_ORDER:
        if step == "STRATA" and req & UPLOAD_STRATA:
            out.append(step)
        elif step in req:
            out.append(step)
    return out


def configure_ws_protocol(security) -> None:
    """D-03/B8: opt-in protocol adapter; the frozen legacy client stays unchanged.

    Keep this adapter here: medlib, cases and criteria remain frozen. Shared
    contexts come only from the fixture's successful share resolution, never
    from discovering a link for an attacker or from labels such as 'reader'.
    """
    mode = os.environ.get("MED_WS_JOIN_FORMAT", "legacy")
    if mode == "legacy":
        return
    if mode != "v2":
        raise SystemExit("MED_WS_JOIN_FORMAT must be legacy or v2")
    from medlib.api import API
    from medlib.ws import WS

    contexts = {}
    clients = weakref.WeakSet()
    share_resolve = API.share_resolve
    create_project = API.create_project

    class ProtocolWS(WS):
        def connect(self, token):
            self._protocol_token = token
            clients.add(self)
            return super().connect(token)

        def join(self, project_id):
            if self.sio.connected:
                access = contexts.get((self._protocol_token, project_id), {"kind": "owner"})
                try:
                    self.sio.call("join-project", {"projectId": project_id, "access": access}, timeout=2)
                except Exception:  # refusal/timeout never stands in for authorization
                    pass

    def resolve(self, acct, share_id):
        response = share_resolve(self, acct, share_id)
        if response.ok and isinstance(response.json, dict) and response.json.get("_id"):
            contexts[(acct.jwt, str(response.json["_id"]))] = {"kind": "share", "shareId": share_id}
        return response

    def create(self, owner, *args, **kwargs):
        project = create_project(self, owner, *args, **kwargs)
        # D-29: S05 connects before creating its project. Present that owner
        # context explicitly before operations produce protected personal events.
        for client in list(clients):
            if client.connected and client._protocol_token == owner.jwt:
                client.join(project.id)
        return project

    API.share_resolve = resolve
    API.create_project = create
    security.WS = ProtocolWS


def run(args: argparse.Namespace) -> int:
    from medlib import security
    from medlib.api import API
    from medlib.uploads import Uploader

    configure_ws_protocol(security)

    pre = preflight(args.campaign)
    if not pre["ok"] and not args.force:
        log(f"preflight falhou: {pre['failed']} (use --force apenas em campanhas EXP)")
        return 2
    if args.force and args.campaign in ("BF", "MF"):
        log("--force não é permitido em BF/MF")
        return 2
    if not dockerctl.MARKER_FILE.exists():
        log("a stack isolada não está ativa: corra `med.py stack up` primeiro")
        return 2
    if not dockerctl.probe_running():
        dockerctl.start_probe()

    out_dir = Path(args.resume) if args.resume else RESULTS_DIR / f"{args.campaign}-{utc_stamp()}"
    res = Results(out_dir)
    if not (out_dir / "manifest.json").exists():
        res.write_json("manifest.json", manifest(args.campaign, pre))
    log(f"resultados em {out_dir}")

    api = API()
    api.wait_ready(300)
    reps = 1 if args.quick else args.reps
    steps = _wanted(args.metrics, args.suite)
    video10 = corpus.path("pad_10MiB_H.mp4")
    uploader = None
    t0 = time.time()
    for step in steps:
        log(f"=== {step} ===")
        try:
            if step == "S18":
                security.run_s18(res, args.campaign)
            elif step == "S01":
                security.run_s01(api, res, args.campaign, reps)
            elif step == "S02":
                security.run_s02(api, res, args.campaign, reps)
            elif step == "S03":
                security.run_s03(api, res, args.campaign, reps)
            elif step == "S04":
                security.run_s04(api, res, args.campaign, reps)
            elif step == "S16":
                security.run_s16(api, res, args.campaign, reps)
            elif step == "S17":
                security.run_s17(api, res, args.campaign, reps)
            elif step == "S12":
                security.run_s12(api, res, args.campaign, reps, window_s=10.0 if args.quick else 30.0)
            elif step == "S05":
                security.run_s05(api, res, args.campaign, reps, video10)
            elif step == "S21":
                security.run_s21(api, res, args.campaign, n=20 if args.quick else 100)
            else:
                if uploader is None:
                    log("a reiniciar os serviços Node antes da suite de upload")
                    dockerctl.restart_app()
                    uploader = Uploader(api, res, args.campaign)
                    uploader.wait_api()
                    uploader.accounts.clear()  # fresh accounts for the measured runs
                else:
                    uploader.ensure_healthy()  # a previous step may have killed the gateway
                if step == "STRATA":
                    uploader.strata(quick=args.quick)
                elif step == "U04":
                    uploader.seaweed_cold(quick=args.quick)
                elif step == "U18":
                    uploader.invalid(reps=1 if args.quick else 3)
                elif step == "U19":
                    uploader.no_token(reps=1 if args.quick else 5, bad_sig_reps=1 if args.quick else 3)
                elif step == "U20":
                    uploader.concurrent(rounds=1 if args.quick else 3)
                elif step == "U25":
                    uploader.coexistence(pairs=1 if args.quick else 3)
        except Exception as exc:  # noqa: BLE001 - a failing metric must not stop the campaign
            log(f"{step} falhou: {exc!r}")
            res.raw("errors", {"step": step, "error": repr(exc), "trace": traceback.format_exc()[-3000:],
                               "t_utc": utc_now()})
            names = sorted(UPLOAD_STRATA) if step == "STRATA" else [step]
            for n in names:
                if n not in res.summaries:
                    res.summary(n, {"erro": repr(exc)[:300]})
    _check_matrix(res)
    man = json.loads((out_dir / "manifest.json").read_text())
    man["finished_at"] = utc_now()
    man["duration_s"] = round(time.time() - t0)
    res.write_json("manifest.json", man)
    path = report.write_report(out_dir)
    log(f"relatório: {path}")
    print(path.read_text())
    return 0


def _check_matrix(res: Results) -> None:
    """Every frozen case in cases/security.yaml must have been attempted, and vice versa."""
    import yaml
    frozen = yaml.safe_load(CASES_FILE.read_text())
    report_ = {}
    for metric, cases in frozen.items():
        raw = res.path / "raw" / f"{metric}.jsonl"
        if not raw.exists():
            continue
        seen = set()
        for line in raw.read_text().splitlines():
            rec = json.loads(line)
            if "case" in rec:
                seen.add(rec["case"])
        expected = {c["id"] for c in cases}
        report_[metric] = {"em_falta": sorted(expected - seen), "nao_congelados": sorted(seen - expected)}
    res.write_json("matrix_check.json", report_)
    for m, r in report_.items():
        if r["em_falta"] or r["nao_congelados"]:
            log(f"matriz {m}: em falta {r['em_falta']} / não congelados {r['nao_congelados']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def resummarise(out_dir: Path) -> None:
    """Rebuild the stratum summaries from raw/U_strata.jsonl and U08_residuals.jsonl."""
    from medlib.uploads import summarise_strata
    from medlib.util import Results
    raw = out_dir / "raw"
    records = [json.loads(l) for l in (raw / "U_strata.jsonl").read_text().splitlines() if l.strip()]
    resid_file = raw / "U08_residuals.jsonl"
    resid = {}
    if resid_file.exists():
        for l in resid_file.read_text().splitlines():
            if l.strip():
                d = json.loads(l)
                resid[d["stratum"]] = d["residual"]
    for r in records:
        r.setdefault("residual", resid.get(r.get("stratum"), {}))
    summarise_strata(Results(out_dir), records)
    log(f"resumos dos estratos recalculados a partir de {len(records)} registos")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preflight")
    p.add_argument("--campaign", default="EXP", choices=["BF", "MF", "EXP"])
    p = sub.add_parser("stack")
    p.add_argument("action", choices=["up", "down", "status", "purge"])
    p.add_argument("--corpus", action="store_true", help="purge: também apaga o corpus")
    p.add_argument("--no-build", action="store_true")
    sub.add_parser("corpus")
    p = sub.add_parser("run")
    p.add_argument("--campaign", required=True, choices=["BF", "MF", "EXP"])
    p.add_argument("--suite", default="all", choices=["security", "upload", "all"])
    p.add_argument("--metrics")
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--quick", action="store_true", help="ensaio de aceitação: 1 repetição, só 10 MiB")
    p.add_argument("--resume", help="diretório de resultados existente a completar")
    p.add_argument("--force", action="store_true", help="ignorar o preflight (só EXP)")
    p = sub.add_parser("report")
    p.add_argument("dir")
    p.add_argument("--resummarise", action="store_true",
                   help="recalcular os resumos dos estratos de upload a partir de raw/ (sem medir)")
    p = sub.add_parser("freeze", help="registar a versão atual do instrumento numa BF")
    p.add_argument("dir")
    p.add_argument("--motivo", required=True)
    p = sub.add_parser("compare")
    p.add_argument("bf")
    p.add_argument("mf")
    args = ap.parse_args()

    if args.cmd == "preflight":
        r = preflight(args.campaign)
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return 0 if r["ok"] else 1
    if args.cmd == "stack":
        if args.action == "up":
            dockerctl.stack_up(build=not args.no_build)
            from medlib.api import API
            API().wait_ready(1800)
            log("stack pronta")
        elif args.action == "down":
            dockerctl.stack_down()
        elif args.action == "status":
            print(dockerctl.compose("ps", check=False).stdout)
            print("probe:", "running" if dockerctl.probe_running() else "stopped")
        elif args.action == "purge":
            before = shutil.disk_usage(REPO).free / 2**30
            removed = dockerctl.stack_purge()
            if args.corpus:
                mf_done = any(d.name.startswith("MF-") for d in RESULTS_DIR.glob("MF-*"))
                if not mf_done:
                    log("o corpus só pode ser apagado depois de existir uma campanha MF")
                elif input("Apagar evaluation/.corpus? [s/N] ").strip().lower() == "s":
                    shutil.rmtree(CORPUS_DIR, ignore_errors=True)
            after = shutil.disk_usage(REPO).free / 2**30
            log(f"imagens removidas: {removed}")
            log(f"espaço livre: {before:.1f} -> {after:.1f} GiB")
        return 0
    if args.cmd == "corpus":
        files = corpus.build()
        log(f"corpus: {len(files)} ficheiros em {CORPUS_DIR}")
        return 0
    if args.cmd == "run":
        return run(args)
    if args.cmd == "report":
        if args.resummarise:
            resummarise(Path(args.dir))
        print(report.write_report(Path(args.dir)).read_text())
        return 0
    if args.cmd == "freeze":
        inst = freeze(Path(args.dir), args.motivo)
        log(f"instrumento congelado na BF: {inst['total'][:12]}")
        return 0
    if args.cmd == "compare":
        print(report.compare(Path(args.bf), Path(args.mf)))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
