




We have microservices setup with two Flask apps (service_a and service_b), each running in its own Docker container.
Observability is provided by Prometheus (metrics), Loki (logs), Promtail (log shipping), and Grafana (dashboarding).
Prometheus scrapes metrics from your services, such as HTTP request counts, error rates, and latency.
Promtail collects logs from your containers and ships them to Loki, where you can query logs in Grafana.
Grafana is used to visualize metrics and logs, build dashboards, and set up alerts.
The system is designed for monitoring service health, error rates, performance, and resource usage.
The README includes instructions for running, debugging, and extending the system, plus example queries and dashboard panel ideas.

## Runnig system 
```
docker compose up --build
```

## docker debuging 
```
docker exec -it <container> bash

ls /var/lib/docker/containers/
docker inspect --format='{{.LogPath}}' service_a
docker logs service_a

docker exec -it service_a cat /logs/app.log | head -n 1


docker compose stop service_b
docker compose start service_b


docker exec -it promtail sh
ls -l /logs/
```


## local development 
```
python -m venv venv
source venv/bin/activate
```


## URLs:
- Flask app service_a: http://localhost:5000
- Flask app service_b: http://localhost:5001
- Grafana: http://localhost:3000 (login: admin / admin)
- Loki: http://loki:3100
- Prometheus: http://prometheus:9090


In Grafana:

Go to ⚙️ Settings → Data Sources
Click “Add data source”
Choose “Loki”
Set the URL to: 
    http://loki:3100
Click Save & Test (should say "Data source is working")

Open Grafana at http://localhost:3000
Go to ⚙️ Settings → Data Sources
Click Add data source
Choose Prometheus
Set URL to: http://prometheus:9090
Click Save & Test


Go to the “Explore” section (🔍 icon in sidebar)
In the top Data Source dropdown, select Loki
In the Log labels selector, click on Label browser or manually type a label filter, for example:
    {job="flask-app"}
You should see log lines coming from your Flask service, like:
    2025-06-29T12:00:00Z INFO Visited home endpoint


{job="flask-app"} |= "ERROR"
|= means "contains this exact string"
|~ for regex match
!= for "does not contain"


1. Match logs with word ERROR
    {job="flask-app"} |= "ERROR"
2. Regex match (case-insensitive error, e.g. error, Error, ERROR)
    {job="flask-app"} |~ "(?i)error"
3. Match logs that contain JSON with "level": "error"
If you're logging in JSON format (e.g., from loguru, pino, logrus, etc.):
    {job="flask-app"} |= `"level":"error"`


{container_name="service_a"}
{container_name="service_a"} |= "ERROR"
{container_name="service_b"}
{job="service_a"}  |= "trace_id=048f16d9-ad69-4dc3-90ac-b7d9d5181270"
{job="service_a", level="ERROR"}
{job="service-a", level="INFO"}

## Prometheus
- Purpose: Metrics collection and monitoring
- What it does: Prometheus scrapes numeric metrics (like CPU usage, memory, request counts, latency) from instrumented applications, servers, or exporters at regular intervals.
- Data type: Time-series data (numbers over time)
- Use case: Alerting on system health, building dashboards for resource utilization, service-level metrics, etc.
- Example metrics:
-- HTTP request count
-- CPU load
-- Number of active users 
-- Memory usage

## Promtail
- Purpose: Log collection and forwarding for Loki
- What it does: Promtail tails log files (or collects logs from Docker) and ships them to Loki for indexing and querying.
- Data type: Unstructured or semi-structured logs (text data)
- Use case:
Centralized log aggregation, searching logs by labels, troubleshooting errors or incidents from logs.
- Example logs:
-- Application error logs
-- Access logs
-- Debug or info statements from your code



```
# scrape_configs:
#   - job_name: docker
#     static_configs:
#       - targets:
#           - localhost
#         labels:
#           job: flask-app
#           __path__: /var/lib/docker/containers/*/*.log

# scrape_configs:
#   - job_name: docker
#     docker_sd_configs:
#       - host: unix:///var/run/docker.sock
#         refresh_interval: 5s
#     relabel_configs:
#       - source_labels: [__meta_docker_container_name]
#         regex: '/(.*)'
#         target_label: container_name
#       - source_labels: [__meta_docker_container_log_stream]
#         target_label: stream
#       - source_labels: [__meta_docker_container_id]
#         target_label: container_id
#       - source_labels: [__meta_docker_container_image]
#         target_label: image
#       - source_labels: [__meta_docker_container_labels_job]
#         target_label: job
```

## To build a dashboard for service health and errors in Grafana, you should focus on these major metrics:

