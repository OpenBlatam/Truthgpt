# Health Checks & Environment Diagnostics

TruthGPT includes a comprehensive diagnostic suite to audit system readiness, verify CUDA driver compatibility, detect hardware bottlenecks, and ensure optimal training and inference efficiency.

---

## 🔍 Built-In Diagnostic Tools

### 1. Master Environment Health Check

Run the top-level audit tool before starting any compute workload:

```bash
python utils/health_check.py
```

#### Diagnostic Audit Checks
The health check systematically evaluates:
1. **Python Environment**: Version check, virtual environment isolation, critical package integrity.
2. **CUDA & GPU Subsystems**: Device count, CUDA runtime version, driver capability, NVLink status, VRAM availability.
3. **Hardware Accelerators**: FlashAttention-2 availability, Triton compiler readiness, bitsandbytes quantization libraries.
4. **Polyglot Engines**: Rust native dynamic libraries (`.so` / `.dll` / `.dylib`), C++20 binary interfaces, Go cluster binaries.
5. **Disk & I/O Performance**: Fast NVMe read/write benchmark for data streaming pipelines.

---

## 🧪 Latency & Throughput Benchmark

Measure raw tensor operations, attention throughput, and memory bandwidth across your GPU hardware:

```bash
# Run comprehensive latency benchmark
python latency_optimizations.py --benchmark-all
```

Sample output:
```text
======================================================================
 TRUTHGPT HARDWARE PERFORMANCE BENCHMARK
======================================================================
 [Attention] Standard Scaled Dot-Product:     4.82 ms (Baseline)
 [Attention] FlashAttention-2 Fused Kernel:   1.14 ms (4.23x Speedup)
 [Optimizer] PyTorch Standard AdamW:         2.41 ms / step
 [Optimizer] TruthGPT Fused SOAP:            0.98 ms / step (2.45x Speedup)
 [Compiler]  TorchInductor Graph Execution:  1.32x Throughput Boost
 [KV-Cache]  PagedAttention 4-Bit Int:       3.8x Memory Reduction
======================================================================
```

---

## 🛠️ Automated Diagnostic Verification Script

To run an automated self-test across all optimization layers, execute:

```bash
python smoke_test_phase6.py
```
This tests optimizer convergence, gradient stability, AMP precision scaling, and multi-threaded data loading in less than 30 seconds.
