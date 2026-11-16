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
OS="$(uname -s)"
if [ "$OS" = "Darwin" ]; then
    echo "🍎 macOS detected - installing Apple Silicon/MPS optimized packages..."
    pip install torch torchvision torchaudio transformers accelerate datasets typer rich pydantic fastapi uvicorn
else
    if [ -f "requirements_advanced.txt" ]; then
        pip install -r requirements_advanced.txt
    else
        echo "⚠️  requirements_advanced.txt not found, installing basic packages..."
        pip install torch transformers datasets accelerate typer rich
    fi
fi

# Install TruthGPT in editable mode to register truthgpt & truth CLI entry points
echo "📦 Installing TruthGPT package (editable mode)..."
pip install -e .

# Create global wrapper script so 'truthgpt' works in any terminal
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
cat << EOF > "$BIN_DIR/truthgpt"
#!/usr/bin/env bash
SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR="$(pwd)"
exec "\$PROJECT_DIR/.venv/bin/python" "\$PROJECT_DIR/truth_cli.py" "\$@"
EOF
chmod +x "$BIN_DIR/truthgpt"
ln -sf "$BIN_DIR/truthgpt" "$BIN_DIR/truth"

# Ensure ~/.local/bin is in PATH for zsh / bash
for RC in "$HOME/.zshrc" "$HOME/.bashrc"; do
    if [ -f "$RC" ] || [ "$RC" = "$HOME/.zshrc" ]; then
        touch "$RC"
        if ! grep -q '\.local/bin' "$RC"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
        fi
    fi
done

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
echo "✅ Setup complete!"
echo "🚀 You can now run 'truthgpt' or 'truth' directly!"
echo "📖 Run 'make help' to see available commands"


