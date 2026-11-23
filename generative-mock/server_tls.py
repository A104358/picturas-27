# mTLS wrapper for the generative mock (Phase 2, B5; SP-10): the same Flask app, served over
# TLS with a mandatory client certificate from the installation CA and a peer allowlist
# (only expand_ai_tool, D4 matrix). TLS 1.3 without session tickets: no resumption, every
# connection presents its certificate. The own certificate is checked at start-up and the
# process stops when it expires (PKI-C3 A).
import os
import ssl
import sys
import threading
import time

from flask import abort, request

from server import app

PKI = os.environ.get("PKI_DIR", "/run/secrets/pki")
CERT, KEY, CA = f"{PKI}/service.crt", f"{PKI}/service.key", f"{PKI}/ca.crt"
ALLOWED_PEERS = {"expand_ai_tool"}


@app.before_request
def check_peer():
    sock = request.environ.get("werkzeug.socket")
    peer = sock.getpeercert() if sock is not None else None
    cn = dict(x[0] for x in peer["subject"]).get("commonName") if peer else None
    if cn not in ALLOWED_PEERS:
        abort(403)


def guard_validity():
    info = ssl._ssl._test_decode_cert(CERT)
    not_before = ssl.cert_time_to_seconds(info["notBefore"])
    not_after = ssl.cert_time_to_seconds(info["notAfter"])

    def stop(reason):
        print(f"pki: own certificate {reason}; stopping (renew with ops/pki.sh)", file=sys.stderr, flush=True)
        os._exit(1)

    now = time.time()
    if now < not_before:
        stop("not yet valid")
    if now >= not_after:
        stop("expired")
    timer = threading.Timer(not_after - now, stop, args=("expired",))
    timer.daemon = True
    timer.start()


if __name__ == "__main__":
    guard_validity()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.num_tickets = 0
    ctx.options |= ssl.OP_NO_TICKET
    ctx.load_cert_chain(CERT, KEY)
    ctx.load_verify_locations(CA)
    ctx.verify_mode = ssl.CERT_REQUIRED
    app.run(host="0.0.0.0", port=7860, debug=False, ssl_context=ctx)
