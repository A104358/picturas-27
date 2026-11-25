"""B7 SigV4 binds length, content type and internal Host, even if the URL leaks."""
import os
from pathlib import Path
import uuid

import requests

secrets = Path(os.environ["PICTURAS_SECRETS_DIR"])
ca = str(secrets / "pki/ca/ca.crt")
cert = (str(secrets / "pki/services/projects/service.crt"),
        str(secrets / "pki/services/projects/service.key"))
user = "1" * 24
project = "2" * 24
name = f"{uuid.uuid4()}.mp4"
path = f"https://img_storage:11000/video-objects/{user}/{project}/staging/{name}"
response = requests.get(path + "/put-url", params={"size": 1000, "type": "video/mp4"},
                        cert=cert, verify=ca, timeout=10)
assert response.status_code == 200, response.status_code
url = response.json()["url"]
try:
    wrong = requests.put(url, data=b"x" * 1001,
                         headers={"Content-Type": "video/mp4"}, verify=ca, timeout=10)
    assert wrong.status_code == 403, wrong.status_code
    wrong_type = requests.put(url, data=b"x" * 1000,
                              headers={"Content-Type": "video/webm"}, verify=ca, timeout=10)
    assert wrong_type.status_code == 403, wrong_type.status_code
    wrong_host = requests.put(url, data=b"x" * 1000,
                              headers={"Content-Type": "video/mp4", "Host": "localhost:8080"},
                              verify=ca, timeout=10)
    assert wrong_host.status_code == 403, wrong_host.status_code
    assert requests.head(path, cert=cert, verify=ca, timeout=10).status_code == 404
    valid = requests.put(url, data=b"x" * 1000,
                         headers={"Content-Type": "video/mp4"}, verify=ca, timeout=10)
    assert valid.status_code in (200, 201, 204), valid.status_code
    assert requests.head(path, cert=cert, verify=ca, timeout=10).status_code == 200
    print("PASS signed length, content type and Host; valid control")
finally:
    deleted = requests.delete(path, cert=cert, verify=ca, timeout=10)
    assert deleted.status_code == 204, deleted.status_code
