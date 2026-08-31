"""
Activity Logging & System Event Ledger for TruthGPT Interface.
================================================================
Maintains in-memory session logs, audit trails, and connects to the
persistent activity ledger in history_menu.
"""
from __future__ import annotations

import sys

# Module aliasing for enterprise imports
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.interface.logging":
        sys.modules["interface.logging"] = _mod
    elif __name__ == "interface.logging":
        sys.modules["optimization_core.interface.logging"] = _mod

from interface.state import (
    BLOCKCHAIN_READY,
    SYSTEM_LOGS,
    background_missions,
    claude_log_event,
    log_activity,
    log_event,
    system_history,
)

__all__ = [
    "BLOCKCHAIN_READY",
    "SYSTEM_LOGS",
    "background_missions",
    "claude_log_event",
    "log_activity",
    "log_event",
    "system_history",
]