### **From Prometheus (metrics):**
- HTTP request count (total and per endpoint)
    - sum by (endpoint) (flask_http_request_total)
    - sum(flask_http_request_total)
- HTTP error rate (number of 4xx/5xx responses)
    - sum by (endpoint) (flask_http_request_total{status=~"4.."})
    - sum by (endpoint) (flask_http_request_total{status=~"5.."})
    - sum by (endpoint) (flask_http_request_total{status=~"[45].."})
    - sum(flask_http_request_total{status=~"[45].."}) / sum(flask_http_request_total)
- Request latency (average, p95, p99)
    - sum(rate(flask_http_request_duration_seconds_sum[5m])) / sum(rate(flask_http_request_duration_seconds_count[5m]))
    - histogram_quantile(0.95, sum by (le) (rate(flask_http_request_duration_seconds_bucket[5m])))
    - histogram_quantile(0.99, sum by (le) (rate(flask_http_request_duration_seconds_bucket[5m])))
- Uptime (service availability)
    - up{job="service_a"}
    - up{job="service_b"}    
- CPU and memory usage (container or host level) ?

### Alerting ? 

### **From Loki/Promtail (logs):**
- Number of error log entries (`level="ERROR"`)
- Recent error messages (with trace IDs if available)
- Log volume (number of log lines per service)
- Specific error types or patterns (e.g., by message content or exception type)

### **Dashboard panels to include:**
- Service status (up/down)
- Error rate over time
- Top error messages
- Request latency histogram
- Request count per endpoint
- Resource usage (CPU, memory)
- Recent logs (filtered by error level or trace ID)

These metrics and panels will give you a clear view of service health, performance, and error trends.



## To make this system more complex for training and learning purposes, consider adding the following features:

1. **Add More Services:**  
   Introduce additional microservices (e.g., a database service, a cache, or a third Flask app) to simulate a real-world distributed system.

2. **Distributed Tracing:**  
   Integrate OpenTelemetry or Jaeger to trace requests across services and visualize end-to-end latency.

3. **Custom Metrics:**  
   Add custom Prometheus metrics (e.g., business KPIs, queue lengths, cache hit rates) in your Flask apps.

4. **Alerting and Auto-remediation:**  
   Set up more advanced Grafana alerts and add scripts or webhooks for automated remediation (e.g., restart a service on failure).

5. **Log Enrichment:**  
   Add more context to logs (user IDs, request IDs, etc.) and experiment with log parsing and filtering in Loki.

6. **Security and Access Control:**  
   Add authentication/authorization to your services and monitor security-related events.

7. **Simulate Failures:**  
   Use tools like `chaos-mesh` or custom scripts to randomly kill containers, introduce latency, or drop requests to test system resilience and alerting.

8. **Load Testing:**  
   Integrate a load testing tool (e.g., Locust, k6) and monitor how the system behaves under stress.

9. **Service Mesh:**  
   Add a service mesh like Istio or Linkerd for traffic management, observability, and security between services.

10. **Multi-environment Support:**  
    Add staging and production environments with different configurations and monitoring setups.

These enhancements will give you hands-on experience with advanced observability, reliability, and operational practices.


### Example Service Roles

Yes, you can use PostgreSQL, Redis, and RabbitMQ together in your system. Here’s how each component fits:

- **PostgreSQL**:  
  Central database for persistent storage. All services can read/write structured data here.

- **Redis**:  
  In-memory cache for fast access to frequently used data. Services use it to cache queries, session data, or temporary results.

- **RabbitMQ**:  
  Message broker for event-driven communication. Services publish and consume messages for async processing, decoupling, and scalability.

### Example Service Roles

- service_a:  
  - Handles API requests.
  - Reads/writes to PostgreSQL.
  - Caches results in Redis.
  - Publishes events to RabbitMQ.

- service_b:  
  - Background jobs or analytics.
  - Reads from PostgreSQL.
  - Consumes events from RabbitMQ.

- `service_c`:  
  - Notification or reporting service.
  - Consumes events from RabbitMQ.
  - Updates Redis cache or PostgreSQL.

- `service_d`:  
  - Any additional service (e.g., user management, billing).
  - Can interact with any of the above components.

This setup is common in modern microservice architectures and supports high performance, scalability, and flexibility. Would you like a sample docker-compose.yml or service interaction diagram for this architecture?

## Draft 

- PostgreSQL 
- MongoDB
- Redis
- RabbitMQ 
- 
- Rate limiting  
- API Gateway 
- Service Discovery 
- Service mesh
-
- Obsirvability 
- 
1. Video Processing Platform
2. Learning Platform for videos and articles 
3. 


