"""B4 route matrix, run against a stack: one or more checks for every B4-Rnnn row.

Usage: PICTURAS_SECRETS_DIR=... python3 tests/conformance/b4-routes.py
Covers S13 (ACL-C1, persistent links, revocation), S14 (profiles, presets), S15
(subscriptions), F05 (subscribe -> premium -> cancel -> free) and the public exceptions.

Gateway rows: the legitimate caller passes and the others are refused (no session 401,
another account 403, read share on an edit route 403, editor on owner-only routes 403).
Service rows (direct calls): no client certificate -> TLS refused; a valid identity from
another peer -> 403; gateway certificate without identity -> 401; identity for another
route -> 401; another subject -> 403; and a positive control, either direct (reads and
service-only operations) or through the gateway row named in the label (mutations).
"""
import time
import uuid
from pathlib import Path

from b4_common import (TLS, Results, authorised, call, direct, internal_token, matrix_ids,
                       ok2xx, png_bytes, project_version, register, status)

REPO = Path(__file__).resolve().parents[2]
res = Results("B4 routes")
check = res.check
peer_admitted = lambda s: isinstance(s, int) and s not in (401, 403)  # noqa: E731

O, X, E, R = register(), register(), register(), register()
A = register("anonymous")
oid, xid = O["id"], X["id"]
CARD = {"cardHolderName": "B4 Fixture", "cardNumber": "4242424242424242",
        "expiryMonth": "12", "expiryYear": "29", "cvc": 123}


def ver(project):
    """Current version, read by the (premium) owner; sent with every mutation, refused or not."""
    return {"X-Project-Version": project_version(O, project)}


def img_file(seed=1, size=None):
    data = png_bytes(seed) if size is None else b"\x89PNG\r\n\x1a\n" + b"\0" * size
    return {"image": (f"b4-{seed}.png", data, "image/png")}


# ======================================================================= subscriptions (F05, S15)
check("B4-R033", "no session", status("POST", "subscriptions/", body={"subscription": {"user_id": oid}, "card": CARD}), 401)
check("B4-R033", "subscribe for another account", status("POST", "subscriptions/", X["token"], body={"subscription": {"user_id": oid, "interval": 1}, "card": CARD}), 403)
r = call("POST", "subscriptions/", O["token"], body={"subscription": {"user_id": oid, "interval": 1}, "card": CARD})
check("B4-R033", "holder subscribes (F05)", r.status_code, 200)
check("F05", "profile becomes premium", call("GET", f"users/{oid}", O["token"]).json().get("type"), "premium")
for rid, sub in (("B4-R030", ""), ("B4-R031", "/status"), ("B4-R032", "/card")):
    check(rid, "no session", status("GET", f"subscriptions/{oid}{sub}"), 401)
    check(rid, "another account", status("GET", f"subscriptions/{oid}{sub}", X["token"]), 403)
    check(rid, "holder", status("GET", f"subscriptions/{oid}{sub}", O["token"]), ok2xx)
check("B4-R034", "another account", status("PUT", f"subscriptions/{oid}", X["token"], body={"interval": 12}), 403)
check("B4-R034", "holder changes interval", status("PUT", f"subscriptions/{oid}", O["token"], body={"interval": 12}), 200)
check("B4-R036", "another account", status("PUT", f"subscriptions/{oid}/card", X["token"], body=CARD), 403)
check("B4-R036", "holder updates card", status("PUT", f"subscriptions/{oid}/card", O["token"], body=CARD), 200)
check("B4-R035", "another account cancels", status("PUT", f"subscriptions/{oid}/cancel", X["token"], body={}), 403)
check("S15", "subscription list not exposed at the gateway", status("GET", "subscriptions/", O["token"]), {403, 404})

# ======================================================================= projects through the gateway
for rid, who, want in (("B4-R013", None, 401), ("B4-R013", X, 403)):
    check(rid, "no session" if who is None else "another account", status("POST", f"projects/{oid}", who and who["token"], body={"name": "x"}), want)
pids = []
for name in ("B4 main", "B4 disposable", "B4 video"):
    r = call("POST", f"projects/{oid}", O["token"], body={"name": name})
    check("B4-R013", f"owner creates '{name}'", r.status_code, 201)
    pids.append(r.json()["_id"])
P1, P2, P3 = pids
base = f"projects/{oid}/{P1}"

