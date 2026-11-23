"""B2 RabbitMQ transport and least-privilege checks (no credentials in output)."""
import os
import socket
import ssl
from contextlib import contextmanager
from pathlib import Path

import pika
import requests

root = Path(os.environ["PICTURAS_SECRETS_DIR"])
ca = root / "pki/services/rabbitmq/ca.crt"

def password(name):
    return (root / "values" / name).read_text().strip()

def connect(user, secret):
    context = ssl.create_default_context(cafile=str(ca))
    return pika.BlockingConnection(pika.ConnectionParameters(
        "localhost", 5671, credentials=pika.PlainCredentials(user, secret),
        ssl_options=pika.SSLOptions(context, "rabbitmq"), connection_attempts=1,
        socket_timeout=5))

def closed(port):
    try:
        with socket.create_connection(("localhost", port), timeout=2):
            return False
    except OSError:
        return True

@contextmanager
def service_dns():
    original = socket.getaddrinfo
    socket.getaddrinfo = lambda host, port, *args, **kwargs: original(
        "127.0.0.1" if host == "rabbitmq" else host, port, *args, **kwargs)
    try:
        yield
    finally:
        socket.getaddrinfo = original

assert closed(5672) and closed(15672)
try:
    old = connect("user", "password")
except pika.exceptions.AMQPError:
    pass
else:
    old.close()
    raise AssertionError("Git-era broker credential accepted")

worker = "brightness_tool"
secret = password("rabbit_" + worker)
conn = connect(worker, secret)
channel = conn.channel()
channel.exchange_declare("picturas", passive=True)
channel.queue_declare("brightness_queue", passive=True)
conn.close()

conn = connect(worker, secret)
try:
    conn.channel().basic_get("ws_queue")
except pika.exceptions.ChannelClosedByBroker as exc:
    assert exc.reply_code == 403
else:
    raise AssertionError("worker can read ws_queue")
finally:
    conn.close()

conn = connect(worker, secret)
channel = conn.channel()
try:
    channel.confirm_delivery()
    channel.basic_publish("picturas", "video_queue", b"denied", mandatory=True)
except pika.exceptions.ChannelClosedByBroker as exc:
    assert exc.reply_code == 403
else:
    raise AssertionError("worker can publish to video_queue")
finally:
    conn.close()

http = requests.Session()
http.trust_env = False
with service_dns():
    worker_response = http.get("https://rabbitmq:15671/api/overview", auth=(worker, secret),
                               verify=str(ca), timeout=5)
assert worker_response.status_code in (401, 403)
with service_dns():
    admin_response = http.get("https://rabbitmq:15671/api/overview",
                              auth=("picturas_admin", password("rabbit_admin")),
                              verify=str(ca), timeout=5)
assert admin_response.status_code == 200
print("B2 broker: plaintext closed, old login denied, worker scope enforced, management admin only")
