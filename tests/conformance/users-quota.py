"""Daily operations quota of a free account (users service, FREE_DAILY_OP = 5).

Regression for the pre-B4 defect: PUT /:user/process/:n called operations.remove() on a
toJSON() object and answered 701 on the second operation of the day. Calls the users
service directly as the projects peer (the only caller the D4 matrix allows).
"""
from b4_common import Results, call, direct, register

res = Results("users quota")
account = register()
uid = account["id"]


def put(n):
    return direct("users", "PUT", f"/{uid}/process/{n}", peer="projects")


def get(n):
    return direct("users", "GET", f"/{uid}/process/{n}", peer="projects", want_body=True)


def remaining():
    r = call("GET", f"users/{uid}", account["token"])  # the holder, through the gateway
    return r.json().get("remaining_operations") if r.status_code == 200 else r.status_code


res.check("Q01", "first PUT of the day", put(1), 204)
res.check("Q02", "second PUT of the same day (was 701)", put(1), 204)
res.check("Q03", "remaining after two operations", remaining(), 3)
res.check("Q04", "third and fourth via PUT 2", put(2), 204)
res.check("Q05", "fifth via GET reservation (projects path)", get(1)[0], 200)
res.check("Q06", "remaining after five operations", remaining(), 0)
res.check("Q07", "sixth PUT refused at the limit", put(1), 799)
res.check("Q08", "sixth GET reservation refused at the limit", get(1)[0], 701)
res.check("Q09", "limit unchanged after refusals", remaining(), 0)
res.check("Q10", "zero-operation PUT still accepted at the limit", put(0), 204)
res.finish()
