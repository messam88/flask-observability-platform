from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from logging.handlers import TimedRotatingFileHandler
import logging
import datetime
import sys
import time
import random
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": "B",  # or "B" for service B
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
#     format='[SERVICE B] %(asctime)s %(levelname)s %(message)s',
#     handlers=[logging.StreamHandler(sys.stdout)]
# )

# Structured JSON logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "B", "message": "%(message)s"}',
#     handlers=[logging.StreamHandler(sys.stdout)]
# )

# logging.basicConfig(
#     level=logging.INFO,
#     format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "B", "message": "%(message)s"}',
#     handlers=[
#         logging.FileHandler("/logs/app.log"),
#         logging.StreamHandler(sys.stdout)
#     ]
# )

# logger = logging.getLogger()
log_filename = f"/logs/service_b/app.log.{datetime.datetime.now().strftime('%Y-%m-%d')}"

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
    trace_id = request.headers.get("X-Trace-ID", "none")
    logger.info(f"Service B Home called | trace_id={trace_id}")
    return jsonify(message="Hello from Service B", trace_id=trace_id)


@app.route('/process')
def process():
    trace_id = request.headers.get("X-Trace-ID", "none")
    logger.info(f"Processing request | trace_id={trace_id}")
    
    # Simulate processing time
    time.sleep(random.uniform(0.5, 1.5))
    
    # Simulate random failure
    if random.choice([True, False]):
        logger.error(f"Simulated error in Service B | trace_id={trace_id}")
        return jsonify(error="Random failure", trace_id=trace_id), 500

    logger.info(f"Request processed successfully | trace_id={trace_id}")
    return jsonify(status="processed", trace_id=trace_id)


@app.route('/error')
def error():
    app.logger.error("This is a simulated error on Service-B")
    return "Error occurred in Service-B!", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)