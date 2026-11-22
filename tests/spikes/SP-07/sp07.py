import ssl, pika, requests, socket
def params(user, pw, ca="/pki/ca.crt", host="rabbitmq", port=5671, tls=True, sni="rabbitmq"):
    kw = {}
    if tls:
        ctx = ssl.create_default_context(cafile=ca)  # verifies chain + hostname
        kw["ssl_options"] = pika.SSLOptions(ctx, server_hostname=sni)
    return pika.ConnectionParameters(host=host, port=port, credentials=pika.PlainCredentials(user, pw), socket_timeout=5, connection_attempts=1, **kw)
def t(label, fn):
    try: r = fn(); print(f"ALLOW  {label}{'' if r is None else ': ' + str(r)[:60]}")
    except Exception as e: print(f"DENY   {label}: {type(e).__name__} {str(e)[:110]}")
W = ("brightness_tool", "brightness-pw-0123456789")
t("plaintext AMQP 5672", lambda: pika.BlockingConnection(params(*W, port=5672, tls=False)).close())
t("plaintext AMQP to TLS port 5671", lambda: pika.BlockingConnection(params(*W, tls=False)).close())
t("TLS wrong CA", lambda: pika.BlockingConnection(params(*W, ca="/pki/otherca.crt")).close())
IP = socket.gethostbyname("rabbitmq")
t("TLS by IP (name not in SAN)", lambda: pika.BlockingConnection(params(*W, host=IP, sni=IP)).close())
t("TLS user/password (Git default)", lambda: pika.BlockingConnection(params("user", "password")).close())
t("TLS guest/guest", lambda: pika.BlockingConnection(params("guest", "guest")).close())
def ch(user=W):
    return pika.BlockingConnection(params(*user)).channel()
t("worker connect TLS", lambda: ch().connection.close())
t("worker passive declare own queue", lambda: ch().queue_declare("brightness_queue", passive=True).method.message_count)
t("worker active declare own queue (durable, same args)", lambda: ch().queue_declare("brightness_queue", durable=True).method.queue)
t("worker basic_get own queue", lambda: ch().basic_get("brightness_queue", auto_ack=False)[0])
t("worker exchange_declare picturas (active, as Tools/utils does)", lambda: ch().exchange_declare("picturas", "direct", durable=True))
t("worker exchange_declare picturas (passive)", lambda: ch().exchange_declare("picturas", passive=True))
t("R3 worker get ws_queue", lambda: ch().basic_get("ws_queue", auto_ack=False)[0])
t("R4 worker declare+delete canary", lambda: (lambda c: (c.queue_declare("med_canary_x", auto_delete=True), c.queue_delete("med_canary_x")))(ch()))
t("worker delete exchange picturas", lambda: ch().exchange_delete("picturas"))
t("worker delete own queue", lambda: ch().queue_delete("brightness_queue", if_empty=True, if_unused=True))
def pub(ex, rk):
    c = ch(); c.confirm_delivery(); c.basic_publish(ex, rk, b'{"spike":1}', mandatory=True); return "confirmed"
t("worker publish picturas -> project_queue (legit reply)", lambda: pub("picturas", "project_queue"))
t("worker publish picturas -> video_queue (other principal's queue)", lambda: pub("picturas", "video_queue"))
t("worker publish picturas -> ws_queue", lambda: pub("picturas", "ws_queue"))
t("worker publish default exchange -> ws_queue", lambda: pub("", "ws_queue"))
t("worker publish picturas_topic -> project_queue (topic perm ok)", lambda: pub("picturas_topic", "project_queue"))
t("worker publish picturas_topic -> video_queue (topic perm denies)", lambda: pub("picturas_topic", "video_queue"))
A = ("admin_spike", "admin-spike-pw-0123456789")
adm = pika.BlockingConnection(params(*A)).channel()
print("queue depths (admin):", {q: adm.queue_declare(q, passive=True).method.message_count for q in ("project_queue", "video_queue", "ws_queue")})
for q in ("project_queue", "video_queue", "ws_queue"): adm.queue_purge(q)
for label, url, auth in (("R5 worker mgmt API https", "https://rabbitmq:15671/api/overview", W), ("admin mgmt API https", "https://rabbitmq:15671/api/overview", A), ("mgmt API plaintext 15672", "http://rabbitmq:15672/api/overview", A), ("prometheus 15692 (no auth)", "http://rabbitmq:15692/metrics", None)):
    try: r = requests.get(url, auth=auth, verify="/pki/ca.crt", timeout=5); print(f"{label}: HTTP {r.status_code} ({len(r.content)} bytes)")
    except Exception as e: print(f"{label}: {type(e).__name__}")
