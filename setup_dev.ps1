# Development setup script for optimization_core (Windows/PowerShell)

Write-Host "🚀 Setting up TruthGPT Optimization Core..." -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "✅ Activating virtual environment..." -ForegroundColor Green
.\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements_advanced.txt") {
    pip install -r requirements_advanced.txt
} else {
    Write-Host "⚠️  requirements_advanced.txt not found, installing basic packages..." -ForegroundColor Yellow
    pip install torch transformers datasets accelerate
}

# Validate installation
Write-Host "🧪 Validating installation..." -ForegroundColor Yellow
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"

# Validate config
if ((Test-Path "validate_config.py") -and (Test-Path "configs/llm_default.yaml")) {
    Write-Host "✅ Validating configuration..." -ForegroundColor Yellow
    python validate_config.py configs/llm_default.yaml
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "📖 Activate with: .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan


