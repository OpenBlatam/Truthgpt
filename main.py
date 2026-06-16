"""
🚀 TruthGPT Command Center — Modular Orchestrator
System 6.0 Object-Oriented Architecture
"""
import sys
import asyncio

# Fix Windows emoji encoding issues
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure paths are ready before loading the kernel
from pathlib import Path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from core.kernel.truthgpt_kernel import TruthGPTKernel

kernel = TruthGPTKernel()

async def main_loop():
    # 1. Boot Kernel 2.0
    await kernel.start()
    
    try:
        # 2. Launch the TUI Dashboard
        import main_legacy
        await main_legacy.main_loop()
    except asyncio.CancelledError:
        pass
    finally:
        # 3. Shutdown Kernel 2.0 gracefully
        await kernel.stop()

def _console_hint() -> str:
    return (
        "\nTruthGPT needs a real interactive terminal (the TUI uses prompt_toolkit).\n"
        "Run it directly in a Windows console — PowerShell or cmd.exe:\n\n"
        "    python main.py\n\n"
        "Do NOT run it through a pipe, redirected stdin, Git Bash/MSYS, or a non-TTY\n"
        "environment (e.g. `python main.py | tee`, or from a CI/agent shell).\n"
    )


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        # prompt_toolkit raises NoConsoleScreenBufferError when there is no real
        # Windows console. Surface a clear, actionable hint instead of a traceback.
        if type(e).__name__ == "NoConsoleScreenBufferError" or "ConsoleScreenBuffer" in str(e):
            print(_console_hint(), file=sys.stderr)
            sys.exit(1)
        from loguru import logger
        logger.error(f"Critical Kernel Error: {e}")
        sys.exit(1)
