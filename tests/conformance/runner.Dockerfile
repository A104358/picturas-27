# Conformance test runner: runs the tests from a container on the stack network, now that
# only nginx publishes a port (B3, D-05). Holds no secrets: in-network.sh mounts them.
FROM python:3.12-slim
RUN pip install --no-cache-dir requests==2.32.5 urllib3==2.5.0 PyJWT==2.10.1 cryptography==50.0.2
WORKDIR /repo/tests/conformance