i like to build something that would be related to a learning platform 
I need it for studying tech and new language like german or even programming language 
which we can save videos and articles 
saving code snippets 
saving new learning words 
not sure how to make all that together 

## 🎓 App Idea: “LearnTrackr” – A Personal Learning Hub
✅ Key Features
1. Learning Resource Manager
    - Save links to articles, videos, books
    - Tag them by topic (e.g., Python, Databases, German)
2. Vocabulary Builder
    - Save new words/phrases
    - Group by language and topic
    - Add translations, usage examples, audio
3. Code Snippet Vault
    - Save code snippets with language tags and notes
    - Syntax-highlighted viewer
4. Study Tracker
    - Track progress on resources
    - Daily study reminders
    - Smart suggestions based on unfinished topics
5. Note-Taking & Flashcards
    - Markdown notes (linked to resources)
    - Turn notes into flashcards (e.g., for Anki or internal quizzing)


## 🎥🧠 App Idea: “VisionVault” – Intelligent Video/Image Archiver
🔑 Key Features
1. Upload Video/Image
2. Generate Thumbnails from Videos
3. Extract Faces from Frames
4. Detect and Group Same Person
5. Search by Face (upload a face → find matching videos/images)
6. Organize by Tags, Date, People



## ⚙️ System Design Overview
You can simulate a basic e-commerce-like system with the following services:

1. User Service (Flask + PostgreSQL)
    - Overview: 
      - Handle user registration, login, and user info retrieval.    
    - Responsibilities: 
        - Register new user (store username, email, hashed password, )
    - API Endpoints: 
        - `POST /register` – Register new user    
        - `POST /login`    – Authenticate user, return token  
        - `GET /user/<id>` – Get user info
2. Product Service (Flask + MongoDB)
    - Overview: 
      - Manages product catalog (CRUD operations).
      - Stores product data in MongoDB for flexible schema (e.g., name, description, price, tags).
    - Responsibilities: 
      - List all products
      - Add new product 
      - Get product by id
      - Update product 
      - Delete product      
    - API Endpoints: 
      - `POST /products`        – Add new product  
      - `GET /products`         – List all products  
      - `GET /products/<id>`    – Get product details  
      - `PUT /products/<id>`    – Update product  
      - `DELETE /products/<id>` – Delete product
3. Order Service (Flask + PostgreSQL + RabbitMQ)
    - Places orders
    - Publishes order events to RabbitMQ
4. Inventory Service (Flask + Redis + RabbitMQ)
    - Subscribes to order events
    - Updates inventory in Redis (simulate fast read/write)
5. Notification Service (Flask + RabbitMQ)
    - Subscribes to order/user events
    - Sends simulated email/SMS notifications (e.g., logs)


## 🔍 Observability Stack
Here’s what you can integrate for observability:

🧪 Metrics (Prometheus + Grafana)
    - Use prometheus_flask_exporter to expose Flask metrics
    - Monitor response times, error rates, etc.
    - Grafana dashboards for visualization
📊 Logs (ELK Stack or Loki)
    - Use Fluentd or Logstash to ship logs from containers
    - Store in Elasticsearch or Loki
    - Visualize in Kibana or Grafana
🔍 Tracing (OpenTelemetry + Jaeger)
    - Add OpenTelemetry SDK to each Flask app
    - Export traces to Jaeger to trace requests across services


pip install --upgrade argcomplete
docker rm -f loki
docker rm -f service_a
docker rm -f service_b
docker rm -f promtail
docker rm -f prometheus
docker rm -f grafana
sudo systemctl stop postgresql


### To change the indentation (indent level) of the file explorer tree in Visual Studio Code
- Press Ctrl + Shift + P and type Preferences: Open Settings (JSON).
- Add or edit the "workbench.tree.indent" line.
- Save the file. The explorer indentation will update immediately.

```
"workbench.tree.indent": 12

{
    "workbench.sideBar.location": "right",
    "[python]": {
        "editor.formatOnType": true
    },
    "workbench.colorTheme": "Default Dark+",
    "workbench.tree.indent": 22
}

```
### Extentions: 
- GitHub Copilot Chat
- 

https://vscodethemes.com/



http://localhost:5000/register
{
    "username":"username_1" ,
    "email":"email_1" ,
    "password":"password_1" 
}

http://localhost:5001/products
{        
  "name": "name_1",
  "description": "description_1",
  "price": 10
}


[2025-07-22 18:22:56,736] DEBUG in __init__: Metrics are disabled when run in the Flask development server with reload enabled. Set the environment variable DEBUG_METRICS=1 to enable them anyway.


docker exec -it mongo mongosh -u root -p example --authenticationDatabase admin

docker volume ls
docker volume rm yourvolume_name