check("B4-R002", "no session", status("POST", f"{base}/share", body={"permission": "edit"}), 401)
check("B4-R002", "another account", status("POST", f"{base}/share", X["token"], body={"permission": "edit"}, headers=ver(P1)), 403)
shares = {}
for key, perm in (("edit", "edit"), ("read", "read"), ("revoke", "read")):
    r = call("POST", f"{base}/share", O["token"], body={"permission": perm}, headers=ver(P1))
    check("B4-R002", f"owner creates a {perm} link", r.status_code, 201)
    shares[key] = r.json()["id"]
SE, SR, SD = shares["edit"], shares["read"], shares["revoke"]
QE, QR = f"owner={oid}&share={SE}", f"owner={oid}&share={SR}"
check("B4-R002", "editor cannot create links", status("POST", f"{base}/share", E["token"], query=QE, body={"permission": "edit"}, headers=ver(P1)), 403)

check("B4-R001", "no session", status("GET", f"{base}/share"), 401)
check("B4-R001", "another account", status("GET", f"{base}/share", X["token"]), 403)
check("B4-R001", "editor cannot list links", status("GET", f"{base}/share", E["token"], query=QE), 403)
r = call("GET", f"{base}/share", O["token"])
check("B4-R001", "owner lists links", r.status_code, 200)
check("S13", "links have no expiresAt (LINK-C1 A)", any("expiresAt" in link for link in r.json()), False)

check("B4-R003", "public link resolution", status("GET", f"projects/share/{SE}"), 200)
check("B4-R003", "unknown link", status("GET", f"projects/share/{uuid.uuid4()}"), 404)
check("B4-R004", "no session", status("GET", f"projects/share/{SE}/project"), 401)
check("B4-R004", "authenticated link holder", status("GET", f"projects/share/{SE}/project", X["token"]), 200)
check("B4-R004", "unknown link", status("GET", f"projects/share/{uuid.uuid4()}/project", X["token"]), 404)

# uploads (R015) and media reads
check("B4-R015", "no session", status("POST", f"{base}/img", files=img_file()), 401)
check("B4-R015", "another account", status("POST", f"{base}/img", X["token"], files=img_file(), headers=ver(P1)), 403)
check("B4-R015", "read link cannot upload", status("POST", f"{base}/img", R["token"], query=QR, files=img_file(), headers=ver(P1)), 403)
check("B4-R015", "owner uploads", status("POST", f"{base}/img", O["token"], files=img_file(1), headers=ver(P1)), 204)
check("B4-R015", "editor uploads", status("POST", f"{base}/img", E["token"], query=QE, files=img_file(2), headers=ver(P1)), 204)
check("B4-R015", "image over 25 MiB refused (D-21)", status("POST", f"{base}/img", O["token"], files=img_file(size=25 * 1024 * 1024 + 1), headers=ver(P1), timeout=120), 413)

for rid, path in (("B4-R007", base), ("B4-R009", f"{base}/imgs")):
    check(rid, "no session", status("GET", path), 401)
    check(rid, "another account", status("GET", path, X["token"]), 403)
    check(rid, "read link", status("GET", path, R["token"], query=QR), 200)
    check(rid, "owner", status("GET", path, O["token"]), 200)
check("B4-R007", "edit link", status("GET", base, E["token"], query=QE), 200)
project = call("GET", base, O["token"]).json()
I1, I2 = project["imgs"][0]["_id"], project["imgs"][1]["_id"]
check("B4-R008", "no session", status("GET", f"{base}/img/{I1}"), 401)
check("B4-R008", "another account", status("GET", f"{base}/img/{I1}", X["token"]), 403)
check("B4-R008", "read link", status("GET", f"{base}/img/{I1}", R["token"], query=QR), 200)
check("B4-R008", "owner", status("GET", f"{base}/img/{I1}", O["token"]), 200)

