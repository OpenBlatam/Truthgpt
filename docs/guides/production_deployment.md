# Enterprise Production Deployment Guide

Deploying TruthGPT Optimization Core in enterprise production environments requires high reliability, automated health checks, Prometheus telemetry, and robust container orchestration.

---

## 🐳 1. Production Docker Container

```dockerfile
# Multi-stage production build
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 as base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip python3.10-venv libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_advanced.txt .
RUN pip install --no-cache-dir -r requirements_advanced.txt

COPY . .
RUN pip install -e .

EXPOSE 8080 9090
CMD ["python", "inference/server.py", "--port", "8080", "--workers", "4"]
```

---

## ☸️ 2. Kubernetes Deployment (NVIDIA GPU Operator)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: truthgpt-inference-service
  labels:
    app: truthgpt-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: truthgpt-inference
  template:
    metadata:
      labels:
        app: truthgpt-inference
    spec:
      containers:
      - name: truthgpt
        image: truthgpt-optimization-core:latest
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "32Gi"
            cpu: "8"
          requests:
            nvidia.com/gpu: 1
            memory: "16Gi"
            cpu: "4"
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 15
```

---

## 📊 3. Prometheus & Grafana Monitoring

TruthGPT exposes Prometheus-formatted metrics at `/metrics`:

- `truthgpt_token_throughput_per_sec`: Total generated tokens per second.
- `truthgpt_time_to_first_token_ms`: TTFT latency distribution.
- `truthgpt_kv_cache_usage_ratio`: Fraction of allocated Paged KV-Cache blocks currently in use.
- `truthgpt_gpu_memory_used_bytes`: Real-time VRAM allocation.

### Prometheus Job Scrape Config:
```yaml
scrape_configs:
  - job_name: 'truthgpt-inference'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['truthgpt-service:8080']
```

---

## 🛡️ 4. Circuit Breakers & Graceful Shutdown

The inference server includes automatic circuit breakers to protect against GPU out-of-memory cascading failures:

- If GPU memory exceeds 95%, new non-streaming incoming requests receive HTTP `429 Too Many Requests` or are placed in an async queue.
- On `SIGTERM` / `SIGINT`, the server stops accepting new connections, drains active token generation streams (timeout: 30s), and flushes cache buffers safely.
