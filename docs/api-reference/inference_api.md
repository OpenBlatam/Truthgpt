# Inference Engine API Reference

The `InferenceEngine` class (`inference/core/engine.py`) provides the core interface for high-throughput serving, continuous batch scheduling, and token streaming.

---

## 🏛️ `InferenceEngine` Class

```python
class InferenceEngine:
    def __init__(self, config: EngineConfig) -> None: ...
    async def initialize(self) -> None: ...
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: Optional[List[str]] = None
    ) -> GenerationResult: ...

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> AsyncGenerator[TokenChunk, None]: ...
```

---

## 📄 `EngineConfig` Schema

```python
@dataclass
class EngineConfig:
    model_name: str
    max_batch_size: int = 32
    max_sequence_length: int = 4096
    gpu_memory_utilization: float = 0.90
    enable_paged_kv_cache: bool = True
    kv_cache_block_size: int = 16
    quantization: Optional[str] = None   # "fp8", "int8", "awq", "gptq"
    speculative_draft_model: Optional[str] = None
    num_speculative_tokens: int = 5
    device: str = "cuda"
```

---

## 📦 Output Schemas

### `GenerationResult`
- `text: str` — Complete generated text sequence.
- `prompt_tokens: int` — Number of input prompt tokens.
- `completion_tokens: int` — Number of generated tokens.
- `finish_reason: str` — Stop reason (`"stop"`, `"length"`).
- `latency_ms: float` — Total execution duration in milliseconds.

### `TokenChunk`
- `delta: str` — Single token text increment.
- `token_id: int` — Token ID integer.
- `logprob: Optional[float]` — Log probability of sampled token.
- `is_final: bool` — Boolean flag indicating sequence termination.
