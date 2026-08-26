# Installation Guide

> [!NOTE]
> This guide has been expanded in our structured documentation portal at **[Getting Started: Installation Guide](getting-started/installation.md)**.

This guide provides setup instructions for installing TruthGPT Optimization Core across Linux, Windows (WSL2), macOS (MPS), and containerized Docker environments.

---

## 📋 Quick Setup

```bash
# Automated setup for Linux/macOS
./setup_dev.sh

# Or on Windows PowerShell
.\setup_dev.ps1
```

---

## 📦 Manual Installation

```bash
# 1. Install PyTorch with CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 2. Install Core Requirements
pip install -r requirements_advanced.txt

# 3. Verify Health
python utils/health_check.py
```

See **[Full Installation Guide](getting-started/installation.md)** for Conda, Docker, and optional extras configuration.
