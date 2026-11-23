import os
from urllib.parse import quote

from pymongo import MongoClient
from pymongo.errors import PyMongoError
H = "projects_mongoDB:27017"

service_password = os.environ["SP06_SERVICE_PASSWORD"]
backup_password = os.environ["SP06_BACKUP_PASSWORD"]
wrong_password = os.environ["SP06_WRONG_PASSWORD"]

def uri(user, password, host, path):
    return "mongodb://" + quote(user, safe="") + ":" + quote(password, safe="") + "@" + host + path

def t(label, uri, fn, **kw):
    try:
        c = MongoClient(uri, serverSelectionTimeoutMS=3000, **kw); r = fn(c); print(f"ALLOW  {label}: {str(r)[:80]}")
    except PyMongoError as e:
        detail = str(e).replace(uri, "[redacted MongoDB URI]")
        for password in (service_password, backup_password, wrong_password):
            detail = detail.replace(password, "***")
        print(f"DENY   {label}: {type(e).__name__}: {detail.split(', full error')[0][:110]}")
TLS = dict(tls=True, tlsCAFile="/pki/ca.crt")
svc = uri("projects_svc", service_password, H, "/projects?authSource=projects")
bak = uri("backup_ro", backup_password, H, "/projects?authSource=projects")
t("no TLS, no creds", f"mongodb://{H}/", lambda c: c.projects.project.find_one())
t("no TLS, service creds", svc, lambda c: c.projects.project.find_one())
t("TLS, wrong CA", svc, lambda c: c.projects.project.find_one(), tls=True, tlsCAFile="/pki/otherca.crt")
t("TLS, no creds find", f"mongodb://{H}/", lambda c: c.projects.project.find_one(), **TLS)
t("TLS, git creds root/example? (none in Git for mongo) -> wrong pw", uri("rootadmin", wrong_password, H, "/?authSource=admin"), lambda c: c.projects.project.find_one(), **TLS)
t("TLS, svc find own", svc, lambda c: c.projects.project.find_one(), **TLS)
t("TLS, svc insert own", svc, lambda c: c.projects.project.insert_one({"x": 1}).inserted_id, **TLS)
t("TLS, svc listDatabases (names)", svc, lambda c: c.list_database_names(), **TLS)
t("TLS, svc insert other DB (users)", svc, lambda c: c.users.user.insert_one({"x": 1}).inserted_id, **TLS)
t("TLS, svc read admin.system.users", svc, lambda c: c.admin.system.users.find_one(), **TLS)
t("TLS, svc createUser", svc, lambda c: c.projects.command("createUser", "evil", pwd="x", roles=["root"]), **TLS)
t("TLS, svc dropDatabase own", svc, lambda c: c.projects.command("dropDatabase"), **TLS)
t("TLS, svc serverStatus", svc, lambda c: c.admin.command("serverStatus")["host"], **TLS)
t("TLS, backup_ro find", bak, lambda c: c.projects.project.find_one(), **TLS)
t("TLS, backup_ro insert", bak, lambda c: c.projects.project.insert_one({"y": 1}).inserted_id, **TLS)
t("TLS, verify hostname: connect by IP alias 't' not in SAN", uri("projects_svc", service_password, "127.0.0.1:1", "/"), lambda c: 0, **TLS)
