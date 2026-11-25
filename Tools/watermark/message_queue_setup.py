import logging
import os
import ssl
import hashlib
import json
from threading import Lock

import pika
from pika.adapters.blocking_connection import BlockingChannel

from ..config import RABBITMQ_HOST, RABBITMQ_PASS, RABBITMQ_PORT, RABBITMQ_USER

LOGGER = logging.getLogger(__name__)

# PictuRAS patch: AMQPS with the installation CA. TLS is mandatory; there is no plaintext fallback.
RABBITMQ_TLS_CA_FILE = os.getenv("RABBITMQ_TLS_CA_FILE")
RABBITMQ_TLS_SERVER_NAME = os.getenv("RABBITMQ_TLS_SERVER_NAME", RABBITMQ_HOST)


def message_queue_connect() -> tuple[pika.BlockingConnection, BlockingChannel]:
    if not RABBITMQ_TLS_CA_FILE:
        raise RuntimeError("RABBITMQ_TLS_CA_FILE is required (AMQPS only)")

    # Verifies the certificate chain against the CA and the server name.
    context = ssl.create_default_context(cafile=RABBITMQ_TLS_CA_FILE)
    loaded_cas = sorted(hashlib.sha256(c).hexdigest() for c in context.get_ca_certs(binary_form=True))
    os.makedirs("/run/picturas", mode=0o700, exist_ok=True)
    with open(f"/run/picturas/pki-loaded-{os.getpid()}.json", "w") as record:
        json.dump({"pid": os.getpid(), "ca": loaded_cas[0], "trusted_cas": loaded_cas}, record)
    os.chmod(f"/run/picturas/pki-loaded-{os.getpid()}.json", 0o600)

    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=int(RABBITMQ_PORT),
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
        heartbeat=5,
        ssl_options=pika.SSLOptions(context, RABBITMQ_TLS_SERVER_NAME),
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # The fixed image dispatches work onto threads. Observe the actual worker method,
    # not the short AMQP callback that only starts that thread.
    from .message_processor import MessageProcessor
    if not getattr(MessageProcessor, "_picturas_observed_work", False):
        original_handle = MessageProcessor.handle_request_message
        marker = f"/run/picturas/picturas-work-{os.getpid()}.json"
        lock = Lock()
        active = 0
        try:
            os.unlink(marker)
        except FileNotFoundError:
            pass

        def record_work():
            with open(marker + ".tmp", "w") as record:
                json.dump({"pid": os.getpid(), "active_count": active}, record)
            os.chmod(marker + ".tmp", 0o600)
            os.replace(marker + ".tmp", marker)

        def observed_handle(instance, *args, **kwargs):
            nonlocal active
            with lock:
                active += 1
                record_work()
            try:
                return original_handle(instance, *args, **kwargs)
            finally:
                with lock:
                    active -= 1
                    record_work()
        MessageProcessor.handle_request_message = observed_handle
        MessageProcessor._picturas_observed_work = True
    return connection, channel