# pipeline edits
TOOL = {"procedure": "brightness", "params": {"brightness": 1.2}}
check("B4-R017", "no session", status("POST", f"{base}/tool", body=TOOL), 401)
check("B4-R017", "another account", status("POST", f"{base}/tool", X["token"], body=TOOL, headers=ver(P1)), 403)
check("B4-R017", "read link", status("POST", f"{base}/tool", R["token"], query=QR, body=TOOL, headers=ver(P1)), 403)
check("B4-R017", "owner adds a tool", status("POST", f"{base}/tool", O["token"], body=TOOL, headers=ver(P1)), ok2xx)
check("B4-R017", "editor adds a tool", status("POST", f"{base}/tool", E["token"], query=QE, body={"procedure": "contrast", "params": {"contrast": 1.1}}, headers=ver(P1)), ok2xx)
tools = call("GET", base, O["token"]).json()["tools"]
T1, T2 = tools[0]["_id"], tools[1]["_id"]
for rid, method, path, body in (
        ("B4-R021", "PUT", f"{base}/tool/{T1}", {"params": {"brightness": 1.3}}),
        ("B4-R018", "POST", f"{base}/reorder", list(reversed(tools))),
        ("B4-R020", "PUT", base, {"name": "B4 renamed"}),
        ("B4-R029", "POST", f"{base}/dirty", {"dirty": True}),
        ("B4-R014", "POST", f"{base}/preview/{I1}", {}),
        ("B4-R026", "POST", f"{base}/assistant/suggest", {"message": "make it brighter"})):
    check(rid, "no session", status(method, path, body=body), 401)
    check(rid, "another account", status(method, path, X["token"], body=body, headers=ver(P1)), 403)
    check(rid, "read link", status(method, path, R["token"], query=QR, body=body, headers=ver(P1)), 403)
    check(rid, "owner", status(method, path, O["token"], body=body, headers=ver(P1), timeout=120), authorised)
check("B4-R020", "editor renames", status("PUT", base, E["token"], query=QE, body={"name": "B4 edited"}, headers=ver(P1)), 204)

for rid, method, want in (("B4-R027", "POST", ok2xx), ("B4-R028", "DELETE", 204)):
    path = f"{base}/presence"
    check(rid, "no session", status(method, path), 401)
    check(rid, "another account", status(method, path, X["token"]), 403)
    check(rid, "read link (presence needs edit)", status(method, path, R["token"], query=QR), 403)
    check(rid, "owner", status(method, path, O["token"]), want)
    check(rid, "edit link", status(method, path, E["token"], query=QE), want)

# processing
check("B4-R019", "no session", status("POST", f"{base}/process"), 401)
check("B4-R019", "another account", status("POST", f"{base}/process", X["token"], headers=ver(P1)), 403)
check("B4-R019", "read link", status("POST", f"{base}/process", R["token"], query=QR, headers=ver(P1)), 403)
check("B4-R019", "owner applies the pipeline", status("POST", f"{base}/process", O["token"], headers=ver(P1), timeout=120), ok2xx)
time.sleep(3)
for rid, path in (("B4-R010", f"{base}/process"), ("B4-R012", f"{base}/process/url")):
    check(rid, "no session", status("GET", path), 401)
    check(rid, "another account", status("GET", path, X["token"]), 403)
    check(rid, "read link", status("GET", path, R["token"], query=QR), authorised)
    check(rid, "owner", status("GET", path, O["token"]), authorised)
check("B4-R011", "no session", status("DELETE", f"{base}/process"), 401)
check("B4-R011", "another account", status("DELETE", f"{base}/process", X["token"], headers=ver(P1)), 403)
check("B4-R011", "read link", status("DELETE", f"{base}/process", R["token"], query=QR, headers=ver(P1)), 403)
check("B4-R011", "owner", status("DELETE", f"{base}/process", O["token"], headers=ver(P1)), authorised)

# removals by the editor (ACL-C1: editor edits and removes media)
for rid, path in (("B4-R024", f"{base}/tool/{T2}"), ("B4-R023", f"{base}/img/{I2}")):
    check(rid, "no session", status("DELETE", path), 401)
    check(rid, "another account", status("DELETE", path, X["token"], headers=ver(P1)), 403)
    check(rid, "read link", status("DELETE", path, R["token"], query=QR, headers=ver(P1)), 403)
    check(rid, "edit link removes", status("DELETE", path, E["token"], query=QE, headers=ver(P1)), ok2xx)

# video upload (R016)
video = (REPO / "samples/video/sample_10s_720p.mp4").read_bytes()
vfile = lambda: {"video": ("b4.mp4", video, "video/mp4")}  # noqa: E731
vbase = f"projects/{oid}/{P3}"
check("B4-R016", "no session", status("POST", f"{vbase}/video", files=vfile()), 401)
check("B4-R016", "another account", status("POST", f"{vbase}/video", X["token"], files=vfile(), headers=ver(P3)), 403)
check("B4-R016", "owner uploads a video", status("POST", f"{vbase}/video", O["token"], files=vfile(), headers=ver(P3), timeout=180), 204)

