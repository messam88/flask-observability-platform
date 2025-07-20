FROM python:3.11-slim

WORKDIR /app

COPY app.py .

RUN pip install flask requests prometheus_flask_exporter


CMD ["python", "app.py"]