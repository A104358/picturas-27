import ssl
import time

import pika


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
        self._queue = queue
        while True:
            try:
                self._channel.queue_declare(queue=queue, passive=True)
                self._channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)
                self._channel.start_consuming()
            except (pika.exceptions.AMQPError, OSError):
                time.sleep(3)
                self._connect()
