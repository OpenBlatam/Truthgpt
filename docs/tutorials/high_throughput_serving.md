# Tutorial: High-Throughput Serving with Paged KV-Cache

This tutorial demonstrates launching a production-grade inference server with continuous batching and Paged KV-Cache.

---

## 🚀 1. Launching the Inference Server

```bash
python -m inference.server \
    --model meta-llama/Llama-2-7b \
    --port 8080 \
    --dtype bfloat16 \
    --gpu-memory-utilization 0.92 \
    --max-batch-size 64
```

---

## 💻 2. Asynchronous Client Benchmarking

Use Python's `asyncio` and `httpx` to simulate 50 concurrent users querying the server:

```python
import asyncio
import httpx
import time

URL = "http://localhost:8080/v1/chat/completions"

async def send_request(client, user_id):
    payload = {
        "model": "meta-llama/Llama-2-7b",
        "messages": [{"role": "user", "content": f"User {user_id}: Give 3 tips for efficient coding."}],
        "max_tokens": 100
    }
    start = time.time()
    response = await client.post(URL, json=payload, timeout=60.0)
    latency = time.time() - start
    return latency, response.status_code

async def main():
    async with httpx.AsyncClient() as client:
        tasks = [send_request(client, i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        latencies = [r[0] for r in results if r[1] == 200]
        print(f"50 Concurrent Requests Completed!")
        print(f"Average Latency: {sum(latencies)/len(latencies):.2f}s")
        print(f"P95 Latency: {sorted(latencies)[int(len(latencies)*0.95)]:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```
