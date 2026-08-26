# Installation & Environment Matrix

TruthGPT Optimization Core is engineered to scale across heterogeneous compute environments, from local Apple Silicon laptops to multi-node NVIDIA H100 GPU clusters.

---

## 💻 Hardware & Environment Support Matrix

| Hardware Tier | Recommended PyTorch / CUDA | Supported Features |
| :--- | :--- | :--- |
| **NVIDIA Hopper / Blackwell (H100/H200/B200)** | PyTorch 2.2+, CUDA 12.1 / 12.4 | Flash Attention 3, FP8 Tensor Cores, Transformer Engine, TorchDynamo, TorchInductor |
| **NVIDIA Ada / Ampere (RTX 4090 / A100 / RTX 3090)** | PyTorch 2.1+, CUDA 11.8 / 12.1 | Flash Attention 2, TF32, BF16 AMP, Fused AdamW, Paged KV-Cache |
| **NVIDIA Turing / Volta (T4 / V100)** | PyTorch 2.0+, CUDA 11.8 | FP16 AMP, SDPA (Math/MemEfficient), Gradient Checkpointing |
| **Apple Silicon (M1 / M2 / M3 / M4 Pro/Max)** | PyTorch 2.0+ (MPS backend) | Native Metal Acceleration, FP16, AdamW, OpenClaw Swarm |
| **x86_64 / ARM64 CPU** | PyTorch 2.0+ | Polyglot acceleration, C++ / Rust kernels, Debugging & Simulation |

---

## 🚀 1. Automated Quick Setup

Automated scripts detect your operating system and configure a clean virtual environment with appropriate dependencies.

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

## 📦 2. Manual Step-by-Step Installation

### Step 1: Environment Isolation
```bash
# Using standard Python virtualenv
python -m venv .venv

# Activate on Linux/macOS
source .venv/bin/activate

# Activate on Windows PowerShell
# .\.venv\Scripts\Activate.ps1
```

Or using Conda:
```bash
conda create -n truthgpt python=3.10 -y
conda activate truthgpt
```

### Step 2: PyTorch with GPU Acceleration
Install the PyTorch build that matches your CUDA toolkit:

**For CUDA 12.1 / 12.4 (Modern GPUs):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**For CUDA 11.8 (Legacy Enterprise GPUs):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**For Apple Silicon (Metal Performance Shaders):**
```bash
pip install torch torchvision torchaudio
```

### Step 3: Core Framework Dependencies
```bash
pip install -r requirements_advanced.txt
```

### Step 4: Optional Extension Groups
TruthGPT uses modular dependency packages via `install_extras.py`:

```bash
# Check status of all extension groups
python install_extras.py --check

# Install specific groups
python install_extras.py wandb          # Weights & Biases telemetry
python install_extras.py bitsandbytes   # 8-bit & 4-bit optimizers
python install_extras.py flash_attn     # Flash Attention 2 compile tools
python install_extras.py polyglot       # C-FFI cross-language bindings

# Install all optional extensions
python install_extras.py all
```

---

## 🐳 3. Docker & Containerized Deployment

Production-ready Docker environments ensure reproducible CUDA driver bindings:

```dockerfile
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

WORKDIR /workspace

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip git build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install PyTorch & TruthGPT requirements
COPY requirements_advanced.txt .
RUN pip3 install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu121 && \
    pip3 install --no-cache-dir -r requirements_advanced.txt

COPY . .

CMD ["python3", "train_llm.py", "--config", "configs/presets/performance_max.yaml"]
```

### Build & Run:
```bash
docker build -t truthgpt-core:latest .
docker run --gpus all --ipc=host -it truthgpt-core:latest
```

---

## ✅ 4. Verifying Environment Health

Run the diagnostic validation script to verify all hardware paths and registries:

```bash
python utils/health_check.py
```
