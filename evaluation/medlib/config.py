"""Configuration: paths, environment (.env.med) and service addresses.

Every value that differs between the baseline (BF) and the final measurement (MF)
comes from the environment, so the same code runs both campaigns.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent.parent
REPO = EVAL_DIR.parent
RUN_DIR = EVAL_DIR / ".run"
CORPUS_DIR = EVAL_DIR / ".corpus"
RESULTS_DIR = EVAL_DIR / "results"
CRITERIA_FILE = EVAL_DIR / "criteria.yaml"
CASES_FILE = EVAL_DIR / "cases" / "security.yaml"
SAMPLES = REPO / "samples" / "video"

# Application paths whose diff against the base commit must be empty in the BF.
APP_PATHS = [
    "apiGateway", "projects", "users", "subscriptions", "wsGateway",
    "imageStorageService", "Tools", "frontend", "nginx", "rabbitMQ",
    "generative-mock", "docker-compose.yaml",
]

FORBIDDEN_PROJECTS = {"picturas", ""}


def _load_env_file(path: Path) -> None:
    """Minimal KEY=VALUE parser; existing environment variables win."""
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env_file(EVAL_DIR / ".env.med")


def env(name: str, default: str = "") -> str:
    """Empty values count as unset, so .env.med can list every key."""
    return os.environ.get(name) or default


@dataclass
class Service:
    name: str          # compose service name
    host: str          # DNS name inside the Docker network
    port: int          # container port
    scheme: str        # http / https


@dataclass
class Settings:
    project: str = field(default_factory=lambda: env("MED_COMPOSE_PROJECT", "picturas-nfr"))
    base_url: str = field(default_factory=lambda: env("MED_BASE_URL", "https://localhost:28080").rstrip("/"))
    cacert: str = field(default_factory=lambda: env("MED_CACERT", ""))
    port_offset: int = field(default_factory=lambda: int(env("MED_PORT_OFFSET", "20000")))
    base_commit: str = field(default_factory=lambda: env("MED_BASE_COMMIT", "0523102"))
    s3_bucket: str = field(default_factory=lambda: env("MED_S3_BUCKET", "picturas"))
    min_free_gib: int = field(default_factory=lambda: int(env("MED_MIN_FREE_GIB", "60")))
    probe_image: str = "picturas-med-probe"

    @property
    def gw(self) -> str:
        return self.base_url + "/api-gateway/"

    @property
    def probe_container(self) -> str:
        return f"{self.project}-medprobe"

    def verify(self):
        """TLS verification for the public entry (nginx uses a self-signed cert)."""
        return self.cacert if self.cacert else False

    def service(self, name: str) -> Service:
        defaults = {
            "projects": ("projects", 9001, "https"),
            "users": ("users", 10001, "https"),
            "subscriptions": ("subscriptions", 11001, "https"),
            "img_storage": ("img_storage", 11000, "http"),
        }
        host, port, scheme = defaults[name]
        scheme = env(f"MED_SVC_SCHEME_{name.upper()}", scheme)
        return Service(name, host, port, scheme)

    # ---- credentials -------------------------------------------------------
    def admin_mongo_uri(self, which: str) -> str:
        """Admin URI used only for fixtures and cleanup (never by attack cases)."""
        defaults = {
            "projects": "mongodb://projects_mongoDB:27018/",
            "users": "mongodb://users_mongoDB:27019/",
            "subscriptions": "mongodb://subscriptions_mongoDB:27017/",
        }
        return env(f"MED_ADMIN_MONGO_URI_{which.upper()}", defaults[which])

    def rabbit_admin(self) -> tuple[str, str]:
        return _pair(env("MED_RABBIT_ADMIN", "user:password"))

    def s3_admin(self) -> tuple[str, str]:
        return _pair(env("MED_S3_ADMIN", "admin:admin123"))

    def svc_cred(self, kind: str, service: str) -> tuple[str, str] | None:
        """Legitimate per-service credential (MF). None when not configured."""
        value = env(f"MED_SVC_CRED_{kind.upper()}_{service.upper()}")
        return _pair(value) if value else None

    def client_cert_dir(self) -> str:
        return env("MED_CLIENT_CERT_DIR", "")


def _pair(value: str) -> tuple[str, str]:
    user, _, password = value.partition(":")
    return user, password


SETTINGS = Settings()

# Values copied verbatim from the delivered docker-compose.yaml of the base. They are
# used by the attack families "credential committed to Git" (S16b/S17) and must not
# be replaced by MF credentials.
GIT_DEFAULT_RABBIT = ("user", "password")
GIT_DEFAULT_S3 = ("admin", "admin123")

MIB = 1024 * 1024
