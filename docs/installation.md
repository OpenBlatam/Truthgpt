# TruthGPT Optimization Core - Installation & Environment Setup

This comprehensive guide covers installation procedures for development workstations, GPU clusters, containerized deployments, and polyglot native acceleration environments.

---

## 📋 System Prerequisites

| Component | Minimum Specification | Recommended Specification |
| :--- | :--- | :--- |
| **Operating System** | Linux (Ubuntu 20.04+), Windows 11 (WSL2), macOS (M1/M2/M3) | Ubuntu 22.04 LTS or RHEL 9 |
| **Python** | Python 3.10 | Python 3.10 or 3.11 |
| **GPU Hardware** | NVIDIA GPU (8GB+ VRAM, Compute Capability 7.0+) | NVIDIA A100 / H100 / RTX 4090 (24GB+ VRAM) |
| **CUDA Driver** | CUDA 11.8 | CUDA 12.1 or 12.4 |
| **C++ Build Tools** | GCC 9.3+ / Clang 11+ / CMake 3.20+ | GCC 11+ / CMake 3.26+ |
| **Rust Toolchain** | Rust 1.70+ (`cargo`) | Latest Stable Rust (`rustup update`) |
| **Disk Storage** | 20 GB Free SSD Space | 100 GB+ NVMe SSD |

---

## 🚀 Quick Automated Installation

We provide automated setup scripts that detect your host OS, configure virtual environments, and install required dependencies.

### Linux / macOS
```bash
cd optimization_core
chmod +x setup_dev.sh
./setup_dev.sh
```

### Windows (PowerShell)
```powershell
cd optimization_core
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_dev.ps1
```

---

## 📦 Step-by-Step Manual Setup

### 1. Create and Activate Virtual Environment

```bash
# Using Python venv
python -m venv .venv

# Activate on Linux/macOS
source .venv/bin/activate

# Activate on Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Or using **Conda**:
```bash
conda create -n truthgpt-core python=3.10 -y
conda activate truthgpt-core
```

---

### 2. Install PyTorch with Hardware Acceleration

Select the exact build corresponding to your target hardware:

#### CUDA 12.1 (Recommended for Modern NVIDIA GPUs)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### CUDA 11.8 (Legacy Support)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Apple Silicon (macOS MPS) / CPU-Only
```bash
pip install torch torchvision torchaudio
```

---

### 3. Install Core Python Dependencies

```bash
pip install -r requirements_advanced.txt
pip install -e .
```

---

### 4. Install Optional Acceleration Extensions

Use our `install_extras.py` utility to selectively install optimized libraries:

```bash
# List all available extension groups
python install_extras.py --list

# Install FlashAttention-2 (Requires CUDA toolkit)
pip install flash-attn --no-build-isolation

# Install 8-bit & 4-bit quantization (bitsandbytes)
python install_extras.py bitsandbytes

# Install Observability & Tracking (W&B, TensorBoard, Prometheus)
python install_extras.py wandb

# Install all optional extensions
python install_extras.py all
```

---

## 🦀 Compiling Polyglot Native Backends

For ultra-low latency execution and custom memory allocators, compile the polyglot native extensions:

### 1. Rust Native Engine
```bash
cd rust_core
cargo build --release
cd ..
```

### 2. C++20 & CUDA Kernel Extensions
```bash
cd cpp_core
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j$(nproc)
cd ../..
```

### 3. Bazel Multi-Target Build (Enterprise)
```bash
# Build complete optimization core with Bazel
bazel build //...
```

---

## 🐳 Docker & Containerized Deployment

We provide production-ready Docker containers with multi-stage builds and CUDA acceleration.

### Build Production Image
```bash
docker build -t truthgpt-optimization-core:latest .
```

### Run with NVIDIA GPU Acceleration
```bash
docker run --gpus all \
  --ipc=host \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  -p 8080:8080 \
  -v $(pwd)/runs:/app/runs \
  truthgpt-optimization-core:latest
```

### Docker Compose Multi-Service Setup
```bash
docker-compose -f docker-compose.yml up -d
```
*This launches the TruthGPT Inference API, Prometheus metrics exporter, and Grafana dashboard.*

---

## 🔍 Verification & Health Diagnostics

Verify that your hardware, CUDA runtimes, and core modules are fully operational:

```bash
# Execute comprehensive environment health check
python utils/health_check.py
```

**Expected Healthy Output**:
```
==================================================
TruthGPT Optimization Core - Health Check Report
==================================================
[✔] Python Version: 3.10.12 (Compatible)
[✔] PyTorch Version: 2.3.0+cu121
[✔] CUDA Available: True (NVIDIA RTX 4090 / 24576 MB)
[✔] BF16 Supported: True
[✔] TF32 Supported: True
[✔] TorchInductor / Triton: Operational
[✔] Polyglot Core Imports: Verified
[✔] OpenClaw Agent Registry: 14 Agents Registered
[✔] Research Papers Registry: 48 Papers Loaded
==================================================
All Systems Operational. Ready for execution.
==================================================
```
