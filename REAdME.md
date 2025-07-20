

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