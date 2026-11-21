"""Resource instruments: Node process peak (VmHWM), cgroup memory and temp-disk samplers."""
from __future__ import annotations

import statistics
import threading
import time
import uuid

from . import dockerctl
from .util import log

KIB = 1024

NODE_SERVICES = ("api_gateway", "projects", "img_storage")

_PID_SH = r"""best=0;bp=0
for d in /proc/[0-9]*; do
  n=$(cat $d/comm 2>/dev/null)
  case "$n" in node*|MainThread)
    r=$(awk '/VmRSS/{print $2}' $d/status 2>/dev/null)
    if [ "${r:-0}" -gt "$best" ]; then best=$r; bp=${d#/proc/}; fi;;
  esac
done
echo $bp"""


class NodeMem:
    """Peak RSS of a service's main Node process around one operation (U01, U19)."""

    def __init__(self, service: str):
        self.service = service
        self.pid: str | None = None
        self.rss_pre_kib: int | None = None
        self.reset_ok = False
        self.before: dict = {}

    def reset(self) -> None:
        self.before = dockerctl.state(self.service)
        try:
            self.pid = dockerctl.exec_sh(self.service, _PID_SH, timeout=15).strip() or None
            if not self.pid or self.pid == "0":
                self.pid = None
                return
            out = dockerctl.exec_sh(
                self.service,
                f"(echo 5 > /proc/{self.pid}/clear_refs && echo OK || echo FAIL); "
                f"awk '/VmRSS/{{print $2}}' /proc/{self.pid}/status", timeout=15).split()
            self.reset_ok = out[0] == "OK"
            self.rss_pre_kib = int(out[1])
        except Exception as exc:  # noqa: BLE001
            log(f"NodeMem.reset {self.service}: {exc!r}")

    def read(self) -> dict:
        after = dockerctl.state(self.service)
        change = dockerctl.state_change(self.before, after)
        rec = {"pid_found": self.pid is not None, "hwm_reset": self.reset_ok,
               "rss_pre_mib": None if self.rss_pre_kib is None else round(self.rss_pre_kib / KIB, 1),
               "restarted": change["restarted"], "oom": change["oom"]}
        if self.pid and not change["restarted"]:
            try:
                out = dockerctl.exec_sh(
                    self.service,
                    f"awk '/VmHWM/{{h=$2}}/VmRSS/{{r=$2}}END{{print h, r}}' /proc/{self.pid}/status",
                    timeout=15).split()
                hwm, rss = int(out[0]), int(out[1])
                rec.update({"peak_mib": round(hwm / KIB, 1), "rss_post_mib": round(rss / KIB, 1),
                            "delta_mib": round((hwm - (self.rss_pre_kib or 0)) / KIB, 1),
                            "process_died": False})
            except Exception:  # noqa: BLE001
                rec["process_died"] = True
        else:
            rec["process_died"] = True
        return rec


def node_reset_all(services=NODE_SERVICES) -> dict[str, NodeMem]:
    mems = {s: NodeMem(s) for s in services}
    for m in mems.values():
        m.reset()
    return mems


def node_read_all(mems: dict[str, NodeMem]) -> dict:
    return {s: m.read() for s, m in mems.items()}


class Sampler:
    """Background in-container loop; stops via a flag file or a hard deadline."""

    def __init__(self, service: str, body: str, interval: float, max_s: int = 900, user: str | None = None):
        self.service = service
        self.user = user
        self.id = uuid.uuid4().hex[:8]
        self.lines: list[str] = []
        flag = f"/tmp/med_stop_{self.id}"
        self.flag = flag
        self.script = (
            f'S={flag}; rm -f $S; end=$(( $(cut -d. -f1 /proc/uptime) + {max_s} )); '
            f'while [ ! -f $S ] && [ $(cut -d. -f1 /proc/uptime) -lt $end ]; do '
            f'printf "%s " "$(cut -d" " -f1 /proc/uptime)"; {body}; sleep {interval}; done; rm -f $S')
        self.proc = None
        self.thread = None

    def start(self) -> "Sampler":
        try:
            self.proc = dockerctl.popen_sh(self.service, self.script, user=self.user)
        except Exception as exc:  # noqa: BLE001
            log(f"sampler {self.service}: {exc!r}")
            return self

        def reader():
            for line in self.proc.stdout:  # type: ignore[union-attr]
                self.lines.append(line.strip())
        self.thread = threading.Thread(target=reader, daemon=True)
        self.thread.start()
        return self

    def stop(self) -> list[list[float]]:
        if self.proc is None:
            return []
        try:
            dockerctl.exec_sh(self.service, f"touch {self.flag}", timeout=10, check=False)
        except Exception:  # noqa: BLE001
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001
            self.proc.kill()
        if self.thread:
            self.thread.join(timeout=5)
        rows = []
        for line in self.lines:
            try:
                rows.append([float(x) for x in line.split()])
            except ValueError:
                continue
        return rows


