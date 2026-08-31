"""
Console Management & Terminal Control Utilities for TruthGPT Interface.
=======================================================================
Provides lazy console proxy initialization, Windows terminal mouse mode flags,
screen clearing, and interactive execution pause controls.
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional

from rich.console import Console

_console: Optional[Console] = None


def get_console() -> Console:
    """Lazily instantiate and return the Rich Console."""
    global _console
    if _console is None:
        _console = Console()
    return _console


class LazyConsole:
    """Proxy object that defers Rich Console initialization until first use."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_console(), name)

    def __repr__(self) -> str:
        return repr(get_console())

    def __enter__(self) -> Any:
        return get_console().__enter__()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        return get_console().__exit__(exc_type, exc_val, exc_tb)


LazyConsole.LazyConsole = LazyConsole  # type: ignore[attr-defined]

console: LazyConsole = LazyConsole()


def disable_quick_edit() -> None:
    """Disables QuickEdit mode in Windows Terminal to allow mouse clicks to be captured cleanly."""
    if os.name == "nt":
        import ctypes

        try:
            kernel32 = ctypes.windll.kernel32
            h_input = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
            mode = ctypes.c_uint()
            kernel32.GetConsoleMode(h_input, ctypes.byref(mode))

            # Disable QuickEdit (0x0040)
            # Enable Mouse Input (0x0010)
            # Enable Extended Flags (0x0080)
            # Enable Window Input (0x0008)
            new_mode = (mode.value & ~0x0040) | 0x0010 | 0x0080 | 0x0008
            kernel32.SetConsoleMode(h_input, new_mode)

            # Enable Virtual Terminal Processing for output
            h_output = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            out_mode = ctypes.c_uint()
            kernel32.GetConsoleMode(h_output, ctypes.byref(out_mode))
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(h_output, out_mode.value | 0x0004)
        except Exception:
            pass


# Automatically ensure terminal mode flags are applied
disable_quick_edit()


def clear_screen() -> None:
    """Clears the terminal screen across Windows and Unix platforms."""
    os.system("cls" if os.name == "nt" else "clear")


def wait_for_user(force: bool = False, timeout: int = 15) -> None:
    """Pause execution until the user presses a key or timeout expires."""
    from interface.config import USER_PREFS

    if force or not USER_PREFS.get("continuous_mode", False):
        try:
            import msvcrt

            console.print(
                f"\n[dim]Press Enter to continue... (Auto-continuing in {timeout}s)[/dim]",
                end="",
            )
            start_time = time.time()
            while time.time() - start_time < timeout:
                if msvcrt.kbhit():
                    msvcrt.getch()
                    console.print()
                    return
                time.sleep(0.1)
            console.print("\n[bold yellow]⌛ Idle timeout. Continuing autonomously...[/bold yellow]")
        except ImportError:
            try:
                console.input("\n[dim]Press Enter to continue...[/dim]")
            except Exception:
                pass
    else:
        time.sleep(1)