# clear and delete (ACL-C1)
check("B4-R025", "no session", status("POST", f"projects/{oid}/{P2}/clear"), 401)
check("B4-R025", "another account", status("POST", f"projects/{oid}/{P2}/clear", X["token"], headers=ver(P2)), 403)
check("B4-R025", "read link", status("POST", f"{base}/clear", R["token"], query=QR, headers=ver(P1)), 403)
check("B4-R025", "owner clears", status("POST", f"projects/{oid}/{P2}/clear", O["token"], headers=ver(P2)), authorised)
check("B4-R022", "no session", status("DELETE", base), 401)
check("B4-R022", "another account", status("DELETE", base, X["token"], headers=ver(P1)), 403)
check("B4-R022", "editor cannot delete the project (ACL-C1)", status("DELETE", base, E["token"], query=QE, headers=ver(P1)), 403)
check("B4-R022", "reader cannot delete the project", status("DELETE", base, R["token"], query=QR, headers=ver(P1)), 403)
check("B4-R022", "owner deletes a project", status("DELETE", f"projects/{oid}/{P2}", O["token"], headers=ver(P2)), ok2xx)

# revocation (R005, S13)
check("B4-R005", "no session", status("DELETE", f"{base}/share/{SD}"), 401)
check("B4-R005", "another account", status("DELETE", f"{base}/share/{SD}", X["token"], headers=ver(P1)), 403)
check("B4-R005", "editor cannot revoke", status("DELETE", f"{base}/share/{SD}", E["token"], query=QE, headers=ver(P1)), 403)
check("B4-R005", "owner revokes", status("DELETE", f"{base}/share/{SD}", O["token"], headers=ver(P1)), ok2xx)
check("S13", "revoked link no longer resolves", status("GET", f"projects/share/{SD}"), 410)
check("S13", "revoked link no longer opens the project", status("GET", base, R["token"], query=f"owner={oid}&share={SD}"), {403, 404, 410})

check("B4-R006", "no session", status("GET", f"projects/{oid}"), 401)
check("B4-R006", "another account", status("GET", f"projects/{oid}", X["token"]), 403)
check("B4-R006", "owner lists projects", status("GET", f"projects/{oid}", O["token"]), 200)

# ======================================================================= users through the gateway (S14, presets)
check("B4-R037", "own session validates", status("GET", f"users/validate/{oid}", O["token"]), 200)
check("B4-R037", "another account's session does not validate", status("GET", f"users/validate/{oid}", X["token"]), 401)
check("B4-R038", "no session", status("GET", f"users/{oid}"), 401)
check("B4-R038", "another account's profile (S14)", status("GET", f"users/{oid}", X["token"]), 403)
check("B4-R038", "own profile", status("GET", f"users/{oid}", O["token"]), 200)
check("S14", "user list not available to users", status("GET", "users/", O["token"]), 403)
check("B4-R039", "public registration cannot create premium (G06)", status("POST", "users/", body={"name": "x", "email": f"b4-{uuid.uuid4().hex}@example.invalid", "password": "x" * 16, "type": "premium"}), 403)
check("B4-R039", "public registration (free)", status("POST", "users/", body={"name": "x", "email": f"b4-{uuid.uuid4().hex}@example.invalid", "password": "x" * 16, "type": "free"}), 201)
check("B4-R040", "login", status("POST", f"users/{X['email']}/login", body={"password": X["password"]}), 201)
check("B4-R040", "wrong password", status("POST", f"users/{X['email']}/login", body={"password": "wrong"}), 401)
check("B4-R041", "no session", status("PUT", f"users/{xid}", body={"name": "y"}), 401)
check("B4-R041", "another account", status("PUT", f"users/{xid}", O["token"], body={"name": "y"}), 403)
check("B4-R041", "own profile", status("PUT", f"users/{xid}", X["token"], body={"name": "B4 renamed"}), 204)
check("B4-R041", "profile update cannot change type (G07)", status("PUT", f"users/{xid}", X["token"], body={"type": "premium"}), 403)
check("B4-R041", "type unchanged", call("GET", f"users/{xid}", X["token"]).json().get("type"), "free")

