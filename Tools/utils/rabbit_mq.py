import ssl
import hashlib
import json
import os
import time

import pika
from .work_state import active_work


class Rabbit_MQ:
    def __init__(self, host, port, username, password):
        self._host = host
        self._port = int(port)
        self._credentials = pika.PlainCredentials(username, password)
        self._connection = None
        self._channel = None
        self._queue = ""
        self._connect()

    def _connect(self):
        # A broken connection is replaced after a broker restart; TLS is mandatory.
        context = ssl.create_default_context(cafile="/run/secrets/pki/ca.crt")
        loaded_cas = sorted(hashlib.sha256(c).hexdigest() for c in context.get_ca_certs(binary_form=True))
        os.makedirs("/run/picturas", mode=0o700, exist_ok=True)
        with open(f"/run/picturas/pki-loaded-{os.getpid()}.json", "w") as record:
            json.dump({"pid": os.getpid(), "ca": loaded_cas[0], "trusted_cas": loaded_cas}, record)
        os.chmod(f"/run/picturas/pki-loaded-{os.getpid()}.json", 0o600)
        params = pika.ConnectionParameters(
            self._host, self._port, "/", self._credentials,
            ssl_options=pika.SSLOptions(context, self._host),
            heartbeat=0,
        )
        while True:
            try:
                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()
                self._channel.exchange_declare(exchange="picturas", passive=True)
                return
            except pika.exceptions.AMQPError:
                time.sleep(3)

    def send_rabbit_msg(self, msg, queue):
        self._channel.basic_publish(exchange="picturas", routing_key=queue, body=msg)

    def read_rabbit_msg(self, queue, callback):
        def observed_callback(*args):
            with active_work():
                return callback(*args)
        self._queue = queue
        while True:
            try:
                self._channel.queue_declare(queue=queue, passive=True)
                self._channel.basic_consume(queue=queue, on_message_callback=observed_callback, auto_ack=True)
                self._channel.start_consuming()
            except (pika.exceptions.AMQPError, OSError):
                time.sleep(3)
                self._connect()
