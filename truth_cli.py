"""
🚀 TruthGPT CLI - Shim for Modular CLI Package
"""
import sys
from pathlib import Path

# Add the current directory to sys.path to ensure cli package is found
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from truth_cli import app

if __name__ == "__main__":
    app()
