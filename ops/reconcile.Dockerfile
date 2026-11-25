FROM python:3.12-slim
RUN pip install --no-cache-dir pymongo==4.15.5 pika==1.3.2 boto3==1.35.36 requests==2.32.5
WORKDIR /ops
