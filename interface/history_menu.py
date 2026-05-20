"""
📜 TruthGPT Activity History & Live Feed
System 5.9 — Persistent Event Ledger with Live Tail

Provides:
  - Live view of current session activity (what IS happening)
  - Persistent log of past session actions (what WAS done)
  - Filterable, scrollable, Claude-Code-style presentation
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns

from interface.core import (
    console, clear_screen, get_header, get_input,
    SYSTEM_LOGS, system_history, USER_PREFS, log_activity,
)
from interface.cc_style import (
    cc_menu, cc_action, cc_divider, cc_spinner, cc_result,
    BULLET, CONT, ARROW,
)


# ---------------------------------------------------------------------------
# Persistence paths
# ---------------------------------------------------------------------------

_HISTORY_DIR = Path(__file__).resolve().parent.parent / "truthgpt_collected" / "Truthgpt_sessions"
_HISTORY_FILE = _HISTORY_DIR / "activity_history.jsonl"
_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _persist_event(entry: Dict[str, Any]) -> None:
    """Append a single event dict as a JSON line to the persistent ledger."""
    try:
        with open(_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def persist_current_session() -> None:
    """Flush all in-memory SYSTEM_LOGS and system_history to the ledger file."""
    session_id = f"S-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    for entry in SYSTEM_LOGS:
        _persist_event({**entry, "session": session_id, "kind": "event"})
    for entry in system_history:
        _persist_event({**entry, "session": session_id, "kind": "activity"})


def load_history(limit: int = 200) -> List[Dict[str, Any]]:
    """Read the last *limit* entries from the persistent ledger."""
    if not _HISTORY_FILE.exists():
        return []
    try:
        lines = _HISTORY_FILE.read_text(encoding="utf-8").strip().splitlines()
        entries = []
        for line in lines[-limit:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries
    except Exception:
        return []


def record_action(module: str, action: str, status: str = "OK", meta: Optional[Dict] = None) -> None:
    """Record an action to both in-memory history AND the persistent ledger.
    
    Call this from anywhere in the codebase to leave an audit trail.
    """
    timestamp = time.strftime("%H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = {
        "time": timestamp,
        "date": date_str,
        "module": module,
        "action": action,
        "status": status,
        "meta": meta or {},
        "kind": "action",
    }
    # Also add to in-memory list
    system_history.append(entry)
    if len(system_history) > 50:
        system_history.pop(0)
    # Persist
    _persist_event(entry)


# ---------------------------------------------------------------------------
# Status Styling
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "OK":        "green",
    "DONE":      "green",
    "Completed": "green",
    "RUN":       "cyan",
    "RUNNING":   "cyan",
    "WARN":      "yellow",
    "PENDING":   "yellow",
    "ERROR":     "red",
    "FAIL":      "red",
    "INFO":      "white",
}


def _render_status(status: str) -> str:
    color = _STATUS_COLORS.get(status, "dim")
    return f"[{color}]{status}[/{color}]"


# ---------------------------------------------------------------------------
# TUI: Main History Menu
# ---------------------------------------------------------------------------

@cc_menu("Activity History")
async def history_menu() -> None:
    """Full-screen history viewer with live session + persistent log tabs."""
    while True:
        clear_screen()
        
        # Header
        theme = USER_PREFS.get("theme", "claude")
        color = "plum1" if theme in ["claude", "anthropic", "minimalist"] else "orange3"
        
        console.print(Panel(
            f"[bold {color}]📜 Activity History & Live Feed[/bold {color}]",
            border_style=color,
            subtitle="[dim]What's happening · What was done[/dim]",
        ))
        
        console.print(f"\n  [bold cyan]1[/bold cyan]  [white]🔴 Live Session Feed[/white]    [dim]Current session activity in real-time[/dim]")
        console.print(f"  [bold cyan]2[/bold cyan]  [white]📖 Full History Log[/white]     [dim]All past sessions & actions[/dim]")
        console.print(f"  [bold cyan]3[/bold cyan]  [white]🔍 Search History[/white]        [dim]Filter by module, action, or date[/dim]")
        console.print(f"  [bold cyan]4[/bold cyan]  [white]📊 Session Statistics[/white]    [dim]Aggregated metrics & breakdown[/dim]")
        console.print(f"  [bold cyan]5[/bold cyan]  [white]🗑️  Clear History[/white]         [dim]Purge persistent history ledger[/dim]")
        console.print(f"  [bold cyan]0[/bold cyan]  [white]← Back[/white]\n")
        
        cc_divider()
        choice = get_input("Select", choices=["0", "1", "2", "3", "4", "5"], default="0")
        
        if choice == "0":
            break
        elif choice == "1":
            _show_live_session()
        elif choice == "2":
            _show_full_history()
        elif choice == "3":
            _search_history()
        elif choice == "4":
            _show_statistics()
        elif choice == "5":
            _clear_history()


# ---------------------------------------------------------------------------
# Sub-views
# ---------------------------------------------------------------------------

def _show_live_session() -> None:
    """Show what is currently happening in this session."""
    clear_screen()
    console.print(Panel(
        "[bold cyan]🔴 LIVE SESSION FEED[/bold cyan]",
        border_style="cyan",
        subtitle="[dim]Events from this running session[/dim]",
    ))
    
    # --- System Events (SYSTEM_LOGS) ---
    if SYSTEM_LOGS:
        console.print(f"\n [bold white]System Events[/bold white] [dim]({len(SYSTEM_LOGS)} captured)[/dim]\n")
        
        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
            show_lines=False,
            pad_edge=True,
            expand=True,
        )
        table.add_column("⏱️ Time", style="dim", width=10)
        table.add_column("Layer", style="bold cyan", width=12)
        table.add_column("Event", style="white", ratio=3)
        table.add_column("Status", justify="center", width=12)
        
        for entry in SYSTEM_LOGS[-30:]:
            table.add_row(
                entry.get("time", "—"),
                entry.get("layer", "—").upper(),
                entry.get("event", "—"),
                _render_status(entry.get("status", "—")),
            )
        console.print(table)
    else:
        console.print("\n [dim]No system events captured yet in this session.[/dim]")
    
    # --- Activity History (system_history) ---
    if system_history:
        console.print(f"\n [bold white]Activity Log[/bold white] [dim]({len(system_history)} entries)[/dim]\n")
        
        table = Table(
            show_header=True,
            header_style="bold magenta",
            border_style="dim",
            show_lines=False,
            expand=True,
        )
        table.add_column("⏱️ Time", style="dim", width=10)
        table.add_column("Module", style="bold yellow", width=16)
        table.add_column("Action", style="white", ratio=3)
        table.add_column("Status", justify="center", width=12)
        
        for entry in system_history[-20:]:
            table.add_row(
                entry.get("time", "—"),
                entry.get("module", "—"),
                entry.get("task", entry.get("action", "—")),
                _render_status(entry.get("status", "—")),
            )
        console.print(table)
    else:
        console.print("\n [dim]No activity recorded yet in this session.[/dim]")
    
    console.print()
    cc_divider()
    get_input("Press Enter to return", default="")


def _show_full_history() -> None:
    """Show the persistent cross-session history ledger."""
    clear_screen()
    
    entries = load_history(limit=200)
    
    console.print(Panel(
        f"[bold green]📖 FULL HISTORY LOG[/bold green]  [dim]({len(entries)} entries loaded)[/dim]",
        border_style="green",
        subtitle=f"[dim]Stored at: {_HISTORY_FILE.name}[/dim]",
    ))
    
    if not entries:
        console.print("\n [dim]No persistent history found. Activity will be recorded as you use TruthGPT.[/dim]")
        console.print(f" [dim]History file: {_HISTORY_FILE}[/dim]\n")
        get_input("Press Enter to return", default="")
        return
    
    # Group by date
    by_date: Dict[str, List[Dict]] = {}
    for entry in entries:
        date_key = entry.get("date", entry.get("time", "Unknown")[:10])
        if date_key not in by_date:
            by_date[date_key] = []
        by_date[date_key].append(entry)
    
    # Display grouped by date (most recent first)
    for date_key in sorted(by_date.keys(), reverse=True)[:7]:
        day_entries = by_date[date_key]
        console.print(f"\n [bold white]📅 {date_key}[/bold white] [dim]({len(day_entries)} events)[/dim]")
        console.print(f" [dim]{'─' * 70}[/dim]")
        
        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
            show_lines=False,
            expand=True,
        )
        table.add_column("⏱️", style="dim", width=10)
        table.add_column("Type", style="bold blue", width=10)
        table.add_column("Module", style="bold yellow", width=16)
        table.add_column("Detail", style="white", ratio=3)
        table.add_column("Status", justify="center", width=10)
        table.add_column("Session", style="dim", width=18)
        
        for entry in day_entries[-40:]:
            kind = entry.get("kind", "event")
            kind_icon = "🔵" if kind == "event" else "🟢" if kind == "activity" else "🟡"
            detail = entry.get("event", entry.get("action", entry.get("task", "—")))
            module = entry.get("layer", entry.get("module", "—"))
            
            table.add_row(
                entry.get("time", "—"),
                f"{kind_icon} {kind[:6]}",
                module[:16],
                detail[:60],
                _render_status(entry.get("status", "—")),
                entry.get("session", "—")[:18],
            )
        
        console.print(table)
    
    console.print()
    cc_divider()
    get_input("Press Enter to return", default="")


def _search_history() -> None:
    """Filter history by keyword."""
    clear_screen()
    console.print(Panel(
        "[bold yellow]🔍 SEARCH HISTORY[/bold yellow]",
        border_style="yellow",
    ))
    
    query = get_input("Search term (module, action, or keyword)").strip().lower()
    if not query:
        return
    
    entries = load_history(limit=500)
    matches = []
    for entry in entries:
        searchable = json.dumps(entry, ensure_ascii=False).lower()
        if query in searchable:
            matches.append(entry)
    
    console.print(f"\n [bold]Found {len(matches)} results for '[cyan]{query}[/cyan]'[/bold]\n")
    
    if not matches:
        console.print(" [dim]No matching entries. Try a broader term.[/dim]")
        get_input("Press Enter to return", default="")
        return
    
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        expand=True,
    )
    table.add_column("Date", style="dim", width=12)
    table.add_column("⏱️", style="dim", width=10)
    table.add_column("Module", style="bold yellow", width=16)
    table.add_column("Detail", style="white", ratio=3)
    table.add_column("Status", justify="center", width=10)
    
    for entry in matches[-50:]:
        detail = entry.get("event", entry.get("action", entry.get("task", "—")))
        module = entry.get("layer", entry.get("module", "—"))
        table.add_row(
            entry.get("date", "—"),
            entry.get("time", "—"),
            module[:16],
            detail[:60],
            _render_status(entry.get("status", "—")),
        )
    
    console.print(table)
    console.print()
    cc_divider()
    get_input("Press Enter to return", default="")


def _show_statistics() -> None:
    """Show aggregated stats from history."""
    clear_screen()
    
    entries = load_history(limit=1000)
    
    console.print(Panel(
        "[bold magenta]📊 SESSION STATISTICS[/bold magenta]",
        border_style="magenta",
    ))
    
    if not entries:
        console.print("\n [dim]No history data available for analysis.[/dim]")
        get_input("Press Enter to return", default="")
        return
    
    # Compute metrics
    total_events = len(entries)
    unique_modules = set()
    unique_sessions = set()
    status_counts: Dict[str, int] = {}
    module_counts: Dict[str, int] = {}
    kind_counts: Dict[str, int] = {}
    
    for entry in entries:
        module = entry.get("layer", entry.get("module", "unknown"))
        unique_modules.add(module)
        unique_sessions.add(entry.get("session", ""))
        
        status = entry.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        module_counts[module] = module_counts.get(module, 0) + 1
        
        kind = entry.get("kind", "unknown")
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
    
    # Overview table
    console.print(f"\n [bold white]Overview[/bold white]\n")
    overview = Table(show_header=False, border_style="dim", expand=False, pad_edge=True)
    overview.add_column("Metric", style="bold cyan", width=24)
    overview.add_column("Value", style="white", width=20)
    
    overview.add_row("Total Events", f"[bold]{total_events}[/bold]")
    overview.add_row("Unique Sessions", f"[bold]{len(unique_sessions)}[/bold]")
    overview.add_row("Unique Modules", f"[bold]{len(unique_modules)}[/bold]")
    overview.add_row("Event Types", ", ".join(f"{k}: {v}" for k, v in kind_counts.items()))
    console.print(overview)
    
    # Status breakdown
    console.print(f"\n [bold white]Status Breakdown[/bold white]\n")
    status_table = Table(
        show_header=True,
        header_style="bold green",
        border_style="dim",
        expand=False,
    )
    status_table.add_column("Status", style="bold", width=16)
    status_table.add_column("Count", justify="right", width=10)
    status_table.add_column("Bar", width=30)
    
    max_count = max(status_counts.values()) if status_counts else 1
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        bar_len = int((count / max_count) * 25)
        color = _STATUS_COLORS.get(status, "white")
        bar = f"[{color}]{'█' * bar_len}{'░' * (25 - bar_len)}[/{color}]"
        status_table.add_row(_render_status(status), str(count), bar)
    
    console.print(status_table)
    
    # Top modules
    console.print(f"\n [bold white]Top Modules[/bold white]\n")
    mod_table = Table(
        show_header=True,
        header_style="bold yellow",
        border_style="dim",
        expand=False,
    )
    mod_table.add_column("Module", style="bold cyan", width=20)
    mod_table.add_column("Events", justify="right", width=10)
    
    for module, count in sorted(module_counts.items(), key=lambda x: -x[1])[:10]:
        mod_table.add_row(module[:20], str(count))
    
    console.print(mod_table)
    
    console.print()
    cc_divider()
    get_input("Press Enter to return", default="")


def _clear_history() -> None:
    """Purge the persistent history file after confirmation."""
    console.print("\n [bold red]⚠️  WARNING:[/bold red] This will permanently delete all persistent history.")
    confirm = get_input("Type 'DELETE' to confirm", default="")
    
    if confirm.strip().upper() == "DELETE":
        try:
            if _HISTORY_FILE.exists():
                _HISTORY_FILE.unlink()
            cc_action("History ledger purged successfully", status="DONE")
        except Exception as e:
            cc_action(f"Failed to clear history: {e}", status="ERROR")
    else:
        cc_action("Clear cancelled — history preserved", status="INFO")
    
    time.sleep(1)
