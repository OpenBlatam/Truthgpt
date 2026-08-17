# Unified Adapters Architecture (`optimization_core/adapters`)

The `adapters` package provides a standardized, Pydantic-first adapter infrastructure that bridges core components (models, datasets, optimizers, trainers) into autonomous tool registries (`BaseTool`) and execution pipelines.

## Key Design Principles

1. **Pydantic-First Data Contracts**: All adapter inputs and execution outputs return strongly typed Pydantic response models with full runtime validation and JSON serialization.
2. **Global ObjectStore**: Heavyweight PyTorch models, datasets, optimizers, and trainers are stored in a thread-safe in-memory `ObjectStore` singleton, passing lightweight string IDs (`model_id`, `data_id`, `optimizer_id`) across tool interactions.
3. **Structured Exception Hierarchy**: Operations raise specific exceptions (`AdapterError`, `ObjectNotFoundError`, `AdapterConfigurationError`, `AdapterExecutionError`) for predictable error handling.
4. **Dual Module Alias Registration**: Full support for both `import optimization_core.adapters` and `import adapters` via transparent `sys.modules` aliasing.

---

## Subsystems & Modules

- **`base.py`**: Base protocol (`BaseAdapterProtocol`), generic lifecycle abstract class (`BaseAdapter`), tool-compatible dynamic base (`BaseDynamicAdapter`), exception hierarchy, and thread-safe in-memory `ObjectStore`.
- **`data_adapter.py`**: Dataset loading, split management, HuggingFace Hub integration (`HuggingFaceDataAdapter`), and local JSONL file processing (`JSONLDataAdapter`).
- **`model_adapter.py`**: PyTorch and HuggingFace model I/O, parameter inspection, and state management (`ModelAdapter`, `HuggingFaceModelAdapter`).
- **`optimizer_adapter.py`**: PyTorch optimizer creation, parameter group management, CUDA fused kernel detection, and state queries (`OptimizerAdapter`, `PyTorchOptimizerAdapter`).
- **`training_adapter.py`**: Lifecycle management for model training loops (`TrainingAdapter`).
- **`truthgpt_adapters.py`**: Standard and legacy TruthGPT optimization wrappers (`TruthGPTAdapter`, `TruthGPTPerformanceAdapter`, etc.).
- **`enterprise_truthgpt_adapter.py`**: Enterprise-grade model creation, inference optimization, and hardware analytics (`EnterpriseTruthGPTAdapter`).
- **`__init__.py`**: Unified factory function (`create_adapter`), central registry (`ADAPTER_REGISTRY`), and inspection helper functions (`list_available_adapter_types`, `list_available_adapter_subtypes`, `get_adapter_info`).

---

## Usage Examples

### 1. Unified Factory & Inspection

```python
import optimization_core.adapters as adapters

# Inspect registered types and subtypes
types = adapters.list_available_adapter_types()
opt_subtypes = adapters.list_available_adapter_subtypes("optimizer")
info = adapters.get_adapter_info("optimizer", "pytorch")

# Instantiate adapters via factory
opt_adapter = adapters.create_adapter("optimizer", "pytorch")
jsonl_adapter = adapters.create_adapter("data", "jsonl")
```

### 2. Working with `ObjectStore` & Dynamic Adapters

```python
from optimization_core.adapters.base import ObjectStore

store = ObjectStore.instance()

# Storing PyTorch model
model_id = store.put(my_pytorch_model, kind="model", meta={"name": "my_model"})

# Executing adapter process via JSON string or dictionary
output = opt_adapter.process({
    "action": "create",
    "model_id": model_id,
    "optimizer_type": "adamw",
    "kwargs": {"lr": 1e-4}
})

print("Created optimizer_id:", output["optimizer_id"])
```
