# 🚀 Production Deployment & Serving Guide

This guide covers deploying TruthGPT Optimization Core for high-availability production training clusters and low-latency inference serving with Docker, Kubernetes, and Prometheus monitoring.

---

## 🏛️ Production Architecture Overview

```mermaid
graph LR
    Client[Client Apps / SDKs] --> LB[Load Balancer / Ingress]
    LB --> APIServer[FastAPI Microservice Cluster]
    APIServer --> Ray[Ray / Slurm Orchestrator]
    Ray --> Worker1[GPU Node 1 (TensorRT / Inductor)]
    Ray --> Worker2[GPU Node 2 (TensorRT / Inductor)]
    APIServer --> Prom[Prometheus & Grafana Telemetry]
```

---

## 🌐 1. Launching the Production REST API

Start the high-throughput API gateway with Uvicorn worker clustering:

```bash
python cli.py serve \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 4 \
    --log-level info
```

### Environment Configuration (`.env`):
```ini
TRUTHGPT_ENV=production
TRUTHGPT_DEVICE=cuda
TRUTHGPT_MAX_BATCH_SIZE=64
TRUTHGPT_DEFAULT_MODEL=compiled_models/transformer_fp16.engine
TRUTHGPT_ENABLE_PROMETHEUS=true
```

---

## 🐳 2. Production Dockerfile

```dockerfile
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip git build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements_advanced.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements_advanced.txt

COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8080 9090
CMD ["python3", "cli.py", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

### Building & Running with GPU Passthrough:
```bash
# Build image
docker build -t truthgpt-core:latest .

# Run with full GPU allocation and shared memory support
docker run --gpus all \
    -p 8080:8080 \
    -v /data/models:/models \
    -v /data/runs:/runs \
    --ipc=host \
    truthgpt-core:latest \
    python -m inference.server --model /models/llama-2-7b --port 8080
```

---

## ☸️ 3. Kubernetes Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: truthgpt-inference
  namespace: ml-production
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
        image: truthgpt-core:latest
        command: ["python", "-m", "inference.server", "--port", "8080"]
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
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 15
```

---

## 📊 4. Prometheus & Grafana Monitoring

TruthGPT exports real-time system metrics at `/v1/metrics`:

| Metric Name | Type | Description |
| :--- | :--- | :--- |
| `truthgpt_requests_total` | Counter | Total API requests processed |
| `truthgpt_inference_latency_seconds` | Histogram | Request end-to-end execution latency |
| `truthgpt_tokens_per_second` | Gauge | Active generation / training throughput |
| `truthgpt_gpu_memory_used_bytes` | Gauge | Instantaneous GPU VRAM allocation |
| `truthgpt_kv_cache_usage_ratio` | Gauge | Paged KV-Cache allocation fraction |