PRESET = {"name": f"B4 {uuid.uuid4().hex[:6]}", "tools": [TOOL, {"procedure": "contrast", "params": {"contrast": 1.1}}]}
pp = f"users/{oid}/presets"
check("B4-R044", "no session", status("POST", pp, body=PRESET), 401)
check("B4-R044", "another account", status("POST", pp, X["token"], body=PRESET), 403)
r = call("POST", pp, O["token"], body=PRESET)
check("B4-R044", "owner creates", r.status_code, 201)
PR = r.json()["_id"]
check("B4-R043", "no session", status("GET", pp), 401)
check("B4-R043", "another account", status("GET", pp, X["token"]), 403)
check("B4-R043", "owner lists", status("GET", pp, O["token"]), 200)
check("B4-R043", "anonymous cannot manage presets", status("GET", f"users/{A['id']}/presets", A["token"]), 403)
check("B4-R045", "another account", status("PATCH", f"{pp}/{PR}", X["token"], body={"name": "x"}), 403)
check("B4-R045", "owner edits", status("PATCH", f"{pp}/{PR}", O["token"], body={"name": PRESET["name"] + "e"}), 200)
check("B4-R047", "another account", status("POST", f"{pp}/{PR}/share", X["token"]), 403)
r = call("POST", f"{pp}/{PR}/share", O["token"])
check("B4-R047", "owner shares", r.status_code, 200)
SHR = r.json()["shareId"]
check("B4-R048", "shared preset is public", status("GET", f"users/presets/share/{SHR}"), 200)
check("B4-R048", "unknown shared preset", status("GET", f"users/presets/share/{uuid.uuid4()}"), 404)

# ======================================================================= direct service calls
PATH_OTHER = "/b4-other-route"


def family(rid, service, method, path, *, query=None, body=None, bound=True, share="",
           public=False, positive=None):
    """Refusals for one service row; positive = ('direct', expected) or ('via', 'B4-Rnnn')."""
    q = query
    sub = None if public else oid
    good = internal_token(service, method, path, sub, share=share)
    check(rid, "no client certificate", direct(service, method, path, query=q, body=body), TLS)
    check(rid, "valid identity from ws_gateway", direct(service, method, path, peer="ws_gateway", token=good, query=q, body=body), 403)
    check(rid, "gateway certificate, no identity", direct(service, method, path, peer="api_gateway", query=q, body=body), 401)
    check(rid, "identity for another route", direct(service, method, path, peer="api_gateway", query=q, body=body,
                                                    token=internal_token(service, method, PATH_OTHER, sub, share=share)), 401)
    if bound:
        check(rid, "identity of another subject", direct(service, method, path, peer="api_gateway", query=q, body=body,
                                                         token=internal_token(service, method, path, xid)), 403)
    if positive and positive[0] == "direct":
        check(rid, "legitimate identity (direct)", direct(service, method, path, peer="api_gateway", token=good, query=q, body=body), positive[1])
    elif positive:
        res.note(rid, f"legitimate path proven through the gateway ({positive[1]})")


# ---- projects
pb = f"/{oid}/{P1}"
family("B4-R049", "projects", "GET", f"{pb}/share", positive=("direct", 200))
family("B4-R050", "projects", "POST", f"{pb}/share", positive=("via", "B4-R002"))
family("B4-R051", "projects", "GET", f"/share/{SE}", bound=False, public=True, positive=("direct", 200))
family("B4-R052", "projects", "GET", f"/share/{SE}/project", bound=False, positive=("direct", 200))
check("B4-R052", "public identity (no subject) refused", direct("projects", "GET", f"/share/{SE}/project", peer="api_gateway",
                                                               token=internal_token("projects", "GET", f"/share/{SE}/project", None)), 401)
family("B4-R053", "projects", "DELETE", f"{pb}/share/{SE}", positive=("via", "B4-R005"))
family("B4-R054", "projects", "GET", f"/{oid}", positive=("direct", 200))
family("B4-R055", "projects", "GET", pb, positive=("direct", 200))
check("B4-R055", "share holder (direct, link in context)", direct("projects", "GET", pb, peer="api_gateway", query=f"share={SR}",
                                                                  token=internal_token("projects", "GET", pb, R["id"], share=SR)), 200)
