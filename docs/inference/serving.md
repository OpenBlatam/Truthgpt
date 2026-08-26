# High-Throughput Inference Serving

The **TruthGPT Inference Serving Subsystem** (`inference/server.py`, `inference/engine.py`) provides an OpenAI-compatible REST and WebSocket serving layer with continuous iteration-level batching.

---

## ⚡ Key Serving Capabilities

1. **Continuous Batching**: Dynamically inserts incoming requests into running model forward passes without waiting for prior sequences to finish generation.
2. **Chunked Prefill**: Splits large prompt prefill computations into chunks (e.g. 512 tokens) to prevent stalling active generation tokens.
3. **OpenAI Compatibility**: Seamless drop-in replacement for standard client SDKs (`openai.OpenAI(base_url="http://localhost:8080/v1")`).

---

## 🚀 Starting the Production Server

```bash
# Start server with 4 worker processes and FP8 quantization
python -m inference.server \
    --model meta-llama/Llama-2-7b \
    --port 8080 \
    --dtype bfloat16 \
    --gpu-memory-utilization 0.92 \
    --max-batch-size 64
```

---

## 💻 Client Usage (Python OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="none"
)

response = client.chat.completions.create(
    model="meta-llama/Llama-2-7b",
    messages=[
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Explain FlashAttention in two sentences."}
    ],
    temperature=0.7,
    stream=True
)

for chunk in response:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
print()
```
