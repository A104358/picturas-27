"""B5 conformance: mTLS on every internal API hop (D4, option A, PKI-C5 A; S08, S09).

Runs on the stack network (tests/conformance/in-network.sh <project> mtls-pki/b5-mtls.py).
For every internal HTTPS server it checks:
  - S08: no client certificate, a certificate from another CA, an expired certificate signed
    by the installation CA and a server-only certificate (EKU) are refused in TLS; plaintext
    gets no HTTP answer;
  - D4 matrix: each service certificate of the installation is accepted only by the servers
    whose allowlist names it (others answer 403: "a valid CA is not enough");
  - S09: the allowed peer gets a domain answer (below 500, not a peer refusal);
  - no TLS session resumption (a resumed session would carry an identity across connections);
  - static: no disabled verification in the product code, every Node agent without cached
    sessions, nginx upstreams over verified TLS without session reuse.
The harness is trusted: it reads the CA key only to sign the expired test certificate, in
memory and a private temporary directory. Nothing secret is printed.
"""
import datetime
import os
import re
import socket
import ssl
import sys
import tempfile
import uuid
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from b4_common import CA, ROOT, Results  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
PKI = ROOT / "pki"
res = Results("B5 mTLS")
OID = "0" * 24

# server: port, {allowed peer: (method, path)}; a refused peer is sent the first request.
SERVERS = {
    "frontend": (3000, {"nginx": ("GET", "/")}),
    "api_gateway": (8000, {"nginx": ("GET", "/users/x")}),
    "ws_gateway": (4000, {"nginx": ("GET", "/socket.io/?EIO=4&transport=polling")}),
    "projects": (9001, {"api_gateway": ("GET", f"/{OID}"), "users": ("DELETE", f"/{OID}")}),
    "users": (10001, {"api_gateway": ("GET", f"/{OID}"), "projects": ("GET", f"/{OID}/process/0")}),
    "subscriptions": (11001, {"api_gateway": ("GET", f"/{OID}")}),
    "img_storage": (11000, {"projects": ("GET", "/b5-not-a-route")}),
    "generative-mock": (7860, {"expand_ai_tool": ("GET", "/sdapi/v1/samplers")}),
}
CLIENT_CERTS = ["nginx", "frontend", "api_gateway", "ws_gateway", "projects", "users", "subscriptions",
                "img_storage", "seaweedfs", "generative-mock", "expand_ai_tool"]
TLS_REFUSED = {"TLS", "CLOSED"}


def peer_files(name):
    d = PKI / "services" / name
    return str(d / "service.crt"), str(d / "service.key")


def context(cert=None, key=None):
    ctx = ssl.create_default_context(cafile=CA)
    if cert:
        ctx.load_cert_chain(cert, key)
    return ctx


def request(server, port, method, path, ctx, session=None):
    """Returns (status | 'TLS' | 'CLOSED' | 'ERROR', body, session, reused)."""
    try:
        raw = socket.create_connection((server, port), timeout=10)
    except OSError as exc:
        return f"ERROR:{type(exc).__name__}", b"", None, False
    try:
        with ctx.wrap_socket(raw, server_hostname=server, session=session) as tls:
            tls.sendall(f"{method} {path} HTTP/1.1\r\nHost: {server}\r\nConnection: close\r\n"
                        f"Content-Length: 0\r\n\r\n".encode())
            data = b""
            while True:
                chunk = tls.recv(65536)
                if not chunk:
                    break
                data += chunk
            sess, reused = tls.session, tls.session_reused
    except ssl.SSLError:
        return "TLS", b"", None, False
    except (ConnectionResetError, BrokenPipeError):
        return "TLS", b"", None, False
    except socket.timeout:
        return "TIMEOUT", b"", None, False
    if not data:
        return "CLOSED", b"", None, False
    if not data.startswith(b"HTTP/"):
        return "ERROR:not-http", b"", None, False
    return int(data.split(b" ", 2)[1]), data.split(b"\r\n\r\n", 1)[-1], sess, reused


def plaintext(server, port):
    try:
        with socket.create_connection((server, port), timeout=10) as raw:
            raw.sendall(f"GET / HTTP/1.1\r\nHost: {server}\r\nConnection: close\r\n\r\n".encode())
            data = raw.recv(64)
    except OSError:
        return "CLOSED"
    if not data:
        return "CLOSED"
    return int(data.split(b" ", 2)[1]) if data.startswith(b"HTTP/") else "NOT-HTTP"


def domain(status):
    return isinstance(status, int) and status < 500 and status != 403


# --------------------------------------------------------------------------- test certificates
def make_cert(subject_cn, issuer_key, issuer_name, not_before, not_after, eku):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_cn)])
    builder = (x509.CertificateBuilder().subject_name(name).issuer_name(issuer_name or name)
               .public_key(key.public_key()).serial_number(x509.random_serial_number())
               .not_valid_before(not_before).not_valid_after(not_after)
               .add_extension(x509.BasicConstraints(ca=issuer_key is None, path_length=None), critical=True)
               .add_extension(x509.ExtendedKeyUsage(eku), critical=False)
               .add_extension(x509.SubjectAlternativeName([x509.DNSName(subject_cn)]), critical=False))
    return key, builder.sign(issuer_key or key, hashes.SHA256())


def write(tmp, label, key, cert):
    c, k = os.path.join(tmp, f"{label}.crt"), os.path.join(tmp, f"{label}.key")
    Path(c).write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    Path(k).write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
    os.chmod(k, 0o600)
    return c, k


