"""Atomic network actions, usable on the host and inside the probe container.

Each action returns a JSON-serialisable dict with at least:
  ok          - the operation was accepted by the server
  error_kind  - None | tls | refused | timeout | dns | auth | http | other
Callers decide admitted/refused/inconclusive from these fields plus an effect check.
"""
from __future__ import annotations

import base64
import hashlib
import json
import socket
import ssl
import uuid
from typing import Any

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def classify_exception(exc: BaseException) -> str:
    text = repr(exc).lower()
    if isinstance(exc, requests.exceptions.SSLError) or "ssl" in text or "certificate" in text \
            or "handshake" in text or "tlsv1" in text:
        return "tls"
    if isinstance(exc, (requests.exceptions.Timeout, socket.timeout, TimeoutError)) or "timed out" in text:
        return "timeout"
    if "name or service not known" in text or "nodename nor servname" in text \
            or "temporary failure in name resolution" in text or "getaddrinfo" in text:
        return "dns"
    if "refused" in text or "connection reset" in text or "remotedisconnected" in text \
            or "connectionerror" in text or "max retries" in text:
        return "refused"
    return "other"


def _cert_args(spec: dict) -> dict:
    cert = spec.get("client_cert")
    if cert:
        return {"cert": (cert["crt"], cert["key"])}
    return {}


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def http(spec: dict) -> dict:
    """spec: method, url, headers?, json?, files? {field: {name, b64, ctype}}, timeout?"""
    files = None
    if spec.get("files"):
        files = {k: (v["name"], base64.b64decode(v["b64"]), v.get("ctype", "application/octet-stream"))
                 for k, v in spec["files"].items()}
    try:
        r = requests.request(
            spec["method"], spec["url"], headers=spec.get("headers") or {},
            json=spec.get("json"), files=files, timeout=spec.get("timeout", 20),
            verify=spec.get("verify", False), allow_redirects=False, **_cert_args(spec))
    except Exception as exc:  # noqa: BLE001 - every failure is classified
        return {"ok": False, "status": None, "error_kind": classify_exception(exc), "error": repr(exc)[:300]}
    body: Any
    try:
        body = r.json()
    except ValueError:
        body = r.text[:2000]
    return {"ok": 200 <= r.status_code < 300, "status": r.status_code, "error_kind": None,
            "body": body, "headers": {k.lower(): v for k, v in r.headers.items()
                                      if k.lower() in ("x-project-version", "content-type")}}


def fetch_sha(spec: dict) -> dict:
    """Download a URL and return its SHA-256 (body never returned)."""
    h = hashlib.sha256()
    n = 0
    try:
        with requests.get(spec["url"], stream=True, timeout=spec.get("timeout", 120),
                          verify=spec.get("verify", False), **_cert_args(spec)) as r:
            if r.status_code != 200:
                return {"ok": False, "status": r.status_code, "error_kind": "http"}
            for chunk in r.iter_content(1 << 20):
                h.update(chunk)
                n += len(chunk)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "status": None, "error_kind": classify_exception(exc), "error": repr(exc)[:300]}
    return {"ok": True, "status": 200, "error_kind": None, "sha256": h.hexdigest(), "bytes": n}


def tcp(spec: dict) -> dict:
    try:
        with socket.create_connection((spec["host"], int(spec["port"])), timeout=spec.get("timeout", 1.0)):
            return {"ok": True, "error_kind": None}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_kind": classify_exception(exc)}


# ---------------------------------------------------------------------------
# MongoDB
# ---------------------------------------------------------------------------

def mongo(spec: dict) -> dict:
    """spec: uri, db, coll?, op in {find_one, insert_canary, list_dbs, drop_canary, update_one}."""
    import pymongo
    from bson import ObjectId
    try:
        client = pymongo.MongoClient(spec["uri"], serverSelectionTimeoutMS=3000,
                                     connectTimeoutMS=3000, directConnection=True)
        db = client[spec["db"]]
        op = spec["op"]
        if op == "find_one":
            doc = db[spec["coll"]].find_one({}, {"_id": 1})
            return {"ok": True, "error_kind": None, "found": doc is not None}
        if op == "insert_canary":
            db["med_canary"].insert_one({"med": str(uuid.uuid4())})
            return {"ok": True, "error_kind": None}
        if op == "list_dbs":
            names = client.list_database_names()
            return {"ok": True, "error_kind": None, "names": names}
        if op == "drop_canary":
            db.drop_collection("med_canary")
            return {"ok": True, "error_kind": None}
        if op == "update_one":
            flt = spec["filter"]
            if "_id" in flt:
                flt = {**flt, "_id": ObjectId(flt["_id"])}
            r = db[spec["coll"]].update_one(flt, {"$set": spec["set"]})
            return {"ok": r.matched_count == 1, "error_kind": None, "matched": r.matched_count}
        if op == "get_field":
            flt = spec["filter"]
            if "_id" in flt:
                flt = {**flt, "_id": ObjectId(flt["_id"])}
            doc = db[spec["coll"]].find_one(flt, {spec["field"]: 1})
            return {"ok": doc is not None, "error_kind": None,
                    "value": None if doc is None else str(doc.get(spec["field"]))}
        return {"ok": False, "error_kind": "other", "error": f"unknown op {op}"}
    except Exception as exc:  # noqa: BLE001
        text = repr(exc).lower()
        kind = "auth" if ("auth" in text or "unauthorized" in text or "requires authentication" in text
                          or "not authorized" in text) else classify_exception(exc)
        return {"ok": False, "error_kind": kind, "error": repr(exc)[:300]}


