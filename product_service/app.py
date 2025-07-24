
from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from logging.handlers import TimedRotatingFileHandler
from pymongo import MongoClient
import logging
import datetime
import json
import sys

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": "product_service",
            "message": record.getMessage().replace("\n", "\\n"),
        }
        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id
        return json.dumps(log_record)

app = Flask(__name__)
app.config["DEBUG"] = True
metrics = PrometheusMetrics(app)

log_filename = f"/logs/product_service/app.log.{datetime.datetime.now().strftime('%Y-%m-%d')}"

# handler1 = TimedRotatingFileHandler('/logs/app.log', when='midnight', backupCount=90)
handler1 = logging.FileHandler(log_filename)
handler2 = logging.StreamHandler(sys.stdout)

formatter = JsonFormatter()
handler1.setFormatter(formatter)
handler2.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers = [handler1, handler2]


client = MongoClient("mongodb://root:password@mongo:27017/")
db = client["catalog"]
products = db["products"]


@app.route('/products', methods=['POST'])
def add_product():
    try:
        data = request.json
        if not data or not all(key in data for key in ('name', 'description', 'price')):
            return jsonify({"error": "Invalid product data"}), 400

        product = {        
            "name": data["name"],
            "description": data["description"],
            "price": data["price"],
            "tags": data.get("tags", []),
            "created_at": datetime.datetime.utcnow()
        }
        
        result = products.insert_one(product)
        logger.info(f"Product added with ID: {result.inserted_id}", extra={"trace_id": request.headers.get("X-Trace-ID")})
        
        return jsonify({"id": str(result.inserted_id)}), 201
    except Exception as e:
        logger.error(f"Error adding product: {str(e)}", extra={"trace_id": request.headers.get("X-Trace-ID")})
        return jsonify({"error": "Internal server error"}), 500
    
@app.route('/products', methods=['GET'])
def list_products():
    product_list = list(products.find({}, {"_id": 0}))
    logger.info("Product list retrieved", extra={"trace_id": request.headers.get("X-Trace-ID")})
    
    return jsonify(product_list), 200

@app.route('/products/<string:product_id>', methods=['GET'])
def get_product(product_id):
    product = products.find_one({"_id": product_id}, {"_id": 0})
    if not product:
        logger.warning(f"Product with ID {product_id} not found", extra={"trace_id": request.headers.get("X-Trace-ID")})
        return jsonify({"error": "Product not found"}), 404
    
    logger.info(f"Product with ID {product_id} retrieved", extra={"trace_id": request.headers.get("X-Trace-ID")})
    return jsonify(product), 200

@app.route('/products/<string:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    if not data or not all(key in data for key in ('name', 'description', 'price')):
        return jsonify({"error": "Invalid product data"}), 400

    result = products.update_one(
        {"_id": product_id},
        {"$set": {
            "name": data["name"],
            "description": data["description"],
            "price": data["price"],
            "tags": data.get("tags", []),
            "updated_at": datetime.datetime.utcnow()
        }}
    )
    
    if result.matched_count == 0:
        logger.warning(f"Product with ID {product_id} not found for update", extra={"trace_id": request.headers.get("X-Trace-ID")})
        return jsonify({"error": "Product not found"}), 404
    
    logger.info(f"Product with ID {product_id} updated", extra={"trace_id": request.headers.get("X-Trace-ID")})
    return jsonify({"message": "Product updated successfully"}), 200

@app.route('/products/<string:product_id>', methods=['DELETE'])
def delete_product(product_id):
    result = products.delete_one({"_id": product_id})
    if result.deleted_count == 0:
        logger.warning(f"Product with ID {product_id} not found for deletion", extra={"trace_id": request.headers.get("X-Trace-ID")})
        return jsonify({"error": "Product not found"}), 404     
    logger.info(f"Product with ID {product_id} deleted", extra={"trace_id": request.headers.get("X-Trace-ID")})
    return jsonify({"message": "Product deleted successfully"}), 200    

@app.route('/health', methods=['GET'])
def health_check():
    try:
        client.admin.command('ping')
        logger.info("Health check passed", extra={"trace_id": request.headers.get("X-Trace-ID")})
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", extra={"trace_id": request.headers.get("X-Trace-ID")})
        return jsonify({"status": "unhealthy"}), 500

@app.route('/metrics', methods=['GET'])
def metrics_endpoint():
    return metrics.do_metrics()

@app.route('/error')
def error():
    app.logger.error("This is a simulated error on Product-Service")
    return "Error occurred in Product-Service!", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0")