#!/bin/bash
# Development setup script for optimization_core

set -e

echo "🚀 Setting up TruthGPT Optimization Core..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📦 Installing dependencies..."
if [ -f "requirements_advanced.txt" ]; then
    pip install -r requirements_advanced.txt
else
    echo "⚠️  requirements_advanced.txt not found, installing basic packages..."
    pip install torch transformers datasets accelerate
fi

# Validate installation
echo "🧪 Validating installation..."
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import transformers; print(f'Transformers: {transformers.__version__}')"

# Validate config
if [ -f "validate_config.py" ] && [ -f "configs/llm_default.yaml" ]; then
    echo "✅ Validating configuration..."
    python3 validate_config.py configs/llm_default.yaml
fi

echo ""
echo "✅ Setup complete! Activate with: source .venv/bin/activate"
echo "📖 Run 'make help' to see available commands"


