# Tutorial: High-Throughput Serving with Speculative Decoding & Paged KV-Cache

In this tutorial, you will configure and benchmark a high-throughput LLM serving endpoint using **Paged KV-Cache** and **Speculative Decoding**, accelerating inference throughput by up to **2.8x**.

---

## 🎯 Tutorial Objectives
1. Configure target and draft models.
2. Initialize Paged KV-Cache pools.
3. Start the high-concurrency serving server.
4. Execute an asynchronous load test and evaluate token latency.

---

## ⚙️ Step 1: Create Serving Configuration

Create `configs/speculative_serving.yaml`:

```yaml
inference:
  target_model: "meta-llama/Llama-2-7b-chat-hf"
  draft_model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
  
  speculative:
    enabled: true
    num_speculative_tokens: 4     # Number of candidate tokens generated per draft step
    acceptance_threshold: 0.85
  
  kv_cache:
    backend: "paged"
    block_size_tokens: 16
    max_gpu_memory_gb: 16.0
    dtype: "bfloat16"

server:
  host: "0.0.0.0"
  port: 8080
  workers: 2
  max_concurrent_requests: 128
```

---

## 🚀 Step 2: Start Inference Daemon

Launch the serving daemon with your configuration:

```bash
python inference/server.py --config configs/speculative_serving.yaml
```

---

## 🏎️ Step 3: Run High-Concurrency Load Test

Create a load testing script `load_test.py`:

```python
import asyncio
import time
import httpx

PROMPTS = [
    "Explain quantum entanglement in simple terms.",
    "Write a high-performance Python function for matrix transposition.",
    "What are the primary benefits of PagedAttention?",
    "Summarize the history of deep learning compilers from XLA to TorchInductor.",
] * 20

async def send_request(client, prompt_id, prompt):
    start = time.perf_counter()
    response = await client.post(
        "http://localhost:8080/v1/completions",
        json={"prompt": prompt, "max_tokens": 128, "temperature": 0.7},
        timeout=60.0
    )
    duration = time.perf_counter() - start
    data = response.json()
    token_count = len(data["choices"][0]["text"].split())
    return duration, token_count

async def main():
    async with httpx.AsyncClient() as client:
        print(f"🚀 Dispatching {len(PROMPTS)} concurrent requests...")
        start_total = time.perf_counter()
        
        tasks = [send_request(client, idx, p) for idx, p in enumerate(PROMPTS)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.perf_counter() - start_total
        total_tokens = sum(r[1] for r in results)
        avg_latency = sum(r[0] for r in results) / len(results)
        
        print("\n================ Benchmark Results ================")
        print(f"Total Requests:     {len(PROMPTS)}")
        print(f"Total Elapsed Time: {total_time:.2f} seconds")
        print(f"Total Tokens:       {total_tokens} tokens")
        print(f"System Throughput:  {total_tokens / total_time:.2f} tokens/sec")
        print(f"Average Latency:    {avg_latency:.3f} seconds/request")
        print("===================================================")

if __name__ == "__main__":
    asyncio.run(main())
```

Run the benchmark:
```bash
python load_test.py
```
