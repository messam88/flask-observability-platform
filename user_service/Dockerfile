FROM python:3.11-slim

WORKDIR /app

COPY app.py .

RUN pip install flask psycopg2-binary bcrypt prometheus_flask_exporter


CMD ["python", "app.py"]