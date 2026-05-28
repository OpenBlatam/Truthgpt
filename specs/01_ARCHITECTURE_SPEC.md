# 🏗️ Architecture Specification - Optimization Core

## 📋 Executive Summary

The `optimization_core` system is a high-performance framework designed for Large Language Model (LLM) inference orchestration and out-of-core data processing. By employing a hybrid polyglot architecture, it bridges the user-friendly prototyping environments of Python with the memory-safe, ultra-low-latency execution environments of compiled backends (Rust, C++, Go). 

---

## 🎯 System Objectives

### Primary Objectives
1. **High Throughput**: Achieve a 5x to 10x throughput enhancement compared to standard, naive PyTorch inference loops.
2. **Memory Efficiency**: Reduce peak memory utilization by 3x to 5x through dynamic cache pruning, page-aligned allocations, and Lazy query evaluation.
3. **Decoupled Orchestration**: Maintain a strict separation between front-end orchestration layers (Python API/CLI) and native execution kernels.
4. **Resilience**: Enforce graceful degradation protocols, maintaining system availability via fallback paths.

### Non-Functional Requirements (NFRs)

*   **Target Latency**: 
    $$L_{token} < 50 \text{ ms}$$
    where $L_{token}$ represents the time-to-first-token (TTFT) and the inter-token latency during inference for models up to 7B parameters under normal load.
*   **Target Throughput**: 
    $$T \ge 1000 \text{ tokens/sec/GPU}$$
*   **Memory Overhead**: 
    $$M_{overhead} < 4\text{GB}$$
    for a 7B parameter model in FP16 precision, excluding weight memory, using PagedAttention optimization.
*   **System Availability**: $99.9\%$ uptime under continuous load.
*   **Scalability**: Supports both vertical scaling (tensor parallelism) and horizontal scaling (distributed inference blocks).

---

## 🏛️ Macro Topology & Layers

### System Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│         (Python Training Loops, Orchestrators, CLI)         │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    Polyglot Core Layer                      │
│        (Unified Python API + Auto-Discovery Routing)        │
└────────────────────────────┬────────────────────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────▼──────┐    ┌─────────▼─────────┐   ┌──────▼──────┐
│  Rust Core  │    │    C++ Core       │   │  Go Core    │
│  (PyO3 FFI) │    │  (PyBind11 FFI)   │   │ (gRPC/HTTP) │
├──────────────┤    ├───────────────────┤   ├─────────────┤
│ • KV Cache   │    │ • FlashAttention  │   │ • HTTP API  │
│ • Compression│    │ • CUDA Kernels    │   │ • gRPC Host │
│ • Tokenizer  │    │ • Memory Alloc    │   │ • Messaging │
│ • JSONL Load │    │ • Vector SIMD     │   │ • Dist Sync │
└──────────────┘    └───────────────────┘   └─────────────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                       Hardware Layer                        │
│             (VRAM, RAM, PCIe bus, InfiniBand)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Core Subsystems

### 1. Abstract Core Subsystem (`core/`)
- **Purpose**: Defines system interfaces, base lifecycle components, and validation rules.
- **Key Modules**:
  - `interfaces.py` - Core contracts (`IComponent`, `IInferenceEngine`, `IDataProcessor`).
  - `base_classes.py` - Standard initializers and thread pool dispatchers.
  - `factories.py` - Factory registries for dynamic class resolution.
  - `exceptions.py` - Structured exception hierarchies (`ComponentLifecycleError`, `MemoryConstraintError`).
  - `config.py` - Configuration structures powered by Pydantic.

### 2. Inference Subsystem (`inference/`)
- **Purpose**: High-throughput inference engine wrappers.
- **Key Modules**:
  - `base_engine.py` - Common logic for model loading and token stream processing.
  - `vllm_engine.py` - Async integration with the vLLM execution backend (PagedAttention).
  - `tensorrt_llm_engine.py` - TensorRT-LLM integration for NVIDIA GPU optimization.
  - `engine_factory.py` - Factory resolver for engine execution backends.

### 3. Data Processing Subsystem (`data/`)
- **Purpose**: Out-of-core, vectorized data transformation pipelines.
- **Key Modules**:
  - `polars_processor.py` - High-speed, multi-threaded dataframe processing using Polars.
  - `processor_factory.py` - Dynamic engine instantiation.

### 4. Polyglot Subsystem (`polyglot_core/`)
- **Purpose**: FFI boundary management and memory sharing.
- **Key Modules**:
  - `backend.py` - Probes compilation environments to identify active backends.
  - `cache.py` - Unified interface routing KV cache queries to the optimal backend (Rust vs Python).
  - `compression.py` - Vectorized compression (LZ4/Zstd) using shared memory buffers.

### 5. Utility Subsystem (`utils/`)
- **Purpose**: Shared cross-cutting concerns.
- **Key Modules**:
  - `validation/` - Strictly typed schema validators.
  - `error_handling/` - Exception boundaries.
  - `logging/` - Structured, async-safe logging.
  - `metrics/` - Prometheus gauge/counter metrics.
  - `event_system/` - Asynchronous publish-subscribe event loop.

---

## 🔄 Core Pipeline Execution Flows

