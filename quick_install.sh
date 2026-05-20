#!/bin/bash

echo "============================================================"
echo "   TRUTHGPT - QUICK INSTALL (MAXIMUM SPEED)"
echo "============================================================"
echo ""

echo "[1/4] Installing PyTorch with CUDA..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo ""
echo "[2/4] Installing Transformers and Accelerate..."
pip install transformers accelerate bitsandbytes

echo ""
echo "[3/4] Installing GPU Optimization..."
pip install xformers triton

echo ""
echo "[4/4] Installing Essential Tools..."
pip install gradio wandb tqdm

echo ""
echo "============================================================"
echo "   INSTALLATION COMPLETE!"
echo "============================================================"
echo ""
echo "Verifying installation..."
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
echo ""
echo "DONE! You are ready to go!"

