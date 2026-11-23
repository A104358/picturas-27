FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py server_tls.py ./

CMD ["python", "-u", "server_tls.py"]
