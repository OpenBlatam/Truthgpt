"""
🚀 TruthGPT Command Center — Modular Orchestrator
System 5.9 Gold Standard
"""
import sys
import os
import asyncio
import time
import logging
from pathlib import Path

# Configure logging
import logging
import warnings
from loguru import logger as loguru_logger

# Suppress all user warnings and deprecation warnings to keep TUI pristine
warnings.filterwarnings("ignore")

# Remove Loguru's default console logger to keep the TUI 100% clean like Claude
loguru_logger.remove()

# Configure standard root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)

# Remove any console handlers from standard root logger to prevent noise
for handler in list(root_logger.handlers):
    root_logger.removeHandler(handler)

# Redirect all warnings/errors to a file for persistent agential observability
log_dir = Path(__file__).resolve().parent / "truthgpt_collected" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(log_dir / "truthgpt.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root_logger.addHandler(file_handler)

# Configure loguru to write to its OWN per-process file. Sharing "truthgpt.log"
# with the stdlib FileHandler above (or with a second running instance) made
# loguru's rotation rename fail on Windows with WinError 32 ("file in use").
# A per-PID filename + enqueue (non-blocking, process-safe) + catch (never let a
# logging failure crash the TUI) removes that whole class of errors.
loguru_logger.add(
    log_dir / f"truthgpt_loguru_{os.getpid()}.log",
    level="WARNING",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
    enqueue=True,
    catch=True,
)

# Force specific heavy loggers to be silent
for logger_name in [
    "modules.base.core_system.core.papers.paper_registry",
    "paper_registry_refactored",
    "main",
    "diffusers",
    "torch",
    "httpx",
    "urllib3",
    "agents.razonamiento_planificacion.orchestrator"
]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Force UTF-8 for Windows Console compatibility
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

# --- Path Initialization ---
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(current_dir.parent) not in sys.path:
    sys.path.insert(0, str(current_dir.parent))

from agents.ssl_context import ensure_ssl_certificates

ensure_ssl_certificates()

# Modular Imports (Lazy loading handled in main_loop)
from interface.core import (
    console, clear_screen, linux_boot_sequence, show_main_dashboard, 
    handle_personalize
)

async def main_loop():
    linux_boot_sequence()
    sys.stdout.flush()
    
    # Record boot event to persistent history
    try:
        from interface.history_menu import record_action
        record_action("KERNEL", "TruthGPT OS v5.9 session started", "OK")
    except Exception:
        pass
    
    # Defer pre-heating to background thread to keep UI snappy
    import threading
    def preheat():
        try:
            # We wait a bit to let the UI start first
            time.sleep(0.5)
            
            # Lazy imports one by one to yield the GIL
            from interface import swarm_menu
            import agents.client as ac
            import agents.engines as ae
            
            # Use preferred engine from prefs
            from interface.core import USER_PREFS
            engine_name = USER_PREFS.get("preferred_engine", "deepseek")
            llm = ae.engine_registry.get_engine(engine_name)
            
            swarm_menu._client_cache = ac.AgentClient(use_swarm=True, llm_engine=llm)
            
            # Preheat PaperRegistry (this is the heavy part)
            # We import it here but run the scan separately
            from modules.base.core_system.core.papers.paper_registry import get_paper_registry
            registry = get_paper_registry(preload_popular=False)
            
            # Update the interface cache
            import interface.core as ic
            ic._CACHED_PAPER_COUNT = len(registry.list_papers())
            
            logger.info("Preheat complete: Swarm Client and Paper Registry ready.")
        except Exception as e:
            logger.error(f"Preheat error: {e}")

    preheat_thread = threading.Thread(target=preheat, daemon=True)
    preheat_thread.start()

    extended_mode = True
    
    # Pre-import dashboard to avoid latency in the loop
    from interface.interactive_dashboard import get_dashboard_choice
    
    while True:
        user_input = await get_dashboard_choice(extended=extended_mode)
        
        if user_input is None: 
            continue
            
        choice = str(user_input).lower().strip()
        
        if choice in ["99", "+"]:
            extended_mode = not extended_mode
            continue
            
        if choice in ["reboot", "r"]:
            from interface.core import clear_screen
            from interface.cc_style import cc_action
            clear_screen()
            cc_action("REBOOTING TRUTHGPT KERNEL...", status="WARN")
            time.sleep(1)
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
            os.execl(sys.executable, sys.executable, script_path, *sys.argv[1:])
            
        if choice == "exit" or choice == "x":
            # Persist session history before shutting down
            try:
                from interface.history_menu import persist_current_session
                persist_current_session()
            except Exception:
                pass
            break
            
        # Route via the kernel's InterfaceService
        from main import kernel
        if hasattr(kernel.service_manager, 'get_service'):
            interface_service = kernel.service_manager.get_service("InterfaceService")
            if interface_service:
                await interface_service.execute_command(choice, user_input)
            else:
                from rich.console import Console
                Console().print("[bold red]Kernel InterfaceService not available![/bold red]")
        else:
            from rich.console import Console
            Console().print("[bold red]Kernel Service Manager is missing get_service![/bold red]")

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupted. Exiting...[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Critical Error: {e}[/bold red]")
