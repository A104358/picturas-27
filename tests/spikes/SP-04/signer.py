# Stand-in for the gateway/projects auth route: returns the presigned S3 path for the attempt.
import json, os, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import boto3
from botocore.config import Config
s3 = boto3.client("s3", endpoint_url="https://seaweedfs:9000", aws_access_key_id="uploader", aws_secret_access_key="uploader-secret-0123456789",
                  region_name="us-east-1", verify="/pki/ca.crt", config=Config(s3={"addressing_style": "path"}, signature_version="s3v4"))
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def do_GET(self):
        if self.headers.get("Authorization") != "Bearer good":
            self.send_response(401); self.send_header("Content-Length", "0"); self.end_headers(); return
        token = self.headers["X-Original-URI"].rsplit("/", 1)[1]
        key = {"t1": "staging/sp04-plain", "t2": "staging/sp04 a b+ç(1).mp4", "t3": "staging/sp04-len"}.get(token, "staging/sp04-" + token)
        signed_len = 1000 if token == "t3" else int(self.headers.get("X-Original-Length") or 0)
        url = s3.generate_presigned_url("put_object", Params={"Bucket": "picturas", "Key": key, "ContentLength": signed_len}, ExpiresIn=300)
        p = urllib.parse.urlsplit(url)
        print(json.dumps({"token": token, "key": key, "signed_len": signed_len, "path": p.path}), flush=True)
        self.send_response(200); self.send_header("X-Upload-Uri", f"{p.path}?{p.query}"); self.send_header("Content-Length", "0"); self.end_headers()
ThreadingHTTPServer(("0.0.0.0", 9000), H).serve_forever()