family("B4-R056", "projects", "GET", f"{pb}/img/{I1}", positive=("direct", 200))
family("B4-R057", "projects", "GET", f"{pb}/imgs", positive=("direct", 200))
family("B4-R058", "projects", "GET", f"{pb}/process", positive=("direct", authorised))
family("B4-R059", "projects", "GET", f"{pb}/process/url", positive=("direct", authorised))
family("B4-R060", "projects", "GET", f"{pb}/advanced_tools", positive=("direct", 200))
family("B4-R061", "projects", "POST", f"/{oid}", positive=("via", "B4-R013"))
family("B4-R062", "projects", "POST", f"{pb}/preview/{I1}", positive=("via", "B4-R014"))
family("B4-R063", "projects", "POST", f"{pb}/img", positive=("via", "B4-R015"))
family("B4-R064", "projects", "POST", f"{pb}/video", positive=("via", "B4-R016"))
family("B4-R065", "projects", "POST", f"{pb}/tool", positive=("via", "B4-R017"))
family("B4-R066", "projects", "POST", f"{pb}/reorder", positive=("via", "B4-R018"))
family("B4-R067", "projects", "POST", f"{pb}/process", positive=("via", "B4-R019"))
family("B4-R068", "projects", "PUT", pb, positive=("via", "B4-R020"))
family("B4-R069", "projects", "PUT", f"{pb}/tool/{T1}", positive=("via", "B4-R021"))
family("B4-R070", "projects", "DELETE", pb, positive=("via", "B4-R022"))
family("B4-R072", "projects", "DELETE", f"{pb}/img/{I1}", positive=("via", "B4-R023"))
family("B4-R073", "projects", "DELETE", f"{pb}/tool/{T1}", positive=("via", "B4-R024"))
family("B4-R074", "projects", "POST", f"{pb}/clear", positive=("via", "B4-R025"))
family("B4-R075", "projects", "DELETE", f"{pb}/process", positive=("via", "B4-R011"))
family("B4-R076", "projects", "POST", f"{pb}/assistant/suggest", positive=("via", "B4-R026"))
family("B4-R077", "projects", "POST", f"{pb}/presence", positive=("via", "B4-R027"))
family("B4-R078", "projects", "DELETE", f"{pb}/presence", positive=("via", "B4-R028"))
family("B4-R079", "projects", "POST", f"{pb}/presence", positive=("via", "B4-R027; route shadowed by B4-R077"))
family("B4-R080", "projects", "DELETE", f"{pb}/presence", positive=("via", "B4-R028; route shadowed by B4-R078"))
family("B4-R081", "projects", "POST", f"{pb}/dirty", positive=("via", "B4-R029"))

# R071: account clean-up, only the users service for the account being deleted
D = register()
r = call("POST", f"projects/{D['id']}", D["token"], body={"name": "B4 cleanup"})
assert r.status_code == 201
dpath = f"/{D['id']}"
check("B4-R071", "no client certificate", direct("projects", "DELETE", dpath), TLS)
check("B4-R071", "ws_gateway certificate", direct("projects", "DELETE", dpath, peer="ws_gateway"), 403)
check("B4-R071", "gateway with the holder's own identity", direct("projects", "DELETE", dpath, peer="api_gateway",
                                                                  token=internal_token("projects", "DELETE", dpath, D["id"])), 403)
check("B4-R071", "img_storage certificate", direct("projects", "DELETE", dpath, peer="img_storage"), 403)
check("B4-R071", "users service removes the account's projects", direct("projects", "DELETE", dpath, peer="users"), ok2xx)
check("B4-R071", "projects removed", call("GET", f"projects/{D['id']}", D["token"]).json(), lambda v: v == [])

# ---- users
up = f"/users/{oid}/presets"
family("B4-R082", "users", "GET", up, positive=("direct", 200))
family("B4-R083", "users", "POST", up, body=PRESET, positive=("via", "B4-R044"))
family("B4-R084", "users", "PATCH", f"{up}/{PR}", body={"name": "x"}, positive=("via", "B4-R045"))
family("B4-R085", "users", "DELETE", f"{up}/{PR}", positive=("via", "B4-R046"))
family("B4-R086", "users", "POST", f"{up}/{PR}/share", positive=("via", "B4-R047"))
family("B4-R087", "users", "GET", f"/presets/share/{SHR}", bound=False, public=True, positive=("direct", 200))
for rid, label in (("B4-R088", "user list"),):
    check(rid, "no client certificate", direct("users", "GET", "/"), TLS)
    check(rid, "ws_gateway certificate", direct("users", "GET", "/", peer="ws_gateway"), 403)
    check(rid, "gateway certificate, no identity", direct("users", "GET", "/", peer="api_gateway"), 401)
    check(rid, f"{label} refused to a valid user identity", direct("users", "GET", "/", peer="api_gateway",
                                                                   token=internal_token("users", "GET", "/", oid)), 403)
    check(rid, f"{label} refused to the projects service", direct("users", "GET", "/", peer="projects"), 403)