### Asynchronous Text Generation Flow
```
[User Request] ──> [Unified Engine API]
                          │
            [Determine Backend Capability]
            (vLLM Async > TensorRT > PyTorch Fallback)
                          │
            [Load Model Weights into GPU]
                          │
          [Continuous Batching Thread Loop] <─── [Incoming Stream]
                          │
       [Async Generator Yields Tokens to Client]
```

### Out-of-Core Data Transformation Flow
```
[Disk Path] ──> [Lazy Frame Scan]
                       │
          [Define Computation Graph] (Filters, Projections, Joins)
                       │
          [Optimize Query Graph] (Filter Pushdown, Projection Pruning)
                       │
          [Stream Compute Nodes] (Out-of-Core execution execution)
                       │
          [Sink Output directly to Disk]
```

### Polyglot Backend Resolution & Fallback Flow
```
[Instantiate Facade] ──> [Probe FFI Modules]
                                │
                    Is Rust (PyO3) Installed?
                    ├── Yes ──> Instantiate `rust_core` bindings
                    └── No  ──> Is C++ (pybind11) Installed?
                                ├── Yes ──> Instantiate `cpp_core` bindings
                                └── No  ──> Fallback to Pure Python
```

---

## 🔌 API Definitions

### IComponent
```python
class IComponent(ABC):
    """Abstract lifecycle interface for all core subsystems."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the registry identifier for the component."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Returns the semantic version of the component."""
        pass

    @abstractmethod
    def initialize(self, **kwargs: Any) -> 'IComponent':
        """Executes synchronous resource allocation.
        
        Args:
            **kwargs: System configuration options.
            
        Returns:
            The initialized component instance.
            
        Raises:
            ComponentLifecycleError: If initialization conditions fail.
        """
        pass

    @abstractmethod
    async def ainitialize(self, **kwargs: Any) -> 'IComponent':
        """Executes asynchronous resource allocation.
        
        Args:
            **kwargs: System configuration options.
            
        Returns:
            The initialized component instance.
            
        Raises:
            ComponentLifecycleError: If async initialization fails.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Synchronously releases allocated resources (handles, memory, sockets)."""
        pass

    @abstractmethod
    async def acleanup(self) -> None:
        """Asynchronously releases allocated resources."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Retrieves non-blocking diagnostic and observability metrics.
        
        Returns:
            A dictionary containing health indicators, active errors, and performance metrics.
        """
        pass
```

### IInferenceEngine
```python
class IInferenceEngine(IComponent):
    """Abstract interface for large language model inference engines."""

    @abstractmethod
    async def agenerate(
        self,
        prompts: Union[str, List[str]],
        config: Optional['GenerationConfig'] = None,
        **kwargs: Any
    ) -> Union[str, List[str]]:
        """Asynchronously generates text completions.

        Args:
            prompts: A single string prompt or a list of prompts.
            config: Configuration defining temperature, top_p, etc.
            **kwargs: Dynamic generation flags.

        Returns:
            Generated text string or list of text strings.

        Raises:
            NotInitializedError: If the model has not been loaded.
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        config: Optional['GenerationConfig'] = None,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Asynchronously streams generated tokens.

        Args:
            prompt: Input text prompt.
            config: Generation configuration parameters.
            **kwargs: Dynamic generation parameters.

        Yields:
            Text tokens sequentially.
        """
        pass

    @abstractmethod
    def load_model(self, model: Union[str, Path], **kwargs: Any) -> bool:
        """Loads model weights into memory.

        Args:
            model: Filepath or model hub identifier.
            **kwargs: Backend configuration (device, dtype, precision).

        Returns:
            True if loading is successful, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def is_model_loaded(self) -> bool:
        """Indicates if the model has been loaded into memory."""
        pass
```

---

## 📈 System Scalability Matrix

### Horizontal vs Vertical Scaling
*   **Vertical Scaling**: Handled at the GPU layer using Tensor Parallelism (splitting weight matrices across multiple GPUs on the same motherboard via NVLink).
*   **Horizontal Scaling**: Orchestrated using the Go Core subsystem, distributing requests across stateless worker instances communicating over gRPC.

### Memory Optimization via KV Caching
To avoid redundant processing of prompts in long-running conversations, the KV (Key-Value) cache of previous attention heads is persisted. The allocation size of the cache is dynamically governed by the formula:

$$Size_{KV} = 2 \times N_{layers} \times N_{heads} \times D_{head} \times L_{seq} \times N_{batch} \text{ bytes}$$

Where:
*   $N_{layers}$: Number of attention layers.
*   $N_{heads}$: Number of attention heads.
*   $D_{head}$: Head dimension.
*   $L_{seq}$: Maximum sequence length.
*   $N_{batch}$: Current batch size.

---

## 🧪 Testing Strategy

The validation pipeline enforces three distinct levels of verification:
1.  **Unit Isolation**: Using standard mocking and stubbing to test individual components without loading heavy deep learning libraries.
2.  **Integration Verification**: Cross-compilation testing to verify FFI memory sharing safety and ensure fallback loops degrade gracefully.
3.  **Performance Verification**: Automatic benchmarks tracking throughput and latency against established targets using Locust load testing and pytest-benchmark.

---

**Specification Version**: 1.1.0  
**Last Updated**: March 2026  
**Architectural Scope**: System-wide Topology
