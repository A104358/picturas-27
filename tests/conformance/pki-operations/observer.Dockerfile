FROM picturas-maintenance-probe
RUN pip install --no-cache-dir "python-socketio[client]==5.11.4" websocket-client==1.8.0 boto3==1.35.36