CGROUP_BODY = (
    'if [ -f /sys/fs/cgroup/memory.stat ]; then '
    'awk \'$1=="anon"{a=$2} END{printf "%d ", a+0}\' /sys/fs/cgroup/memory.stat; '
    'cat /sys/fs/cgroup/memory.current; '
    'else awk \'$1=="total_rss"{a=$2} END{printf "%d ", a+0}\' /sys/fs/cgroup/memory/memory.stat; '
    'cat /sys/fs/cgroup/memory/memory.usage_in_bytes; fi')


def cgroup_sampler(service: str) -> Sampler:
    return Sampler(service, CGROUP_BODY, 0.05)


def cgroup_summary(rows: list[list[float]], idle_s: float = 2.0) -> dict:
    """rows: [uptime, anon_bytes, current_bytes]. idle = median of first idle_s seconds."""
    rows = [r for r in rows if len(r) >= 3]
    if not rows:
        return {"samples": 0}
    t0 = rows[0][0]
    idle = [r[1] for r in rows if r[0] - t0 <= idle_s] or [rows[0][1]]
    idle_anon = statistics.median(idle)
    peak = max(r[1] for r in rows)
    return {"samples": len(rows), "idle_anon_mib": round(idle_anon / 2**20, 1),
            "peak_anon_mib": round(peak / 2**20, 1),
            "delta_anon_mib": round((peak - idle_anon) / 2**20, 1),
            "peak_current_mib": round(max(r[2] for r in rows) / 2**20, 1)}


# ---------------------------------------------------------------------------
# Temporary disk (U08)
# ---------------------------------------------------------------------------

_NGINX_TEMP: str | None = None


def nginx_temp_dir() -> str:
    global _NGINX_TEMP
    if _NGINX_TEMP is None:
        out = dockerctl.exec_sh("nginx", "nginx -V 2>&1", check=False)
        path = "/var/cache/nginx/client_temp"
        for tok in out.split():
            if tok.startswith("--http-client-body-temp-path="):
                path = tok.split("=", 1)[1]
        _NGINX_TEMP = path
    return _NGINX_TEMP


def temp_dirs() -> dict[str, str]:
    return {"nginx": nginx_temp_dir(), "api_gateway": "/tmp", "projects": "/tmp", "img_storage": "/tmp"}


def disk_sampler(service: str, directory: str) -> Sampler:
    """Visible files (du) plus files deleted but still open under `directory`.

    nginx unlinks its client-body temp file right after creating it, so du alone
    never sees it; the open descriptor in /proc/*/fd still holds the disk space."""
    body = (
        f'd=$(du -sk {directory} 2>/dev/null | cut -f1); t=0; '
        f'for f in /proc/[0-9]*/fd/*; do l=$(readlink "$f" 2>/dev/null); '
        f'case "$l" in "{directory}/"*" (deleted)") s=$(stat -L -c %s "$f" 2>/dev/null); '
        f't=$((t + ${{s:-0}}));; esac; done; echo "${{d:-0}} $((t / 1024))"')
    # nginx workers run as user nginx; root in the container cannot read their fds.
    return Sampler(service, body, 0.1, user="nginx" if service == "nginx" else None)


def disk_peak_kib(rows: list[list[float]]) -> dict:
    """rows: [uptime, du_kib, deleted_open_kib]."""
    rows = [r for r in rows if len(r) >= 3]
    if not rows:
        return {"samples": 0}
    totals = [r[1] + r[2] for r in rows]
    base = totals[0]
    peak = max(totals)
    return {"samples": len(rows), "start_kib": base, "peak_kib": peak, "delta_peak_kib": peak - base,
            "peak_deleted_open_kib": max(r[2] for r in rows)}


def disk_snapshot(service: str, directory: str) -> dict:
    out = dockerctl.exec_sh(
        service, f"du -sk {directory} 2>/dev/null | awk '{{print $1}}'; "
                 f"find {directory} -type f 2>/dev/null | wc -l", check=False).split()
    try:
        return {"kib": int(out[0]), "files": int(out[1])}
    except (IndexError, ValueError):
        return {"kib": None, "files": None}


def disk_snapshot_all() -> dict:
    return {svc: disk_snapshot(svc, d) for svc, d in temp_dirs().items()}


class Window:
    """Starts cgroup + disk samplers for one measured operation."""

    def __init__(self, cgroup_services=("nginx", "seaweedfs"), disk: bool = True):
        self.cg = {s: cgroup_sampler(s) for s in cgroup_services}
        self.dk = {s: disk_sampler(s, d) for s, d in temp_dirs().items()} if disk else {}

    def start(self, idle_s: float = 2.2) -> "Window":
        for s in list(self.cg.values()) + list(self.dk.values()):
            s.start()
        time.sleep(idle_s)
        return self

    def stop(self) -> dict:
        out = {"cgroup": {k: cgroup_summary(v.stop()) for k, v in self.cg.items()},
               "disk": {k: disk_peak_kib(v.stop()) for k, v in self.dk.items()}}
        return out
