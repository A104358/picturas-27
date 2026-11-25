FROM python:3.12-slim
RUN pip install --no-cache-dir requests==2.32.5 cryptography==50.0.2 pymongo==4.15.5 pika==1.3.2
