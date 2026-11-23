"""B2 MongoDB authentication, TLS, and scoped role checks (no secret output)."""
import os
import socket
from contextlib import contextmanager
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

root = Path(os.environ["PICTURAS_SECRETS_DIR"])
ca = str(root / "pki/services/projects_mongoDB/ca.crt")
instances = (
    ("projects", "projects_mongoDB", 27018, "project"),
    ("users", "users_mongoDB", 27019, "user"),
    ("subscriptions", "subscriptions_mongoDB", 27017, "subscription"),
)

def secret(name):
    return (root / "values" / name).read_text().strip()

@contextmanager
def service_dns(name):
    original = socket.getaddrinfo
    socket.getaddrinfo = lambda host, port, *a, **kw: original(
        "127.0.0.1" if str(host).lower() == name.lower() else host, port, *a, **kw)
    try:
        yield
    finally:
        socket.getaddrinfo = original

def client(host, port, user=None, password=None, tls=True):
    args = dict(host=host, port=port, serverSelectionTimeoutMS=3000, directConnection=True)
    if tls:
        args.update(tls=True, tlsCAFile=ca)
    if user:
        args.update(username=user, password=password, authSource="admin")
    return MongoClient(**args)

for name, host, port, dbname in instances:
    with service_dns(host):
        try:
            client(host, port, tls=False)[dbname].med_b2.find_one()
        except ServerSelectionTimeoutError:
            pass
        else:
            raise AssertionError("plaintext Mongo accepted")
        try:
            client(host, port)[dbname].med_b2.find_one()
        except OperationFailure:
            pass
        else:
            raise AssertionError("unauthenticated Mongo read accepted")
        svc = client(host, port, f"{name}_svc", secret(f"mongo_{name}_service"))
        marker = {"marker": "b2-conformance"}
        svc[dbname].med_b2.insert_one(marker)
        assert svc[dbname].med_b2.find_one({"marker": "b2-conformance"})
        try:
            svc["other_database"].med_b2.insert_one(marker)
        except OperationFailure:
            pass
        else:
            raise AssertionError("service wrote outside its DB")
        assert set(svc.list_database_names()) <= {dbname}
        backup = client(host, port, "backup_ro", secret(f"mongo_{name}_backup"))
        assert backup[dbname].med_b2.find_one({"marker": "b2-conformance"})
        try:
            backup[dbname].med_b2.insert_one(marker)
        except OperationFailure:
            pass
        else:
            raise AssertionError("backup credential can write")
        svc[dbname].med_b2.delete_many({"marker": "b2-conformance"})
print("B2 Mongo: 3 instances require TLS and auth; service and backup roles scoped")
