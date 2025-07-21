from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
from logging.handlers import TimedRotatingFileHandler
import requests
import logging
import datetime
import sys
import uuid
import time
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": "A",  # or "B" for service B
            "message": record.getMessage().replace("\n", "\\n"),
        }
        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id
        return json.dumps(log_record)

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# # Configure logging to stdout
# logging.basicConfig(
#     level=logging.INFO,
#     format='[SERVICE A] %(asctime)s %(levelname)s %(message)s',
#     handlers=[logging.StreamHandler(sys.stdout)]
# )

# Structured JSON logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "A", "message": "%(message)s"}',
#     handlers=[logging.StreamHandler(sys.stdout)]
# )

# logging.basicConfig(
#     level=logging.INFO,
#     format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "A", "message": "%(message)s"}',
#     handler = TimedRotatingFileHandler('/logs/app.log', when='midnight', backupCount=90)
# )

# logger = logging.getLogger()
log_filename = f"/logs/service_a/app.log.{datetime.datetime.now().strftime('%Y-%m-%d')}"

# handler1 = TimedRotatingFileHandler('/logs/app.log', when='midnight', backupCount=90)
handler1 = logging.FileHandler(log_filename)
handler2 = logging.StreamHandler(sys.stdout)

formatter = JsonFormatter()
handler1.setFormatter(formatter)
handler2.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers = [handler1, handler2]

@app.route('/')
def home():
    trace_id = str(uuid.uuid4())
    logger.info(f'Service A Home called | trace_id={trace_id}')
    return jsonify(message="Hello from Service A", trace_id=trace_id)

@app.route('/call-b')
def call_b():
    trace_id = str(uuid.uuid4())
    logger.info(f'Service A will call Service B | trace_id={trace_id}')
    try:
        res = requests.get('http://service_b:5000/process', headers={"X-Trace-ID": trace_id})
        logger.info(f"Service B response: {res.status_code} | trace_id={trace_id}")
        return jsonify(status="OK", service_b_status=res.status_code, trace_id=trace_id)
    except Exception as e:
        logger.error(f"Failed to call Service B: {e} | trace_id={trace_id}")
        return jsonify(status="error", error=str(e), trace_id=trace_id), 500

@app.route('/db-sim')
def db_sim():
    trace_id = str(uuid.uuid4())
    logger.debug(f"Simulating DB read | trace_id={trace_id}")
    time.sleep(1)
    logger.info(f"DB read simulated | trace_id={trace_id}")
    return jsonify(message="Data fetched", trace_id=trace_id)

@app.route('/error')
def error():
    app.logger.error("This is a simulated error on Service-A")
    return "Error occurred in Service-A!", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)