# ---------------------------------------------------------------------------
# RabbitMQ
# ---------------------------------------------------------------------------

def amqp(spec: dict) -> dict:
    """spec: host, port, user, password, op in {connect, get, declare_delete}, queue?"""
    import pika
    try:
        params = pika.ConnectionParameters(
            host=spec["host"], port=int(spec["port"]),
            credentials=pika.PlainCredentials(spec.get("user", ""), spec.get("password", "")),
            socket_timeout=5, blocked_connection_timeout=5, connection_attempts=1)
        conn = pika.BlockingConnection(params)
    except Exception as exc:  # noqa: BLE001
        text = repr(exc).lower()
        kind = "auth" if ("access_refused" in text or "probableauthentication" in text) else classify_exception(exc)
        return {"ok": False, "error_kind": kind, "error": repr(exc)[:300]}
    try:
        ch = conn.channel()
        op = spec["op"]
        if op == "connect":
            return {"ok": True, "error_kind": None}
        if op == "get":
            ch.queue_declare(queue=spec["queue"], passive=True)
            method, _props, _body = ch.basic_get(queue=spec["queue"], auto_ack=False)
            if method is not None:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return {"ok": True, "error_kind": None, "got_message": method is not None}
        if op == "declare_delete":
            q = f"med_canary_{uuid.uuid4().hex[:8]}"
            ch.queue_declare(queue=q, auto_delete=True)
            ch.queue_delete(queue=q)
            return {"ok": True, "error_kind": None}
        return {"ok": False, "error_kind": "other", "error": f"unknown op {op}"}
    except Exception as exc:  # noqa: BLE001
        text = repr(exc).lower()
        kind = "auth" if ("access_refused" in text or "403" in text) else classify_exception(exc)
        return {"ok": False, "error_kind": kind, "error": repr(exc)[:300]}
    finally:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass


def rabbit_mgmt(spec: dict) -> dict:
    """spec: url, user, password."""
    try:
        r = requests.get(spec["url"], auth=(spec.get("user", ""), spec.get("password", "")),
                         timeout=10, verify=False)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "status": None, "error_kind": classify_exception(exc)}
    return {"ok": r.status_code == 200, "status": r.status_code,
            "error_kind": None if r.status_code == 200 else ("auth" if r.status_code in (401, 403) else "http")}


# ---------------------------------------------------------------------------
# S3 (SeaweedFS)
# ---------------------------------------------------------------------------

def s3(spec: dict) -> dict:
    """spec: endpoint, access, secret, bucket, op in {list, create_bucket, delete_bucket,
    head, list_prefix}, key?, prefix?"""
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
    try:
        client = boto3.client(
            "s3", endpoint_url=spec["endpoint"], aws_access_key_id=spec.get("access") or None,
            aws_secret_access_key=spec.get("secret") or None, region_name="us-east-1",
            verify=False, config=Config(signature_version="s3v4", retries={"max_attempts": 1},
                                        connect_timeout=5, read_timeout=20,
                                        s3={"addressing_style": "path"}))
        op = spec["op"]
        if op == "list":
            r = client.list_objects_v2(Bucket=spec["bucket"], MaxKeys=1)
            return {"ok": True, "error_kind": None, "keys": r.get("KeyCount", 0)}
        if op == "list_prefix":
            keys, token = [], None
            while True:
                kw = {"Bucket": spec["bucket"], "Prefix": spec["prefix"]}
                if token:
                    kw["ContinuationToken"] = token
                r = client.list_objects_v2(**kw)
                keys += [o["Key"] for o in r.get("Contents", [])]
                if not r.get("IsTruncated"):
                    break
                token = r.get("NextContinuationToken")
            return {"ok": True, "error_kind": None, "keys_list": keys}
        if op == "create_bucket":
            client.create_bucket(Bucket=spec["bucket"])
            return {"ok": True, "error_kind": None}
        if op == "delete_bucket":
            client.delete_bucket(Bucket=spec["bucket"])
            return {"ok": True, "error_kind": None}
        if op == "head":
            try:
                client.head_object(Bucket=spec["bucket"], Key=spec["key"])
                return {"ok": True, "error_kind": None, "exists": True}
            except ClientError as e:
                code = str(e.response.get("Error", {}).get("Code"))
                if code in ("404", "NoSuchKey", "NotFound"):
                    return {"ok": True, "error_kind": None, "exists": False}
                raise
        return {"ok": False, "error_kind": "other", "error": f"unknown op {op}"}
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code"))
        kind = "auth" if code in ("AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch", "403") else "http"
        return {"ok": False, "error_kind": kind, "error": code}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_kind": classify_exception(exc), "error": repr(exc)[:300]}


ACTIONS = {
    "http": http, "fetch_sha": fetch_sha, "tcp": tcp, "mongo": mongo,
    "amqp": amqp, "rabbit_mgmt": rabbit_mgmt, "s3": s3,
}


def run_action(spec: dict) -> dict:
    fn = ACTIONS.get(spec.get("action"))
    if fn is None:
        return {"ok": False, "error_kind": "other", "error": "unknown action"}
    return fn(spec)


def to_files(field: str, name: str, data: bytes, ctype: str) -> dict:
    return {field: {"name": name, "b64": base64.b64encode(data).decode(), "ctype": ctype}}


def dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)