now = datetime.datetime.now(datetime.timezone.utc)
tmp = tempfile.mkdtemp(prefix="b5-")
ca_cert = x509.load_pem_x509_certificate((PKI / "ca/ca.crt").read_bytes())
ca_key = serialization.load_pem_private_key((PKI / "ca/ca.key").read_bytes(), password=None)
client_eku = [ExtendedKeyUsageOID.CLIENT_AUTH]
other_ca_key, other_ca = make_cert("b5 other CA", None, None, now - datetime.timedelta(days=1),
                                   now + datetime.timedelta(days=1), client_eku)
NEGATIVE = {}
for allowed_cn in {p for _, peers in SERVERS.values() for p in list(peers)[:1]}:
    k, c = make_cert(allowed_cn, other_ca_key, other_ca.subject, now - datetime.timedelta(hours=1),
                     now + datetime.timedelta(days=1), client_eku)
    NEGATIVE[("other CA", allowed_cn)] = write(tmp, f"other-{allowed_cn}", k, c)
    k, c = make_cert(allowed_cn, ca_key, ca_cert.subject, now - datetime.timedelta(days=31),
                     now - datetime.timedelta(days=1), client_eku)
    NEGATIVE[("expired", allowed_cn)] = write(tmp, f"expired-{allowed_cn}", k, c)
del ca_key

# --------------------------------------------------------------------------- dynamic checks
for server, (port, peers) in SERVERS.items():
    first_peer, (method, path) = next(iter(peers.items()))
    case = f"S08 {server}"
    res.check(case, "no client certificate", request(server, port, method, path, context())[0],
              TLS_REFUSED)
    for kind in ("other CA", "expired"):
        cert, key = NEGATIVE[(kind, first_peer)]
        res.check(case, f"{kind} certificate (CN={first_peer})",
                  request(server, port, method, path, context(cert, key))[0], TLS_REFUSED)
    res.check(case, "server-only certificate (EKU, rabbitmq)",
              request(server, port, method, path, context(*peer_files("rabbitmq")))[0], TLS_REFUSED)
    res.check(case, "plaintext HTTP gets no HTTP answer", plaintext(server, port),
              lambda s: not isinstance(s, int))

    for peer in CLIENT_CERTS:
        ctx = context(*peer_files(peer))
        if peer in peers:
            m, p = peers[peer]
            status, _, sess, _ = request(server, port, m, p, ctx)
            res.check(f"S09 {server}", f"allowed peer {peer} {m} {p.split('?')[0]}", status, domain)
            if sess is not None:
                again = request(server, port, m, p, ctx, session=sess)
                res.check(f"RES {server}", f"session offered by {peer} not resumed",
                          "resumed" if again[3] else "full handshake", "full handshake")
            else:
                res.check(f"RES {server}", f"no resumable session issued to {peer}", "none", "none")
        else:
            status = request(server, port, method, path, ctx)[0]
            res.check(f"D4 {server}", f"peer {peer} refused (valid CA is not enough)", status, 403)

# Positive control of the resumption detector: the public nginx entry issues session tickets.
public = context()
first = request("nginx", 443, "GET", "/", public)
control = request("nginx", 443, "GET", "/", public, session=first[2]) if first[2] else (None, b"", None, False)
res.check("RES control", "public nginx entry resumes a session (detector works)",
          "resumed" if control[3] else "full handshake", "resumed")

# --------------------------------------------------------------------------- static checks
PRODUCT = ["apiGateway", "projects", "users", "subscriptions", "imageStorageService", "wsGateway",
           "frontend", "generative-mock", "Tools"]
forbidden = re.compile(r"rejectUnauthorized\s*:\s*false|verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED|"
                       r"checkServerIdentity|CERT_NONE|check_hostname\s*=\s*False")
bad, agents_without = [], []
for top in PRODUCT:
    for path in (REPO / top).rglob("*"):
        if not path.is_file() or path.suffix not in {".js", ".ts", ".tsx", ".py"} or \
                any(part in {"node_modules", ".next", ".venv", "tests", "__pycache__"} for part in path.parts):
            continue
        text = path.read_text(errors="ignore")
        if forbidden.search(text):
            bad.append(str(path.relative_to(REPO)))
        for m in re.finditer(r"new https\.Agent\((\{.*?\})\)", text, re.S):
            if "maxCachedSessions" not in m.group(1):
                agents_without.append(str(path.relative_to(REPO)))
res.check("STATIC", "no disabled TLS verification in product code", bad or "none", "none")
res.check("STATIC", "every Node https.Agent without cached sessions", agents_without or "none", "none")
nginx = (REPO / "nginx/nginx.conf").read_text()
res.check("STATIC", "nginx: no plaintext upstream", re.findall(r"^\s*proxy_pass\s+http://.*$", nginx, re.M) or "none", "none")
res.check("STATIC", "nginx: upstream verification and no session reuse",
          all(x in nginx for x in ("proxy_ssl_verify on;", "proxy_ssl_session_reuse off;",
                                   "proxy_ssl_certificate ")), True)
for svc in ("frontend", "api_gateway", "ws_gateway", "seaweedfs"):
    res.check("STATIC", f"nginx: expected name for {svc}", f"proxy_ssl_name {svc};" in nginx, True)

for f in Path(tmp).iterdir():
    f.unlink()
os.rmdir(tmp)
res.finish()
