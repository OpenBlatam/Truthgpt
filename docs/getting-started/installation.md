# Installation & Environment Matrix

TruthGPT Optimization Core is engineered to scale across heterogeneous compute environments, from developer workstations to enterprise multi-node GPU superclusters.

---

## 🖥️ System Prerequisites

| Component | Minimum Specification | Recommended Specification |
| :--- | :--- | :--- |
| **Operating System** | Linux (Ubuntu 20.04+), Windows 11 / Server 2022, macOS 13+ | Ubuntu 22.04 LTS or Rocky Linux 9 |
| **Python** | 3.10 | 3.11 or 3.12 |
| **GPU / Accelerator** | NVIDIA GPU (Turing / RTX 2000+, 8GB VRAM) | NVIDIA Ada Lovelace / Hopper / Blackwell (24GB+ VRAM) |
| **CUDA Driver** | CUDA 11.8+ | CUDA 12.1 or 12.4 |
| **System RAM** | 16 GB | 64 GB+ |
| **Disk Storage** | 20 GB free SSD storage | 100 GB+ NVMe SSD |

---

## ⚡ Quick Automated Setup

### Linux / macOS

```bash
# Clone the repository
git clone https://github.com/OpenBlatam/TruthGPT.git
cd TruthGPT/optimization_core

# Run automated setup script
chmod +x setup_dev.sh
./setup_dev.sh
```

### Windows (PowerShell)

```powershell
# Clone the repository
git clone https://github.com/OpenBlatam/TruthGPT.git
cd TruthGPT\optimization_core

# Execute automated setup script
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\setup_dev.ps1
```

---

## 🛠️ Step-by-Step Manual Setup

### 1. Create and Activate Virtual Environment

```bash
# Create isolated environment
python -m venv .venv

# Activate on Linux/macOS
source .venv/bin/activate

# Activate on Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 2. Install PyTorch with Hardware Acceleration

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

### 3. Install Core TruthGPT Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Optional SOTA Acceleration Extensions

```bash
# Install FlashAttention-2 (Requires CUDA toolkit & GCC/Clang)
pip install flash-attn --no-build-isolation

# Install 8-bit & 4-bit quantization support (bitsandbytes)
pip install bitsandbytes

# Install Triton kernel development headers
pip install triton

# Install observability & telemetry tools (Prometheus, W&B, TensorBoard)
pip install prometheus_client wandb tensorboard
```

---

## 🦀 Compiling Polyglot Native Backends (Optional)

TruthGPT features optional high-performance native engines written in Rust and C++20 for sub-millisecond tokenization, zero-copy buffer pools, and custom tensor contractions.

### 1. Rust Native Engine (`rust_core`)

Requires the Rust toolchain (`cargo` 1.75+):

```bash
# Navigate to rust_core and build release bindings via PyO3 / Maturin
cd rust_core
cargo build --release
pip install maturin
maturin develop --release
cd ..
```

### 2. C++20 & CUDA Kernel Extensions (`cpp_core`)

Requires CMake 3.20+ and GCC 11+ or MSVC 2022:

```bash
cd cpp_core
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
cd ../..
```

### 3. Bazel Multi-Target Build (Enterprise)

TruthGPT provides full enterprise workspace definitions for Bazel:

```bash
# Build complete optimization core with Bazel
bazel build //... --config=cuda --config=opt
```

---

## 🐳 Docker & Containerized Deployment

TruthGPT provides official multi-stage Dockerfiles optimized for CUDA production deployments:

```bash
# Build production Docker image
docker build -t truthgpt-core:latest -f deployment/Dockerfile .

# Run with NVIDIA GPU acceleration enabled
docker run --gpus all --ipc=host -p 8000:8000 -p 8080:8080 truthgpt-core:latest
```

---

## 🔍 Verification & Health Diagnostics

After installation, run the diagnostic suite to verify all CUDA drivers, kernels, and compiler libraries are functional:

```bash
python utils/health_check.py
```
