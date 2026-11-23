"""Docker / Compose control, restricted to the isolated evaluation project."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import re

from .config import ALLOWED_PROJECT_RE, FORBIDDEN_PROJECTS, REPO, RUN_DIR, SETTINGS, EVAL_DIR
from .util import log

COMPOSE_FILE = REPO / "docker-compose.yaml"
OVERRIDE_FILE = RUN_DIR / "override.yaml"
MARKER_FILE = RUN_DIR / "stack.json"

# Same limits as the November 16 measurements; identical in BF and MF.
LIMITED_SERVICES = ("api_gateway", "projects", "img_storage", "video_tool")


def guard_project() -> str:
    p = SETTINGS.project
    if p in FORBIDDEN_PROJECTS or not re.match(ALLOWED_PROJECT_RE, p):
        raise SystemExit(f"Refusing to operate on compose project '{p}': only picturas-nfr or "
                         "picturas-nfr-<suffix> are allowed.")
    return p


def _marker() -> dict:
    try:
        return json.loads(MARKER_FILE.read_text())
    except (OSError, ValueError):
        return {}


def guard_owned() -> None:
    """Before any removal (down -v, purge): the project must have been created by this
    tool (marker for this same project name). Volumes of any other installation are
    never touched, whatever its name."""
    p = guard_project()
    vols = project_volumes()
    if not vols:
        return
    if _marker().get("project") != p:
        raise SystemExit(f"Project '{p}' has volumes ({', '.join(vols)}) that this tool did not create "
                         f"(no marker for '{p}' in {MARKER_FILE}). Nothing was removed.")


def run(cmd: list[str], *, check: bool = True, timeout: float | None = None,
        input_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True,
                          timeout=timeout, input=input_text)


def compose(*args: str, override: bool = True, check: bool = True,
            timeout: float | None = None) -> subprocess.CompletedProcess:
    cmd = ["docker", "compose", "-p", guard_project(), "-f", str(COMPOSE_FILE)]
    if override and OVERRIDE_FILE.exists():
        cmd += ["-f", str(OVERRIDE_FILE)]
    return run(cmd + list(args), check=check, timeout=timeout)


def cname(service: str) -> str:
    return f"{guard_project()}-{service}-1"


def exec_sh(service: str, script: str, timeout: float = 30, check: bool = True) -> str:
    r = run(["docker", "exec", cname(service), "sh", "-c", script], check=check, timeout=timeout)
    return r.stdout


def popen_sh(service: str, script: str, user: str | None = None) -> subprocess.Popen:
    cmd = ["docker", "exec"] + (["-u", user] if user else []) + [cname(service), "sh", "-c", script]
    return subprocess.Popen(cmd,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)


def inspect(service: str) -> dict:
    r = run(["docker", "inspect", cname(service)], check=False)
    if r.returncode != 0:
        return {}
    return json.loads(r.stdout)[0]


def state(service: str) -> dict:
    """Snapshot used to detect OOM kills and restarts across an operation."""
    info = inspect(service)
    st = info.get("State", {})
    oom_kill = None
    try:
        out = exec_sh(service, "cat /sys/fs/cgroup/memory.events 2>/dev/null || true", timeout=10, check=False)
        for line in out.splitlines():
            k, _, v = line.partition(" ")
            if k == "oom_kill":
                oom_kill = int(v)
    except Exception:
        pass
    return {
        "running": st.get("Running"),
        "started_at": st.get("StartedAt"),
        "restart_count": info.get("RestartCount"),
        "oom_killed": st.get("OOMKilled"),
        "oom_kill_events": oom_kill,
    }


def state_change(before: dict, after: dict) -> dict:
    restarted = (before.get("started_at") != after.get("started_at")
                 or (after.get("restart_count") or 0) > (before.get("restart_count") or 0)
                 or not after.get("running"))
    oom = bool(after.get("oom_killed")) and (not before.get("oom_killed") or restarted)
    b, a = before.get("oom_kill_events"), after.get("oom_kill_events")
    if a is not None and b is not None and a > b:
        oom = True
    return {"restarted": bool(restarted), "oom": bool(oom)}


def network_name() -> str:
    info = inspect("projects")
    nets = list(info.get("NetworkSettings", {}).get("Networks", {}).keys())
    if not nets:
        raise SystemExit("Could not determine the application network (is the stack up?).")
    for n in nets:
        if n.endswith("_elk"):
            return n
    return nets[0]


def published_port(service: str, target: int) -> int | None:
    """Host port of an isolated-stack service, or None if not published."""
    r = compose("port", service, str(target), check=False)
    out = r.stdout.strip()
    if r.returncode != 0 or not out:
        return None
    try:
        port = int(out.splitlines()[0].rsplit(":", 1)[1])
    except (ValueError, IndexError):
        return None
    return port or None  # compose prints ":0" for an unpublished port


def delivered_config() -> dict:
    """Configuration of the delivered docker-compose.yaml, without the override."""
    r = run(["docker", "compose", "-p", guard_project(), "-f", str(COMPOSE_FILE),
             "config", "--format", "json"])
    return json.loads(r.stdout)


# ---------------------------------------------------------------------------
# Override generation
# ---------------------------------------------------------------------------

def write_override() -> Path:
    cfg = delivered_config()
    lines = ["# Generated by evaluation/med.py - do not edit, do not commit.", "services:"]
    for name, svc in sorted(cfg.get("services", {}).items()):
        block: list[str] = []
        ports = svc.get("ports") or []
        if ports:
            block.append("    ports: !override")
            for p in ports:
                published = p.get("published")
                if published in (None, ""):
                    continue
                host_ip = p.get("host_ip") or ""
                proto = p.get("protocol") or "tcp"
                host_port = int(str(published).split("-")[0]) + SETTINGS.port_offset
                prefix = f"{host_ip}:" if host_ip else ""
                block.append(f'      - "{prefix}{host_port}:{p["target"]}/{proto}"')
        if name in LIMITED_SERVICES:
            block.append("    cpus: 2")
            block.append("    mem_limit: 2g")
        if name == "img_storage":
            # Public signed URLs must point to the isolated entry, not port 8080.
            block.append("    environment:")
            block.append(f'      FRONTEND_URL: "{SETTINGS.base_url}"')
        if block:
            lines.append(f"  {name}:")
            lines.extend(block)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    OVERRIDE_FILE.write_text("\n".join(lines) + "\n")
    return OVERRIDE_FILE


# ---------------------------------------------------------------------------
# Stack lifecycle
# ---------------------------------------------------------------------------

def project_volumes() -> list[str]:
    r = run(["docker", "volume", "ls", "-q", "--filter",
             f"label=com.docker.compose.project={guard_project()}"], check=False)
    return [v for v in r.stdout.split() if v]


def stack_up(services: list[str] | None = None, build: bool = True) -> None:
    guard_project()
    guard_owned()
    log("stack: down -v (isolated project only)")
    compose("down", "-v", "--remove-orphans", override=False, check=False, timeout=600)
    write_override()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    MARKER_FILE.write_text(json.dumps({"project": SETTINGS.project, "created_at": time.time()}))
    log("stack: up -d --build (first build can take 15-30 min)")
    args = ["up", "-d"] + (["--build"] if build else []) + (services or [])
    r = compose(*args, check=False, timeout=3600)
    if r.returncode != 0:
        raise SystemExit("docker compose up failed:\n" + r.stderr[-4000:])
    build_probe()
    start_probe()


def stack_down() -> None:
    guard_owned()
    stop_probe()
    compose("down", "-v", "--remove-orphans", check=False, timeout=600)
    if MARKER_FILE.exists():
        MARKER_FILE.unlink()


def stack_purge() -> list[str]:
    """Remove only images built by this project and the probe image."""
    stack_down()
    removed = []
    r = run(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"], check=False)
    prefix = f"{guard_project()}-"
    for ref in r.stdout.split():
        repo = ref.split(":")[0]
        if repo.startswith(prefix) or repo == SETTINGS.probe_image:
            rr = run(["docker", "image", "rm", ref], check=False)
            if rr.returncode == 0:
                removed.append(ref)
    for net in run(["docker", "network", "ls", "-q", "--filter",
                    f"label=com.docker.compose.project={guard_project()}"], check=False).stdout.split():
        run(["docker", "network", "rm", net], check=False)
    return removed


def restart(services: list[str]) -> None:
    compose("restart", *services, timeout=300)


def restart_app() -> None:
    """Restart the three Node services and then nginx.

    - The Node services run under nodemon: after an OOM kill the container stays
      "Up" while the app is dead ("app crashed - waiting for file changes"), so a
      running container does not mean a live service.
    - nginx resolves upstream names at start-up; after the Node containers restart
      their IPs may change and nginx answers 502 until it is restarted too."""
    restart(["api_gateway", "projects", "img_storage"])
    restart(["nginx"])


def stop(service: str) -> None:
    compose("stop", service, timeout=120)


def start(service: str) -> None:
    compose("start", service, timeout=120)


def image_ids() -> dict:
    r = compose("images", "--format", "json", check=False)
    try:
        data = json.loads(r.stdout or "[]")
    except json.JSONDecodeError:
        data = [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
    return {d.get("ContainerName", d.get("Service", "?")): d.get("ID") for d in data}


# ---------------------------------------------------------------------------
# Probe container (runs inside the application network)
# ---------------------------------------------------------------------------

def build_probe() -> None:
    log("probe: building image")
    r = run(["docker", "build", "-t", SETTINGS.probe_image, "-f",
             str(EVAL_DIR / "probe.Dockerfile"), str(EVAL_DIR)], check=False, timeout=1800)
    if r.returncode != 0:
        raise SystemExit("probe image build failed:\n" + r.stderr[-3000:])


def start_probe() -> None:
    stop_probe()
    cmd = ["docker", "run", "-d", "--name", SETTINGS.probe_container,
           "--network", network_name(), "--label", f"med.project={SETTINGS.project}"]
    cert_dir = SETTINGS.client_cert_dir()
    if cert_dir:
        cmd += ["-v", f"{cert_dir}:/certs:ro"]
    for channel in ("s3", "amqp", "rabbit_mgmt", "mongo"):
        ca = getattr(SETTINGS, f"{channel}_ca_file")
        if ca:
            if not Path(ca).is_file():
                raise SystemExit(f"Missing MED data-channel CA file for {channel}")
            cmd += ["-v", f"{Path(ca).resolve()}:/med-certs/{channel}.crt:ro"]
    cmd += [SETTINGS.probe_image, "sleep", "infinity"]
    run(cmd)


def stop_probe() -> None:
    run(["docker", "rm", "-f", SETTINGS.probe_container], check=False)


def probe_running() -> bool:
    r = run(["docker", "inspect", "-f", "{{.State.Running}}", SETTINGS.probe_container], check=False)
    return r.stdout.strip() == "true"


def probe(spec: dict, timeout: float = 120) -> dict:
    """Run one action inside the application network; returns its JSON result."""
    if not probe_running():
        start_probe()
    r = run(["docker", "exec", "-i", SETTINGS.probe_container, "python", "-m", "medlib.probe"],
            check=False, timeout=timeout, input_text=json.dumps(spec))
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"ok": False, "error_kind": "probe_failure", "error": r.stderr[-500:]}