family("B4-R089", "users", "GET", f"/validate/{oid}", bound=False, public=True, positive=None)
check("B4-R089", "legitimate identity (direct, own session)", direct(
    "users", "GET", f"/validate/{oid}", peer="api_gateway", headers={"Authorization": "Bearer " + O["token"]},
    token=internal_token("users", "GET", f"/validate/{oid}", None)), 200)
family("B4-R090", "users", "GET", f"/{oid}", positive=("direct", 200))
for rid, method, path in (("B4-R091", "GET", f"/{oid}/type"), ("B4-R092", "GET", f"/{oid}/process/0"),
                          ("B4-R096", "PUT", f"/{oid}/process/0"), ("B4-R097", "POST", f"/{oid}/process/refund/0")):
    check(rid, "no client certificate", direct("users", method, path), TLS)
    check(rid, "ws_gateway certificate", direct("users", method, path, peer="ws_gateway"), 403)
    check(rid, "gateway with the holder's own identity", direct("users", method, path, peer="api_gateway",
                                                                token=internal_token("users", method, path, oid)), 403)
    check(rid, "subscriptions certificate", direct("users", method, path, peer="subscriptions"), 403)
    # Positive on a fresh account, so earlier writes cannot exhaust the daily quota (the
    # second-write 701 defect is fixed and covered by users-quota.py).
    fresh = register()["id"]
    check(rid, "projects service", direct("users", method, path.replace(oid, fresh), peer="projects"), authorised)
family("B4-R093", "users", "POST", "/", body={"type": "anonymous"}, bound=False, public=True, positive=("direct", 201))
family("B4-R094", "users", "POST", f"/{X['email']}/login", body={"password": X["password"]}, bound=False, public=True,
       positive=("direct", ok2xx))
family("B4-R095", "users", "PUT", f"/{oid}", body={"name": "B4 direct"}, positive=None)
check("B4-R095", "another subject", direct("users", "PUT", f"/{xid}", peer="api_gateway", body={"name": "z"},
                                          token=internal_token("users", "PUT", f"/{xid}", oid)), 403)
check("B4-R095", "type outside the subscription context", direct("users", "PUT", f"/{xid}", peer="api_gateway",
                                                                 body={"type": "premium"}, token=internal_token("users", "PUT", f"/{xid}", xid)), 403)
res.note("B4-R095", "legitimate path proven through the gateway (B4-R041, F05)")
family("B4-R098", "users", "DELETE", f"/{oid}", positive=("via", "B4-R042"))

# presets and account deletion through the gateway, after the direct checks used them
check("B4-R046", "no session", status("DELETE", f"{pp}/{PR}"), 401)
check("B4-R046", "another account", status("DELETE", f"{pp}/{PR}", X["token"]), 403)
check("B4-R046", "owner deletes", status("DELETE", f"{pp}/{PR}", O["token"]), 204)
G = register()
r = call("POST", f"projects/{G['id']}", G["token"], body={"name": "B4 account deletion"})
assert r.status_code == 201
check("B4-R042", "no session", status("DELETE", f"users/{G['id']}"), 401)
check("B4-R042", "another account", status("DELETE", f"users/{G['id']}", X["token"]), 403)
check("B4-R042", "holder deletes the account", status("DELETE", f"users/{G['id']}", G["token"]), 204)
check("B4-R042", "account projects removed (users -> projects)", direct(
    "projects", "GET", f"/{G['id']}", peer="api_gateway", token=internal_token("projects", "GET", f"/{G['id']}", G["id"]),
    want_body=True), lambda v: v == (200, []))

# ---- subscriptions
sp = f"/{oid}"
for rid, path in (("B4-R099", "/"), ("B4-R100", "/cards")):
    check(rid, "no client certificate", direct("subscriptions", "GET", path), TLS)
    check(rid, "ws_gateway certificate", direct("subscriptions", "GET", path, peer="ws_gateway"), 403)
    check(rid, "gateway certificate, no identity", direct("subscriptions", "GET", path, peer="api_gateway"), 401)
    check(rid, "list refused to a valid user identity", direct("subscriptions", "GET", path, peer="api_gateway",
                                                               token=internal_token("subscriptions", "GET", path, oid)), 403)
    check(rid, "list refused to the projects service", direct("subscriptions", "GET", path, peer="projects"), 403)
