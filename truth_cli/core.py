import os
import sys
from pathlib import Path
_console = None

def get_console():
    global _console
    if _console is None:
        from rich.console import Console
        _console = Console()
    return _console

class LazyConsole:
    def __getattr__(self, name):
        return getattr(get_console(), name)
    def __repr__(self):
        return repr(get_console())
    def __enter__(self):
        return get_console().__enter__()
    def __exit__(self, exc_type, exc_val, exc_tb):
        return get_console().__exit__(exc_type, exc_val, exc_tb)

console = LazyConsole()

def _fix_param(val, default_val):
    """Helper to unwrap Typer OptionInfo if called directly."""
    if hasattr(val, "default"):
        return val.default
    return val if val is not None else default_val

def safe_int(val, default=10):
    """Aggressively convert to int to fix slicing errors."""
    try:
        if hasattr(val, "default"):
            return int(val.default)
        return int(val)
    except:
        return default

def get_root_dirs():
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    CURRENT_DIR = Path(__file__).resolve().parent.parent
    return ROOT_DIR, CURRENT_DIR

def setup_paths():
    ROOT_DIR, CURRENT_DIR = get_root_dirs()
    # Prioritize the local package directories over the current working directory
    if str(CURRENT_DIR) not in sys.path:
        sys.path.insert(0, str(CURRENT_DIR))
    if str(ROOT_DIR) not in sys.path:
        sys.path.append(str(ROOT_DIR))
