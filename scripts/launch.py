import sys
import os
import asyncio

# Forzar el uso de la carpeta local para evitar conflictos con instalaciones globales
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from main import main_loop

if __name__ == "__main__":
    print("🚀 Iniciando TruthGPT (Local Mode - Claude Aesthetic)...")
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n👋 Sistema cerrado.")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
