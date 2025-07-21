from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from logging.handlers import TimedRotatingFileHandler
import logging
import psycopg2
import datetime
import bcrypt
import json
import sys

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": "user_service",
            "message": record.getMessage().replace("\n", "\\n"),
        }
        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id
        return json.dumps(log_record)

app = Flask(__name__)
app.config["DEBUG"] = True
metrics = PrometheusMetrics(app)

log_filename = f"/logs/user_service/app.log.{datetime.datetime.now().strftime('%Y-%m-%d')}"

# handler1 = TimedRotatingFileHandler('/logs/app.log', when='midnight', backupCount=90)
handler1 = logging.FileHandler(log_filename)
handler2 = logging.StreamHandler(sys.stdout)

formatter = JsonFormatter()
handler1.setFormatter(formatter)
handler2.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers = [handler1, handler2]


def get_db():
    return psycopg2.connect(
        dbname="users_db",
        user="user",
        password="password",
        host="postgres"
    )

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        app.logger.info(data)

        username = data['username']
        email = data['email']
        password = data['password']

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (username, email, password_hash)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"id": user_id, "username": username, "email": email}), 201
    except Exception as e:
        app.logger.error(f"Exception on /register [POST]: {e}")
        return jsonify({"message": "Error registering user"}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and bcrypt.checkpw(password.encode(), row[0].encode()):
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, created_at FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify({
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "created_at": row[3]
        })
    return jsonify({"message": "User not found"}), 404


@app.route('/error')
def error():
    app.logger.error("This is a simulated error on User-Service")
    return "Error occurred in User-Service!", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0")