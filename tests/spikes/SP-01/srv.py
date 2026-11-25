import os, ssl, sys, time, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODE = os.environ["MODE"]

def log(**kw):
    print(json.dumps({"t": round(time.time(), 3), "mode": MODE, **kw}), flush=True)

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def reply(self, code, body=b"", headers=None):
        self.send_response(code)
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def read_body(self):
        t0 = time.time(); n = 0; first = None
        te = self.headers.get("Transfer-Encoding", "")
        if "chunked" in te.lower():
            while True:
                size = int(self.rfile.readline().strip().split(b";")[0], 16)
                if size == 0:
                    self.rfile.readline(); break
                left = size
                while left:
                    b = self.rfile.read(min(65536, left))
                    if first is None: first = time.time()
                    n += len(b); left -= len(b)
                self.rfile.readline()
        else:
            left = int(self.headers.get("Content-Length") or 0)
            while left:
                b = self.rfile.read(min(65536, left))
                if not b: break
                if first is None: first = time.time()
                n += len(b); left -= len(b)
        return t0, first, time.time(), n, te
    def do_GET(self): self.handle_any()
    def do_PUT(self): self.handle_any()
    def do_POST(self): self.handle_any()
    def handle_any(self):
        if MODE == "auth":
            log(path=self.path, method=self.command, cl=self.headers.get("Content-Length"),
                te=self.headers.get("Transfer-Encoding"), orig=self.headers.get("X-Original-URI"),
                orig_len=self.headers.get("X-Original-Length"))
            if self.path.startswith("/denied/"):
                code = int(self.path.rsplit("/", 1)[1])
                self.reply(code, json.dumps({"error": code}).encode(), {"Content-Type": "application/json"}); return
            a = self.headers.get("Authorization", "")
            if a.startswith("Bearer deny-"):
                self.reply(403, headers={"X-Deny-Status": a.split("-", 1)[1]}); return
            if a == "Bearer slow":
                time.sleep(5)
            if a == "Bearer good" or a == "Bearer slow":
                self.reply(200, headers={"X-Upload-Key": "attempt-123", "X-Upload-Size": "999"})
            else:
                self.reply(401)
        elif MODE == "sink":
            t0, first, end, n, te = self.read_body()
            log(path=self.path, headers_at=t0, first_byte_at=first, end_at=end, bytes=n, te=te,
                cl=self.headers.get("Content-Length"), key=self.headers.get("X-Upload-Key"),
                host=self.headers.get("Host"))
            self.reply(201, json.dumps({"bytes": n, "headers_at": t0, "end_at": end}).encode())
        else:  # tls
            t0, first, end, n, te = self.read_body()
            peer = self.connection.getpeercert()
            cn = dict(x[0] for x in peer["subject"])["commonName"] if peer else None
            log(path=self.path, peer_cn=cn, headers_at=t0, end_at=end, bytes=n)
            self.reply(200, f"tls-ok peer={cn}\n".encode())

port = int(os.environ.get("PORT", "9000"))
srv = ThreadingHTTPServer(("0.0.0.0", port), H)
if MODE == "tls":
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(os.environ["CERT"], os.environ["KEY"])
    ctx.load_verify_locations(os.environ["CA"])
    ctx.verify_mode = ssl.CERT_REQUIRED
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
log(event="listening", port=port)
srv.serve_forever()
