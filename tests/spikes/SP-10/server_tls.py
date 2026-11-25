# mTLS wrapper for the generative mock: same Flask app, TLS with mandatory client certificate and a peer allowlist.
import os
import ssl

from flask import abort, request

from server import app

ALLOWED_PEERS = set(os.environ.get("TLS_ALLOWED_PEERS", "expand_ai_tool").split(","))


@app.before_request
def check_peer():
    sock = request.environ.get("werkzeug.socket")
    peer = sock.getpeercert() if sock is not None else None
    cn = dict(x[0] for x in peer["subject"]).get("commonName") if peer else None
    if cn not in ALLOWED_PEERS:
        abort(403)


if __name__ == "__main__":
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(os.environ["TLS_CERT"], os.environ["TLS_KEY"])
    ctx.load_verify_locations(os.environ["TLS_CA"])
    ctx.verify_mode = ssl.CERT_REQUIRED
    app.run(host="0.0.0.0", port=7860, debug=False, ssl_context=ctx)