family("B4-R101", "subscriptions", "GET", sp, positive=("direct", ok2xx))
family("B4-R102", "subscriptions", "GET", f"{sp}/status", positive=("direct", ok2xx))
family("B4-R103", "subscriptions", "GET", f"{sp}/card", positive=("direct", authorised))
family("B4-R104", "subscriptions", "POST", "/", body={"subscription": {"user_id": oid}, "card": CARD}, bound=False, positive=None)
check("B4-R104", "identity of another subject for this holder", direct(
    "subscriptions", "POST", "/", peer="api_gateway", body={"subscription": {"user_id": oid, "interval": 1}, "card": CARD},
    token=internal_token("subscriptions", "POST", "/", xid)), 403)
res.note("B4-R104", "legitimate path proven through the gateway (B4-R033)")
family("B4-R105", "subscriptions", "PUT", sp, body={"interval": 1}, positive=("via", "B4-R034"))
family("B4-R106", "subscriptions", "PUT", f"{sp}/cancel", positive=("via", "B4-R035"))
family("B4-R107", "subscriptions", "PUT", f"{sp}/card", body=CARD, positive=("via", "B4-R036"))

# R108: compensation of the holder's own new subscription only
H = register()
r = call("POST", "subscriptions/", H["token"], body={"subscription": {"user_id": H["id"], "interval": 1}, "card": CARD})
assert r.status_code == 200, ("subscription for R108", r.status_code)
sid = r.json()["_id"]
dp = f"/{sid}"
rollback = ("POST", "/subscriptions/")
check("B4-R108", "no client certificate", direct("subscriptions", "DELETE", dp), TLS)
check("B4-R108", "ws_gateway certificate", direct("subscriptions", "DELETE", dp, peer="ws_gateway",
                                                  token=internal_token("subscriptions", "DELETE", dp, H["id"], origin=rollback)), 403)
check("B4-R108", "gateway certificate, no identity", direct("subscriptions", "DELETE", dp, peer="api_gateway"), 401)
check("B4-R108", "holder identity outside the compensation context", direct(
    "subscriptions", "DELETE", dp, peer="api_gateway", token=internal_token("subscriptions", "DELETE", dp, H["id"])), 403)
check("B4-R108", "compensation context for another subject", direct(
    "subscriptions", "DELETE", dp, peer="api_gateway", token=internal_token("subscriptions", "DELETE", dp, xid, origin=rollback)), 403)
check("B4-R108", "compensation of the holder's own subscription", direct(
    "subscriptions", "DELETE", dp, peer="api_gateway", token=internal_token("subscriptions", "DELETE", dp, H["id"], origin=rollback)), 200)

# ---- img_storage: only the projects service (peer certificate)
fake = f"{uuid.uuid4().hex}/{uuid.uuid4().hex}"
for rid, method, path in (("B4-R109", "POST", f"/copy/{fake}/src/out/b4.png"), ("B4-R110", "DELETE", f"/delete/{fake}/src/b4.png"),
                          ("B4-R111", "GET", f"/image/internal/{fake}/src/b4.png"), ("B4-R112", "POST", f"/upload/{fake}/src")):
    check(rid, "no client certificate", direct("img_storage", method, path), TLS)
    for peer in ("api_gateway", "ws_gateway", "users"):
        check(rid, f"{peer} certificate", direct("img_storage", method, path, peer=peer), 403)
    check(rid, "projects certificate admitted (function proven by B4-R015/R019)", direct("img_storage", method, path, peer="projects"), peer_admitted)

# ======================================================================= F05 end: cancel -> free
check("B4-R035", "holder cancels (F05)", status("PUT", f"subscriptions/{oid}/cancel", O["token"], body={}), 200)
check("F05", "profile returns to free", call("GET", f"users/{oid}", O["token"]).json().get("type"), "free")

# B8 adds a distinct, read-only mTLS delegation surface (tested in depth by B8).
ws_path = f"/internal/ws/projects/{P1}/authorize"
ws_body = {"requestId": "b4-control", "evaluations": [
    {"ref": "owner", "generation": 1, "sequence": 1, "sub": oid,
     "exp": int(time.time()) + 60, "access": {"kind": "owner"}}]}
check("B4-R113", "no client certificate", direct("projects", "POST", ws_path, body=ws_body), TLS)
for peer in ("api_gateway", "users", "projects"):
    check("B4-R113", f"{peer} cannot delegate WS identity",
          direct("projects", "POST", ws_path, peer=peer, body=ws_body), 403)
check("B4-R113", "ws_gateway admitted to read-only authorization endpoint",
      direct("projects", "POST", ws_path, peer="ws_gateway", body=ws_body), 200)

res.finish(matrix_ids() + ["S13", "S14", "S15", "F05"])
