NET=picturas-spike_default
run(){ # label extra-env...
  docker rm -f wm-spike >/dev/null 2>&1
  docker run -d --name wm-spike --network $NET -v <scratchpad>/sp07/pki:/pki:ro -v <scratchpad>/sp08/images:/images \
    -e RABBITMQ_HOST=rabbitmq -e RABBITMQ_PORT=5671 -e RABBITMQ_USER=watermark_tool -e RABBITMQ_PASS=watermark-pw-0123456789 \
    -e RABBITMQ_REQUESTS_QUEUE_NAME=watermark_queue -e RABBITMQ_RESULTS_EXCHANGE=picturas_topic -e RABBITMQ_RESULTS_ROUTING_KEY=project_queue \
    -e PICTURAS_LOG_LEVEL=INFO "$@" picturas-spike-watermark >/dev/null
  sleep 6; echo "  state: $(docker inspect -f '{{.State.Status}} exit={{.State.ExitCode}}' wm-spike)"; docker logs wm-spike 2>&1 | grep -E 'Error|error|Exception|Published|Processed' | tail -2 | cut -c1-200
}
echo "## 1 no CA configured (must refuse to start, no plaintext fallback)"; run
echo "## 2 wrong CA"; run -e RABBITMQ_TLS_CA_FILE=/pki/otherca.crt
echo "## 3 wrong server name"; run -e RABBITMQ_TLS_CA_FILE=/pki/ca.crt -e RABBITMQ_TLS_SERVER_NAME=projects
echo "## 4 installation CA, process one request end-to-end"; run -e RABBITMQ_TLS_CA_FILE=/pki/ca.crt
cd <scratchpad>/sp07 && docker compose exec -T t python - <<'PY'
import ssl, pika, json, time
p = pika.ConnectionParameters('rabbitmq', 5671, credentials=pika.PlainCredentials('admin_spike', 'admin-spike-pw-0123456789'), ssl_options=pika.SSLOptions(ssl.create_default_context(cafile='/pki/ca.crt'), 'rabbitmq'))
c = pika.BlockingConnection(p).channel()
msg = {"messageId": "spike-wm-1", "timestamp": "2026-11-21T20:00:00", "procedure": "watermark", "parameters": {"inputImageURI": "/images/in.png", "outputImageURI": "/images/out.png"}}
c.basic_publish('picturas_topic', 'watermark_queue', json.dumps(msg).encode())
for _ in range(20):
    m, _, body = c.basic_get('project_queue', auto_ack=True)
    if m: print('  result on project_queue:', body.decode()[:220]); break
    time.sleep(0.5)
else: print('  no result')
PY
docker logs wm-spike 2>&1 | grep -E 'Processed|Published' | cut -c1-160
docker exec wm-spike python -c "import ssl,socket;print('  TLS seen by client: ok')" >/dev/null
docker rm -f wm-spike >/dev/null
