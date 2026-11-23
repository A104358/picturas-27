import logging
import os
import ssl

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

    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=int(RABBITMQ_PORT),
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
        heartbeat=5,
        ssl_options=pika.SSLOptions(context, RABBITMQ_TLS_SERVER_NAME),
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    return connection, channel
