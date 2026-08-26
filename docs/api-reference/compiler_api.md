# Compiler Subsystem API Reference

The `TruthGPTCompiler` class (`compiler/core/compiler.py`) provides the programmatic interface for JIT and AOT graph transformation and kernel compilation.

---

## 🏛️ `TruthGPTCompiler` Class

```python
class TruthGPTCompiler:
    def __init__(
        self,
        backend: str = "inductor",
        precision: str = "bf16",
        fuse_attention: bool = True,
        enable_cuda_graphs: bool = False,
        optimization_level: int = 3
    ) -> None: ...

    def compile(
        self,
        model: torch.nn.Module,
        sample_input_shape: Optional[Tuple[int, ...]] = None,
        dynamic_shapes: bool = True
    ) -> torch.nn.Module: ...

    def export_aot_library(
        self,
        model: torch.nn.Module,
        output_path: str,
        sample_inputs: Tuple[torch.Tensor, ...]
    ) -> str: ...
```

---

## ⚙️ Compiler Configuration Parameters

| Parameter | Type | Options | Description |
| :--- | :--- | :--- | :--- |
| `backend` | `str` | `"inductor"`, `"tensorrt"`, `"xla"`, `"aot"` | Target compilation backend engine. |
| `precision` | `str` | `"bf16"`, `"fp16"`, `"fp8"`, `"fp32"` | Target numerical execution precision. |
| `fuse_attention` | `bool` | `True` / `False` | Automatically replaces standard attention subgraphs with Flash Attention kernels. |
| `enable_cuda_graphs` | `bool` | `True` / `False` | Captures static execution graphs to eliminate CPU launch overhead. |
| `dynamic_shapes` | `bool` | `True` / `False` | Generates symbolic shape guards to prevent re-compilation on variable sequence lengths. |
