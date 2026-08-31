"""
Interactive Prompt & Choice Reader for TruthGPT Interface.
===========================================================
Provides synchronous and asynchronous input handling, timeout-guarded readers,
and full-screen prompt_toolkit menu dialogs.
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Dict, List, Optional

from interface.input_utils import (
    _HAS_PROMPT_TOOLKIT,
    _build_ctrl_o_keybindings,
    _check_prompt_toolkit,
    get_choice,
    get_input,
)
from interface.interfaces import BaseInputReader
from interface.theming import (
    get_theme_color,
    get_theme_panel,
)




async def async_input_with_timeout(prompt: str, timeout: float = 30.0) -> Optional[str]:
    """
    Read user keyboard input asynchronously with a strict timeout limit.
    Cross-platform support for Windows (msvcrt) and Unix (select/to_thread).
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()

    start_time = asyncio.get_event_loop().time()
    input_str = ""

    if os.name == "nt":
        try:
            import msvcrt

            while msvcrt.kbhit():
                msvcrt.getch()

            while asyncio.get_event_loop().time() - start_time < timeout:
                await asyncio.sleep(0.02)
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch in (b"\r", b"\n"):
                        sys.stdout.write("\n")
                        sys.stdout.flush()
                        return input_str.strip()
                    elif ch == b"\x08":  # backspace
                        if len(input_str) > 0:
                            input_str = input_str[:-1]
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                    elif ch == b"\xe0":  # special arrow keys
                        if msvcrt.kbhit():
                            msvcrt.getch()
                    elif ch == b"\x03":  # Ctrl+C
                        raise KeyboardInterrupt()
                    else:
                        try:
                            char_str = ch.decode("utf-8")
                            if len(char_str) == 1 and (ord(char_str) >= 32 or char_str == "\t"):
                                input_str += char_str
                                sys.stdout.write(char_str)
                                sys.stdout.flush()
                        except UnicodeDecodeError:
                            pass
            sys.stdout.write("\n")
            sys.stdout.flush()
            return None
        except Exception:
            pass

    # Unix or NT fallback
    try:
        def _blocking_input() -> str:
            return input()

        return await asyncio.wait_for(asyncio.to_thread(_blocking_input), timeout=timeout)
    except asyncio.TimeoutError:
        return None
    except Exception:
        return None


class InputReader(BaseInputReader):
    """Concrete implementation of BaseInputReader."""

    def ask_input(
        self,
        message: str,
        choices: Optional[List[str]] = None,
        default: str = "",
        password: bool = False,
    ) -> str:
        return get_input(message, choices=choices, default=default, password=password)

    def get_input(
        self,
        message: str,
        choices: Optional[List[str]] = None,
        default: str = "",
        password: bool = False,
    ) -> str:
        return get_input(message, choices=choices, default=default, password=password)

    async def ask_choice(
        self,
        title: str,
        options: Dict[str, str],
        style_name: str = "plum1",
    ) -> str:
        return await get_choice(title, options, style_name=style_name)

    async def get_choice(
        self,
        title: str,
        options: Dict[str, str],
        style_name: str = "plum1",
    ) -> str:
        return await get_choice(title, options, style_name=style_name)

    def confirm(self, message: str, default: bool = True) -> bool:
        ans = get_input(f"{message} (y/n)", choices=["y", "n", "yes", "no", ""], default="y" if default else "n")
        return ans.lower() in ("y", "yes", "") if default else ans.lower() in ("y", "yes")


__all__ = [
    "InputReader",
    "get_input",
    "get_choice",
    "get_theme_color",
    "get_theme_panel",
    "async_input_with_timeout",
    "_check_prompt_toolkit",
    "_build_ctrl_o_keybindings",
]
