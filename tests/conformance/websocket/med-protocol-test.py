"""Protocol-only proof: legacy unchanged; v2 contexts never inferred for attackers."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "evaluation"))
import med
from medlib.api import API
from medlib.ws import WS

security = SimpleNamespace(WS=WS)
original_create, original_resolve = API.create_project, API.share_resolve
os.environ["MED_WS_JOIN_FORMAT"] = "legacy"
med.configure_ws_protocol(security)
assert security.WS is WS and API.create_project is original_create and API.share_resolve is original_resolve
print("PASS legacy: original WS and API methods unchanged")

API.create_project = lambda *a, **kw: SimpleNamespace(id="fixture-project")
API.share_resolve = lambda *a, **kw: SimpleNamespace(ok=True, json={"_id": "fixture-project"})
os.environ["MED_WS_JOIN_FORMAT"] = "v2"
med.configure_ws_protocol(security)


class Socket:
    connected = True
    def connect(self, *args, **kwargs): pass
    def call(self, event, data, **kwargs):
        self.last = event, data
        return {"status": "joined"}


reader, outsider = security.WS("reader"), security.WS("reader")
reader.sio, outsider.sio = Socket(), Socket()
reader.connect("reader-fixture-token")
outsider.connect("outsider-fixture-token")
api = object.__new__(API)
api.share_resolve(SimpleNamespace(jwt="reader-fixture-token"), "presented-fixture-share")
reader.join("fixture-project")
outsider.join("fixture-project")
assert reader.sio.last[1]["access"] == {"kind": "share", "shareId": "presented-fixture-share"}
assert outsider.sio.last[1]["access"] == {"kind": "owner"}
print("PASS v2: share context belongs only to the presenting fixture token; labels grant nothing")
api.create_project(SimpleNamespace(jwt="outsider-fixture-token"))
assert outsider.sio.last == ("join-project", {"projectId": "fixture-project", "access": {"kind": "owner"}})
print("PASS v2 S05: connected owner presents the newly created project explicitly")
