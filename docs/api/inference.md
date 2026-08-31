# 🚀 Inference Engine API Reference

The `inference` subsystem provides high-throughput, low-latency LLM serving powered by Paged KV-Cache memory allocation, continuous batching schedulers, TensorRT-LLM / vLLM engine bridges, and speculative decoding verification.

---

## 🏛️ Inference Subsystem Architecture

```
inference/
├── api/                       # REST (FastAPI) and streaming handlers
├── core/                      # Engine implementations, Paged KV-Cache & engine factories
├── engines/                   # Specialized execution engines (TensorRT, vLLM, Fallback)
├── batch/                     # Continuous batching schedulers & priority queues
├── middleware/                # Cache managers & request interceptors
├── schemas/                   # Strongly-typed Pydantic schemas & engine configs
├── monitoring/                # Prometheus metrics & latency profilers
└── server.py                  # High-performance multi-worker server entrypoint
```

---

## 🚀 `create_inference_engine` & `InferenceEngine`

**Location**: `inference` & `inference.core.engine_factory`

```python
from inference import (
    create_inference_engine,
    EngineType,
    InferenceEngine,
    AsyncInferenceEngine,
    warmup_engines
)

# 1. Warm up inference engines in the background
warmup_engines(model_path="meta-llama/Llama-3-8B-Instruct", prefer_gpu=True)

# 2. Instantiate engine via unified factory
engine = create_inference_engine(
    model="meta-llama/Llama-3-8B-Instruct",
    engine_type=EngineType.AUTO_FALLBACK,
    prefer_gpu=True
)

# 3. Generate text completion (Synchronous)
result = engine.generate(
    prompt="Explain the difference between PagedAttention and FlashAttention.",
    max_new_tokens=256
)
print(result)
```

---

## 🌊 Async Streaming API

For interactive chat applications and real-time generation:

```python
import asyncio
from inference import AsyncInferenceEngine, create_inference_engine, EngineType

async def stream_tokens():
    engine = create_inference_engine(
        model="meta-llama/Llama-3-8B-Instruct",
        engine_type=EngineType.AUTO_FALLBACK
    )
    
    # Generate token stream
    response = engine.generate(
        prompt="Write a Python script for asynchronous queue processing:",
        max_new_tokens=128
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(stream_tokens())
```

---

## 🧠 Paged KV-Cache & Memory Management

**Location**: `inference.middleware.cache_manager` & `inference.core`

Eliminates memory fragmentation by allocating Key and Value tensors in fixed-size blocks (pages):

| Feature | Standard KV-Cache | Paged KV-Cache |
| :--- | :--- | :--- |
| **Memory Allocation** | Contiguous static allocation per sequence | Dynamic non-contiguous virtual pages |
| **Memory Waste** | 60%–80% (internal + external fragmentation) | < 4% (only within the last block of a sequence) |
| **Max Concurrency** | 16–32 concurrent streams | 128–256 concurrent streams |
| **Sharing (Prefix Caching)**| Impossible without duplication | Zero-copy block sharing across common system prompts |

```python
from inference.middleware.cache_manager import CacheManager

cache_mgr = CacheManager(max_cache_size_mb=4096)
```

---

## ⚙️ Engine Configurations & Schemas

**Location**: `inference.schemas.engine_configs`

```python
from inference.schemas.engine_configs import EngineConfig

config = EngineConfig(
    model_name="meta-llama/Llama-3-8B-Instruct",
    max_batch_size=64,
    max_sequence_length=4096,
    tensor_parallel_size=1,
    gpu_memory_utilization=0.90
)
```

---

## 📡 REST API & Production Server

Launch the inference service via CLI:

```bash
# Start the FastAPI inference server
python -m inference.server --port 8000 --host 0.0.0.0
```

### Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/v1/models` | GET | List loaded inference models and backends |
| `/v1/completions` | POST | High-throughput text completion endpoint |
| `/v1/chat/completions`| POST | OpenAI-compatible chat completion endpoint |
| `/metrics` | GET | Prometheus telemetry metrics |
