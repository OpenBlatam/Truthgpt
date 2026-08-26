# Practical Guide: Production Deployment

This guide covers deploying TruthGPT training and inference services into production environments using Docker, Kubernetes, and Systemd.

---

## 🐳 Docker Deployment

### 1. Build the Production Container

```bash
docker build -t truthgpt-core:latest -f deployment/Dockerfile .
```

### 2. Run Inference Server Container with GPU Access

```bash
docker run --gpus all \
    -p 8080:8080 \
    -v /data/models:/models \
    -v /data/runs:/runs \
    --ipc=host \
    truthgpt-core:latest \
    python -m inference.server --model /models/llama-2-7b --port 8080
```

---

## ☸️ Kubernetes Deployment Spec (Helm / Manifest)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: truthgpt-inference
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
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
```
