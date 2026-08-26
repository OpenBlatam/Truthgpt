# Inference Engine API Reference

The `inference` subsystem provides high-throughput, low-latency LLM serving powered by Paged KV-Cache memory allocation, continuous batching schedulers, and speculative decoding verification.

---

## 🏛️ Inference Subsystem Architecture

```
inference/
├── api/                       # REST (FastAPI) and gRPC serving handlers
├── core/                      # Paged KV-Cache allocator & memory pools
├── engines/                   # Execution engines (Standard, Speculative, TensorRT)
├── schedulers/                # Continuous batching & priority request queues
├── pipelines/                 # Token streaming & stopping criteria pipelines
└── server.py                  # High-performance multi-worker server entrypoint
```

---

## 🚀 `InferenceEngine`

**Location**: `inference.engines`

```python
from inference.engines import InferenceEngine
from inference.config import InferenceConfig

# 1. Initialize configuration
config = InferenceConfig(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    max_batch_size=64,
    block_size_tokens=16,          # Size of individual KV pages
    kv_cache_max_gpu_memory_gb=14.0,
    enable_speculative_decoding=False
)

# 2. Instantiate engine
engine = InferenceEngine(config=config)

# 3. Generate text completion (Synchronous)
result = engine.generate(
    prompt="Explain the difference between PagedAttention and FlashAttention.",
    max_new_tokens=256,
    temperature=0.7,
    top_p=0.9
)
print(result.text)
```

---

## 🌊 Async Streaming API

For interactive chat applications and real-time generation:

```python
import asyncio
from inference.engines import AsyncInferenceEngine

async def stream_tokens():
    engine = AsyncInferenceEngine(config=config)
    
    async for token_chunk in engine.generate_stream(
        prompt="Write a Python script for asynchronous queue processing:",
        max_new_tokens=128
    ):
        print(token_chunk.token_text, end="", flush=True)

asyncio.run(stream_tokens())
```

---

## 🧠 Paged KV-Cache Allocator

**Location**: `inference.core.paged_kv_cache`

Eliminates memory fragmentation by allocating Key and Value tensors in fixed-size blocks (pages):

| Feature | Standard KV-Cache | Paged KV-Cache |
| :--- | :--- | :--- |
| **Memory Allocation** | Contiguous static allocation per sequence | Dynamic non-contiguous virtual pages |
| **Memory Waste** | 60%–80% (internal + external fragmentation) | < 4% (only within the last block of a sequence) |
| **Max Concurrency** | 16–32 concurrent streams | 128–256 concurrent streams |
| **Sharing (Prefix Caching)**| Impossible without duplication | Zero-copy block sharing across common system prompts |

```python
from inference.core.paged_kv_cache import PagedKVCacheManager

cache_mgr = PagedKVCacheManager(
    num_blocks=2048,
    block_size=16,
    num_heads=32,
    head_dim=128,
    dtype=torch.bfloat16
)

# Allocate virtual block table for a new incoming sequence
block_table = cache_mgr.allocate_blocks(sequence_id="req_101", initial_length=64)
```

---

## ⚡ Speculative Decoding Engine

**Location**: `inference.engines.speculative`

Accelerates inference by combining a small, fast "Draft Model" (e.g., 125M params) and a large "Target Model" (e.g., 70B params).

```mermaid
sequenceDiagram
    participant Draft as Fast Draft Model (125M)
    participant Target as Large Target Model (70B)
    participant Cache as Paged KV-Cache

    Note over Draft: Step 1: Draft K Tokens Fast
    Draft->>Draft: Generate Token 1, 2, 3, 4
    Draft-->>Target: Send Candidate Tokens [T1, T2, T3, T4]
    
    Note over Target: Step 2: Parallel Verification
    Target->>Target: Single Forward Pass over [T1, T2, T3, T4]
    Target->>Target: Verify Probabilities (Accept T1, T2, T3; Reject T4)
    Target->>Cache: Commit Accepted Tokens to KV-Cache
    Target-->>Draft: Resynchronize KV State
```

- **Speedup**: Achieves 2x–3x lower latency per token with mathematical output equivalence (lossless).

---

## 🌐 Production Server Endpoints

Launch the multi-worker serving daemon:

```bash
python inference/server.py --port 8080 --workers 4
```

### Standard REST Endpoints

| Route | Method | Payload | Description |
| :--- | :--- | :--- | :--- |
| `/v1/chat/completions` | `POST` | `{"messages": [...], "temperature": 0.7, "stream": true}` | OpenAI-compatible chat completion. |
| `/v1/completions` | `POST` | `{"prompt": "...", "max_tokens": 100}` | Standard text completion. |
| `/health` | `GET` | *None* | Health status and GPU memory availability. |
| `/metrics` | `GET` | *None* | Prometheus telemetry (token throughput, KV memory usage). |
