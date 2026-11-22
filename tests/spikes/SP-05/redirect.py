import os, ssl, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith("/redirect"):
            self.send_response(302); self.send_header("Location", os.environ["TARGET"]); self.send_header("Content-Length", "0"); self.end_headers()
        else:  # stall: send headers and 100 bytes, then hang
            self.send_response(200); self.send_header("Content-Length", str(500 << 20)); self.send_header("Content-Type", "video/mp4"); self.end_headers()
            self.wfile.write(b"\0" * 100); self.wfile.flush(); time.sleep(120)
srv = ThreadingHTTPServer(("0.0.0.0", 9443), H)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain("/pki/seaweedfs-redirect.crt", "/pki/seaweedfs-redirect.key")
srv.socket = ctx.wrap_socket(srv.socket, server_side=True); srv.serve_forever()
