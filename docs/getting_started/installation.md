# 📦 Installation Guide

This guide provides step-by-step instructions for installing the TruthGPT Optimization Core across Linux, macOS, and Windows environments, configuring hardware acceleration (CUDA/ROCm/MPS), and compiling native polyglot modules.

---

## 📋 System Prerequisites

| Component | Minimum | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Linux (Ubuntu 20.04+), macOS 12+, Windows 10/11 (WSL2 / PowerShell) | Ubuntu 22.04 LTS or WSL2 |
| **Python** | 3.8+ | **3.10** or **3.11** |
| **Hardware** | 8 GB RAM, 4 CPU cores | NVIDIA GPU (Ampere/Ada/Hopper, 16GB+ VRAM), 32 GB RAM |
| **CUDA** | CUDA 11.8+ | CUDA 12.1+ / cuDNN 8.9+ |
| **C/C++ Compiler** | GCC 9+ / Clang 12+ / MSVC 2019+ | GCC 11+ or Clang 15+ |
| **Rust (Optional)** | Rust 1.70+ (`cargo`) for native kernels | Rust 1.75+ |

---

## 🚀 Quick Setup (Automated)

We provide automated setup scripts that configure a dedicated virtual environment, install base dependencies, and link project packages:

### Linux / macOS
```bash
cd optimization_core
chmod +x setup_dev.sh
./setup_dev.sh
```

### Windows (PowerShell)
```powershell
cd optimization_core
.\setup_dev.ps1
```

---

## 🛠️ Granular Step-by-Step Installation

### Step 1: Virtual Environment Setup

Always install into an isolated environment to prevent dependency conflicts.

```bash
# Python venv
python -m venv .venv

# Activate on Linux/macOS:
source .venv/bin/activate

# Activate on Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Upgrade pip, wheel, and setuptools
pip install --upgrade pip setuptools wheel
```

*(Alternative using Conda)*:
```bash
conda create -n truthgpt python=3.10 -y
conda activate truthgpt
```

---

### Step 2: Install PyTorch with Hardware Acceleration

Select the exact build corresponding to your target accelerator:

#### NVIDIA CUDA 12.1 (Recommended for RTX 30/40 Series, A100, H100)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### NVIDIA CUDA 11.8 (For Turing / Volta GPUs like T4, V100, RTX 2080)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### AMD ROCm 5.7+ (For Radeon RX 7000 / Instinct GPUs on Linux)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7
```

#### Apple Silicon (M1 / M2 / M3 / M4 - Metal Performance Shaders)
```bash
pip install torch torchvision torchaudio
```

#### CPU-Only Mode
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

---

### Step 3: Install TruthGPT Optimization Core

Install project core dependencies and register the package in editable mode:

```bash
# Core requirements
pip install -r requirements.txt

# Or install advanced packages (includes FlashAttention, DeepSpeed, etc.)
pip install -r requirements_advanced.txt

# Install editable package
pip install -e .
```

---

### Step 4: Optional Extension Groups

TruthGPT uses modular extension groups so you only install what you need:

```bash
# Inspect available feature groups
python install_extras.py --list

# Install specific groups
python install_extras.py wandb        # Weights & Biases telemetry
python install_extras.py bitsandbytes   # 8-bit & 4-bit quantization optimizers
python install_extras.py agents        # OpenClaw agent swarm dependencies (ChromaDB, FastAPI)
python install_extras.py compiler      # MLIR / TensorRT / Triton tooling

# Install all optional extensions
python install_extras.py all
```

---

### Step 5: Polyglot Native Cores (Optional)

If using native multi-language acceleration modules:

#### Rust Core (`rust_core/`)
```bash
cd rust_core
cargo build --release
cd ..
```

#### C++ Core (`cpp_core/`)
```bash
mkdir -p cpp_core/build && cd cpp_core/build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
cd ../..
```

---

## 🐳 Docker Deployment

For standardized containerized training and serving:

```bash
# Build container image
docker build -t truthgpt-optimization-core:latest .

# Run with full NVIDIA GPU passthrough
docker run --gpus all --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
    -v $(pwd)/runs:/app/runs \
    -p 8080:8080 \
    -it truthgpt-optimization-core:latest
```

---

## 🔍 Verification & Health Check

Confirm your installation is operational:

```bash
# Run system diagnostics
python utils/health_check.py

# Run quick unit tests
pytest tests/unit/
```
