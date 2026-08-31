"""
Global System State & Event Logging for TruthGPT Interface.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from interface.config import USER_PREFS
from interface.console import console

# Global System State
SYSTEM_LOGS: List[Dict[str, Any]] = []
system_history: List[Dict[str, Any]] = []
background_missions: List[Any] = []
BLOCKCHAIN_READY: bool = False


def log_event(layer: str, event: str, status: str = "DONE") -> None:
    """Record a system-level event, update in-memory log, and dispatch to styling/history."""
    timestamp = time.strftime("%H:%M:%S")
    SYSTEM_LOGS.append(
        {"time": timestamp, "layer": layer, "event": event, "status": status}
    )

    # Persist to cross-session history ledger
    try:
        from datetime import datetime
        from interface.history_menu import _persist_event

        _persist_event(
            {
                "time": timestamp,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "layer": layer,
                "event": event,
                "status": status,
                "kind": "event",
            }
        )
    except Exception:
        pass

    theme = USER_PREFS.get("theme", "industrial")
    if theme in ["claude", "anthropic", "minimalist"]:
        from interface.cc_style import cc_log_event

        cc_log_event(layer, event, status)
    else:
        console.print(
            f"[dim]{timestamp}[/dim] [[bold orange3]{layer.upper()}[/bold orange3]] "
            f"[white]{event}[/white] -> [bold green]{status}[/bold green]"
        )


def log_activity(module: str, task: str, status: str = "Completed") -> None:
    """Record a module activity, update rolling history buffer, and dispatch to styling/history."""
    timestamp = time.strftime("%H:%M:%S")
    system_history.append(
        {
            "time": timestamp,
            "module": module,
            "task": task,
            "action": task,
            "status": status,
        }
    )
    if len(system_history) > 20:
        system_history.pop(0)

    # Persist to cross-session history ledger
    try:
        from datetime import datetime
        from interface.history_menu import _persist_event

        _persist_event(
            {
                "time": timestamp,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "module": module,
                "task": task,
                "status": status,
                "kind": "activity",
            }
        )
    except Exception:
        pass

    theme = USER_PREFS.get("theme", "industrial")
    if theme in ["claude", "anthropic", "minimalist"]:
        from interface.cc_style import cc_log_activity

        cc_log_activity(module, task, status)


def claude_log_event(layer: str, event: str, status: str = "DONE") -> None:
    """Claude-style log entry: clean and minimal."""
    colors = {"DONE": "green", "RUNNING": "cyan", "ERROR": "red", "PENDING": "dim"}
    color = colors.get(status, "white")
    timestamp = time.strftime("%H:%M:%S")
    console.print(
        f"[dim]{timestamp}[/dim] [bold plum1]│[/bold plum1] [white]{layer.upper():<8}[/white] "
        f"[dim]➔[/dim] [{color}]{event}[/{color}]"
    )
