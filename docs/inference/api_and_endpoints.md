# Production Inference Server APIs & Endpoints

TruthGPT exposes enterprise-grade REST and gRPC endpoints (`inference/api/` and `inference/server.py`), compatible with OpenAI API schemas and production telemetry.

---

## 🚀 Launching the Production Server

```bash
# Launch server on port 8080 with 4 worker processes
python cli.py serve --host 0.0.0.0 --port 8080 --workers 4
```

---

## 📡 REST API Specification

### 1. Chat Completions (OpenAI Compatible)
**Endpoint**: `POST /v1/chat/completions`

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "truthgpt-default",
    "messages": [
      {"role": "system", "content": "You are TruthGPT, an expert optimization AI."},
      {"role": "user", "content": "How do I optimize Flash Attention on Hopper?"}
    ],
    "temperature": 0.7,
    "max_tokens": 256,
    "stream": false
  }'
```

#### JSON Response:
```json
{
  "id": "chatcmpl-9482f3a",
  "object": "chat.completion",
  "created": 1724673820,
  "model": "truthgpt-default",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "To optimize Flash Attention on NVIDIA Hopper (H100/H200), leverage Flash Attention 3 which utilizes asynchronous WGMMA instructions..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 28,
    "completion_tokens": 42,
    "total_tokens": 70
  }
}
```

---

### 2. Streaming Completions (Server-Sent Events)
**Endpoint**: `POST /v1/chat/completions` (with `"stream": true`)

Returns an `application/x-ndjson` or `text/event-stream` stream:
```text
data: {"id":"chatcmpl-9482","choices":[{"delta":{"content":"To"}}]}
data: {"id":"chatcmpl-9482","choices":[{"delta":{"content":" optimize"}}]}
data: {"id":"chatcmpl-9482","choices":[{"delta":{"content":" Flash"}}]}
data: [DONE]
```

---

### 3. Swarm Semantic Routing
**Endpoint**: `POST /v1/swarm/ask`

```json
{
  "user_id": "analyst_1",
  "prompt": "Evaluate the SEO conversion rates for our product.",
  "return_traces": true
}
```

---

### 4. Health & Prometheus Metrics
- **`GET /healthz`**: Returns `{"status": "healthy", "gpu_status": "ready"}`
- **`GET /metrics`**: Prometheus metrics endpoint tracking:
  - `truthgpt_inference_requests_total`
  - `truthgpt_inference_latency_seconds_bucket`
  - `truthgpt_tokens_generated_total`
  - `truthgpt_gpu_memory_utilization_ratio`
  - `truthgpt_kv_cache_allocated_blocks`
