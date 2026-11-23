"""B4 identity conformance: S06 (user session JWT), S07 (internal RS256 identity), D7.

Usage: PICTURAS_SECRETS_DIR=... python3 tests/conformance/b4-identity.py
Runs against a development stack (default https://localhost:8080, service ports published).
"""
import time

from b4_common import (GATEWAY_KEY, GATEWAY_PUBLIC, TLS, Results, authorised, call, direct, internal_token,
                       other_rsa_key, register, session_token, status)

res = Results("B4 identity")
now = int(time.time())
user = register()
other = register()
uid = user["id"]
own = f"users/{uid}"

# ---------------------------------------------------------------- S06: user session at the gateway
res.check("S06", "control: issued session reads own profile", status("GET", own, user["token"]), 200)
res.check("S06", "no Authorization", status("GET", own), 401)
res.check("S06", "malformed Authorization", status("GET", own, headers={"Authorization": "Token x"}), 401)
forged = {
    "alg none": session_token(uid, algorithm="none"),
    "HS256 with another secret": session_token(uid, secret="not-the-installation-secret-0123456789"),
    "typ missing": session_token(uid, typ=None),
    "typ of the internal identity": session_token(uid, typ="picturas-internal+jwt"),
    "issuer of another installation": session_token(uid, iss="another-installation"),
    "audience of another installation": session_token(uid, aud="another-audience"),
    "expired (exp = now - 1, no tolerance)": session_token(uid, iat=now - 60, exp=now - 1),
    "lifetime over 7 days": session_token(uid, exp=now + 8 * 86400),
    "issued over 7 days ago": session_token(uid, iat=now - 8 * 86400, exp=now + 3600),
    "sub different from id": session_token(uid, uid=other["id"]),
    "sub missing": session_token(uid, drop=("sub",)),
    "exp missing": session_token(uid, drop=("exp",)),
    "RS256 with the gateway key (algorithm confusion)": session_token(uid, algorithm="RS256", key=GATEWAY_KEY),
    "HS256 keyed with the RS256 public key": session_token(uid, key=GATEWAY_PUBLIC.decode()),
}
for label, token in forged.items():
    res.check("S06", label, status("GET", own, token), 401)
res.check("S06", "valid session of another account on this account's path", status("GET", own, other["token"]), 403)
res.check("S06", "public route still public (login)", status(
    "POST", f"users/{user['email']}/login", body={"password": user["password"]}), 201)

# ---------------------------------------------------------------- D7: ?owner= at the gateway
pr = call("POST", f"projects/{uid}", user["token"], body={"name": "B4 D7"})
assert pr.status_code == 201, ("project", pr.status_code)
path = f"projects/{uid}/{pr.json()['_id']}"
res.check("D7", "owner absent -> allowed", status("GET", path, user["token"]), 200)
res.check("D7", "owner equal to path owner -> allowed", status("GET", path, user["token"], query=f"owner={uid}"), 200)
res.check("D7", "owner contradicts path -> refused", status("GET", path, user["token"], query=f"owner={other['id']}"), 403)
res.check("D7", "owner repeated (multi-value) -> refused", status("GET", path, user["token"], query=f"owner={uid}&owner={uid}"), 403)
res.check("D7", "owner empty -> refused", status("GET", path, user["token"], query="owner="), 403)
res.check("D7", "share repeated (multi-value) -> refused", status("GET", path, other["token"], query=f"owner={uid}&share=a&share=b"), 403)
res.check("D7", "other account with matching owner, no share -> refused", status("GET", path, other["token"], query=f"owner={uid}"), 403)

# ---------------------------------------------------------------- S07: internal identity at each destination
targets = [
    ("users", "GET", f"/{uid}"),
    ("projects", "GET", f"/{uid}"),
    ("subscriptions", "GET", f"/{uid}/status"),
]
for service, method, route in targets:
    case = f"S07-{service}"
    good = lambda **kw: internal_token(service, method, route, uid, **kw)  # noqa: E731
    res.check(case, "control: gateway certificate + valid identity", direct(service, method, route, peer="api_gateway", token=good()), authorised)
    res.check(case, "no client certificate (TLS refused)", direct(service, method, route, token=good()), TLS)
    res.check(case, "valid identity from another peer (ws_gateway)", direct(service, method, route, peer="ws_gateway", token=good()), 403)
    res.check(case, "gateway certificate, no identity", direct(service, method, route, peer="api_gateway"), 401)
    bad = {
        "alg none": good(algorithm="none"),
        "signed by another RSA key": good(key=other_rsa_key()),
        "HS256 keyed with the public key": good(algorithm="HS256", key=GATEWAY_PUBLIC.decode()),
        "issuer differs": good(iss="another-issuer/gateway"),
        "typ differs": good(typ="picturas-session+jwt"),
        "kid unknown": good(kid="gateway-2"),
        "expired (no tolerance)": good(iat=now - 40, exp=now - 1),
        "lifetime over 30 s": good(exp=now + 60),
        "method differs": internal_token(service, "DELETE", route, uid),
        "route differs": internal_token(service, method, route + "/other", uid),
        "share context differs": good(share="other-share"),
        "public flag on a private route": internal_token(service, method, route, None),
        "source differs": good(extra={"source": "ws_gateway"}),
        "requestId missing": good(drop=("requestId",)),
    }
    for other_service in {"users", "projects", "subscriptions"} - {service}:
        bad[f"audience of {other_service} (replay to another service)"] = internal_token(other_service, method, route, uid)
    for label, token in bad.items():
        res.check(case, label, direct(service, method, route, peer="api_gateway", token=token), 401)
    res.check(case, "valid identity, different subject", direct(
        service, method, route, peer="api_gateway", token=internal_token(service, method, route, other["id"])), 403)
    res.check(case, "two share values in the query", direct(
        service, method, route, peer="api_gateway", token=good(share="a"), query="share=a&share=b"), 401)

res.finish(["S06", "D7", "S07-users", "S07-projects", "S07-subscriptions"])
