# Probe image: runs single network actions inside the application's Docker network.
FROM python:3.12-slim
WORKDIR /med
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY medlib /med/medlib
CMD ["sleep", "infinity"]
