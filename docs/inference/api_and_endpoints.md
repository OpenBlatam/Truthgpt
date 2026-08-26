# Inference APIs & REST Endpoints

TruthGPT provides an enterprise-ready FastAPI HTTP and WebSocket serving layer compatible with the OpenAI API standard, alongside dedicated endpoints for telemetry, health auditing, and autonomous swarm routing.

---

## 🌐 Endpoints Overview Matrix

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/v1/chat/completions` | `POST` | OpenAI-compatible chat completions with Server-Sent Events (SSE) streaming support. |
| `/v1/completions` | `POST` | Raw text generation and token completions. |
| `/v1/models` | `GET` | List loaded models, context limits, and active quantization formats. |
| `/v1/swarm/ask` | `POST` | Semantic Swarm router entrypoint (`{"prompt": "...", "user_id": "..."}`). |
| `/v1/health` | `GET` | Service liveness, GPU VRAM allocation, and temperature diagnostics. |
| `/v1/metrics` | `GET` | Prometheus-formatted metrics (throughput, token latency, cache hit rate). |

---

## 📡 1. OpenAI-Compatible Chat Completions

### Request Payload (`POST /v1/chat/completions`)

```json
{
  "model": "truthgpt-transformer-sota",
  "messages": [
    {"role": "system", "content": "You are TruthGPT, an expert AI assistant."},
    {"role": "user", "content": "How does Paged KV-Cache prevent memory fragmentation?"}
  ],
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 512,
  "stream": true
}
```

### cURL Example

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "truthgpt-transformer-sota",
    "messages": [{"role": "user", "content": "Explain SOAP optimizer"}],
    "stream": false
  }'
```

---

## 🐝 2. OpenClaw Swarm Endpoint (`POST /v1/swarm/ask`)

```bash
curl -X POST http://localhost:8080/v1/swarm/ask \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Evaluate gradient descent stability under FP8 quantization",
    "user_id": "researcher_01",
    "max_depth": 4
  }'
```

Response:
```json
{
  "agent_name": "OptimizationSpecialistAgent",
  "action_type": "final_answer",
  "content": "FP8 quantization maintains gradient stability when coupled with dynamic scale factor tracking...",
  "execution_time_ms": 342.1
}
```
