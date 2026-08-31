"""
Event Logging, Activity Tracking & History Persistence for TruthGPT Interface.
"""
from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

# Canonical state and core event loggers
from interface.state import (
    BLOCKCHAIN_READY,
    SYSTEM_LOGS,
    background_missions,
    claude_log_event,
    log_activity,
    log_event,
    system_history,
)


def persist_current_session() -> None:
    """Flush in-memory activity logs to the persistent ledger."""
    try:
        from interface.history_menu import persist_current_session as _persist
        _persist()
    except Exception:
        pass


def load_history(limit: int = 200) -> List[Dict[str, Any]]:
    """Retrieve history ledger entries."""
    try:
        from interface.history_menu import load_history as _load
        return _load(limit=limit)
    except Exception:
        return []


def record_action(module: str, action: str, status: str = "OK", meta: Optional[Dict[str, Any]] = None) -> None:
    """Record an audit action into both memory and persistent storage."""
    try:
        from interface.history_menu import record_action as _rec
        _rec(module, action, status=status, meta=meta)
    except Exception:
        pass


__all__ = [
    "BLOCKCHAIN_READY",
    "SYSTEM_LOGS",
    "background_missions",
    "claude_log_event",
    "log_activity",
    "log_event",
    "system_history",
    "persist_current_session",
    "load_history",
    "record_action",
]
