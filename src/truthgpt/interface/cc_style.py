"""
Claude Code-style terminal aesthetic for TruthGPT.

Renders log lines, tool calls, agent completions, spinners and the bottom
prompt box in the same visual language as the Claude Code CLI:

    ● Let me examine the current working directory structure directly.
      Searched for 2 patterns, read 1 file (ctrl+o to expand)
      ⎿  agents/.../core.py
    ✢ Evaporating… (1m 57s · ↓ 4.1k tokens)

The module is intentionally dependency-light: only Rich (already used by
TruthGPT) plus stdlib. Every helper is safe to call from sync or async code.
"""
from __future__ import annotations

import functools
import inspect
import itertools
import os
import sys
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Deque, Iterable, Iterator, List, Optional, TypeVar

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


SUPPRESS_SPINNERS = False
REASONING_CALLBACK = None


def _enable_utf8_stdout() -> bool:
    """Try to switch stdout/stderr to UTF-8 so the CC glyphs render on Windows.

    Returns True if Unicode glyphs are safe to emit, False if we must fall back.
    """
    try:
        for stream_name in ("stdout", "stderr"):
            stream = getattr(sys, stream_name, None)
            if stream is not None and hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass
    except Exception:
        pass
    enc = (getattr(sys.stdout, "encoding", "") or "").lower()
    return "utf" in enc


_UNICODE_OK = _enable_utf8_stdout()

if _UNICODE_OK:
    BULLET = "●"
    CONT = "⎿"
    SPIN_FRAMES = ["✢", "✳", "✶", "✻", "✽"]
    ARROW = "→"
    CTX_GLYPH = "⧉"
else:
    BULLET = "*"
    CONT = "\\_"
    SPIN_FRAMES = ["|", "/", "-", "\\"]
    ARROW = "->"
    CTX_GLYPH = "[ctx]"

_console = Console(legacy_windows=False if _UNICODE_OK else None, force_terminal=True)

_STATUS_STYLE = {
    "DONE":     ("green",  BULLET),
    "OK":       ("green",  BULLET),
    "RUN":      ("cyan",   BULLET),
    "WAIT":     ("yellow", BULLET),
    "WARN":     ("yellow", BULLET),
    "ERROR":    ("red",    BULLET),
    "FAIL":     ("red",    BULLET),
    "INFO":     ("white",  BULLET),
}


def _fmt_tokens(n: int) -> str:
    if n < 1000:
        return f"{n}"
    if n < 1_000_000:
        return f"{n/1000:.1f}k"
    return f"{n/1_000_000:.1f}M"


def _fmt_elapsed(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    return f"{m}m {s}s"


def cc_action(message: str, status: str = "RUN") -> None:
    """Top-level action line: ``● Let me examine the structure.``"""
    color, glyph = _STATUS_STYLE.get(status.upper(), ("white", BULLET))
    _console.print(f"[bold {color}]{glyph}[/bold {color}] {message}")


def cc_tool_call(summary: str, hint: str = "") -> None:
    """Indented tool-call status: ``  Executing system_health...``."""
    suffix = f" [dim]({hint})[/dim]" if hint else ""
    _console.print(f"  {summary}{suffix}")


def cc_result(path: str, note: str = "") -> None:
    """Result continuation line: ``  ⎿  path/to/file.py``."""
    extra = f"  [dim]{note}[/dim]" if note else ""
    _console.print(f"  [dim]{CONT}[/dim]  [white]{path}[/white]{extra}")


@dataclass
class _ExpandableBlock:
    """A piece of output that was shown collapsed; user can expand with ctrl+o."""
    title: str
    full_lines: List[str]
    preview_count: int  # how many lines were already shown
    consumed: bool = False


_EXPANDABLE_BLOCKS: Deque[_ExpandableBlock] = deque(maxlen=32)
_EXPAND_HINT = "ctrl+o to expand"


def _register_block(title: str, full_lines: List[str], preview_count: int) -> _ExpandableBlock:
    block = _ExpandableBlock(title=title, full_lines=full_lines, preview_count=preview_count)
    _EXPANDABLE_BLOCKS.append(block)
    return block


def has_pending_expansion() -> bool:
    return any(not b.consumed for b in _EXPANDABLE_BLOCKS)


def expand_pending(max_blocks: int = 4) -> int:
    """Print full contents for any unconsumed expandable blocks.

    Returns the number of blocks expanded. Bind this to ctrl+o.
    """
    count = 0
    for block in list(_EXPANDABLE_BLOCKS):
        if block.consumed:
            continue
        _console.print(f"  [dim]{CONT}[/dim]  [bold]{block.title}[/bold] [dim](expanded)[/dim]")
        for line in block.full_lines[block.preview_count:]:
            _console.print(f"  [dim]{CONT}[/dim]  [dim]{line}[/dim]")
        block.consumed = True
        count += 1
        if count >= max_blocks:
            break
    if count == 0:
        _console.print(f"  [dim]{CONT}[/dim]  [dim italic]Nothing to expand.[/dim italic]")
    return count


def cc_tool_output(tool_name: str, output: str, max_lines: int = 1000, max_chars: int = 100000) -> None:
    """Render a truncated tool output inline below the tool result line.

    Shows the first ``max_lines`` of output (up to ``max_chars`` total).
    If truncated, registers the full body for ctrl+o expansion and adds
    a ``(ctrl+o to expand)`` hint — same UX as Claude Code.
    """
    if not output or not output.strip():
        return

    clean = output.strip()
    full_lines = clean.split("\n")
    preview = full_lines

    truncated_by_chars = len(clean) > max_chars
    if truncated_by_chars:
        clipped = clean[:max_chars]
        preview = clipped.split("\n")

    truncated_by_lines = len(preview) > max_lines
    if truncated_by_lines:
        preview = preview[:max_lines]

    truncated = truncated_by_chars or truncated_by_lines

    for line in preview:
        _console.print(f"  [dim]{CONT}[/dim]  [dim]{line}[/dim]")

    if truncated:
        _register_block(title=f"{tool_name} output", full_lines=full_lines, preview_count=len(preview))
        remaining = max(0, len(full_lines) - len(preview))
        suffix = f"+{remaining} more line{'s' if remaining != 1 else ''} · " if remaining else ""
        _console.print(
            f"  [dim]{CONT}[/dim]  [dim italic]… ({suffix}{_EXPAND_HINT})[/dim italic]"
        )


def cc_agent_done(name: str, ok: bool = True) -> None:
    """Agent completion banner: ``● Agent "X" completed``."""
    color = "green" if ok else "red"
    verb = "completed" if ok else "failed"
    _console.print(f'[bold {color}]{BULLET}[/bold {color}] Agent "[bold]{name}[/bold]" {verb}')


def cc_tip(message: str) -> None:
    _console.print(f"  [dim]Tip:[/dim] [dim]{message}[/dim]")


def cc_divider(width: Optional[int] = None) -> None:
    w = width or _console.size.width
    _console.print("[dim]" + "─" * max(20, w - 2) + "[/dim]")


def cc_prompt_footer(context_hint: str = "", interrupt_hint: str = "esc to interrupt") -> None:
    """Render the bottom Claude-style input box.

    Used by interactive menus that want the same footer chrome as Claude Code.
    Returns nothing — it just paints chrome before ``Prompt.ask`` is called.
    """
    cc_divider()
    prompt_glyph = "❯" if _UNICODE_OK else ">"
    _console.print(f"[bold]{prompt_glyph}[/bold]  ")
    cc_divider()
    parts = []
    if interrupt_hint:
        parts.append(f"[dim]{interrupt_hint}[/dim]")
    if context_hint:
        parts.append(f"[dim]{CTX_GLYPH} {context_hint}[/dim]")
    if parts:
        _console.print("  " + "  ".join(parts))


@dataclass
class _SpinnerState:
    label: str
    started: float
    tokens: int = 0
    direction: str = "↓"
    stop: bool = False


class CCSpinner:
    """Animated `✢ Evaporating… (1m 57s · ↓ 4.1k tokens)` indicator.

    Usage::

        with cc_spinner("Evaporating") as s:
            ...work...
            s.add_tokens(1200)
    """

    def __init__(self, label: str = "Evaporating", direction: str = "↓"):
        self.state = _SpinnerState(label=label, started=time.time(), direction=direction)
        self._thread: Optional[threading.Thread] = None
        self._live: Optional[Live] = None

    def add_tokens(self, n: int) -> None:
        self.state.tokens += n

    def set_label(self, label: str) -> None:
        self.state.label = label

    def _render(self, frame: str) -> Text:
        t = Text()
        t.append(f"{frame} ", style="bold magenta")
        t.append(f"{self.state.label}… ", style="white")
        elapsed = _fmt_elapsed(time.time() - self.state.started)
        tok = _fmt_tokens(self.state.tokens)
        t.append(f"({elapsed} · {self.state.direction} {tok} tokens)", style="dim")
        return t

    def _loop(self) -> None:
        try:
            frames = itertools.cycle(SPIN_FRAMES)
            with Live(self._render(next(frames)), console=_console, refresh_per_second=8, transient=True) as live:
                self._live = live
                while not self.state.stop:
                    try:
                        live.update(self._render(next(frames)))
                    except BaseException:
                        pass
                    time.sleep(0.12)
        except BaseException:
            # Safely capture any low-level terminal or Win32 screen buffer errors to prevent CLI crashes
            pass

    def __enter__(self) -> "CCSpinner":
        global SUPPRESS_SPINNERS
        if SUPPRESS_SPINNERS:
            return self
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.state.stop = True
        if self._thread:
            self._thread.join(timeout=1.0)


@contextmanager
def cc_spinner(label: str = "Evaporating", direction: str = "↓") -> Iterator[CCSpinner]:
    sp = CCSpinner(label=label, direction=direction)
    with sp:
        yield sp


def cc_log_event(layer: str, event: str, status: str = "DONE") -> None:
    """Drop-in companion for ``log_event``: prints AND keeps the visual style."""
    color, glyph = _STATUS_STYLE.get(status.upper(), ("white", BULLET))
    ts = time.strftime("%H:%M:%S")
    _console.print(
        f"[bold {color}]{glyph}[/bold {color}] "
        f"[dim]{ts}[/dim] "
        f"[bold cyan]{layer}[/bold cyan] "
        f"[white]{event}[/white] "
        f"[dim]· {status}[/dim]"
    )


def cc_log_activity(module: str, task: str, status: str = "Completed") -> None:
    """Drop-in companion for ``log_activity``."""
    s = status.upper()
    color, glyph = _STATUS_STYLE.get(s, _STATUS_STYLE.get("DONE"))
    _console.print(
        f"[bold {color}]{glyph}[/bold {color}] "
        f"[bold]{module}[/bold] [white]{ARROW}[/white] {task} "
        f"[dim]({status})[/dim]"
    )


def cc_searched(patterns: int = 0, files_read: int = 0, hint: str = "", expandable: bool = False) -> None:
    """Composite helper: ``Searched for 2 patterns, read 1 file (ctrl+o to expand)``.

    Pass ``expandable=True`` (or call when there are pending blocks) to attach
    the ``ctrl+o to expand`` hint.
    """
    bits = []
    if patterns:
        bits.append(f"Searched for {patterns} pattern{'s' if patterns != 1 else ''}")
    if files_read:
        bits.append(f"read {files_read} file{'s' if files_read != 1 else ''}")
    summary = ", ".join(bits) if bits else "Working"
    effective_hint = hint
    if expandable or has_pending_expansion():
        effective_hint = f"{hint} · {_EXPAND_HINT}".strip(" ·") if hint else _EXPAND_HINT
    cc_tool_call(summary, hint=effective_hint)


def cc_file_list(paths: Iterable[str]) -> None:
    """Emit a stack of continuation lines for the given paths."""
    for p in paths:
        cc_result(p)


_CODE_VERB_COLOR = {
    "UPDATE":  "yellow",
    "EDIT":    "yellow",
    "WRITE":   "green",
    "CREATE":  "green",
    "ADD":     "green",
    "DELETE":  "red",
    "REMOVE":  "red",
    "RENAME":  "cyan",
    "READ":    "blue",
    "PATCH":   "magenta",
}


def cc_code_change(
    action: str,
    path: str,
    added: int = 0,
    removed: int = 0,
    note: str = "",
    diff_text: str = "",
) -> None:
    """Render a Claude-Code-style file-mutation banner with optional diffs.

    Example::

        cc_code_change("Update", "core.py", added=2, diff_text="+new_line\\n-old_line")
        # ● Update(core.py)
        #   ⎿  Added 2 lines
        #      +new_line
    """
    verb = action.strip().capitalize()
    color = _CODE_VERB_COLOR.get(verb.upper(), "yellow")
    short = os.path.basename(path) if os.sep in path or "/" in path else path
    _console.print(f"[bold {color}]{BULLET}[/bold {color}] [bold]{verb}[/bold]([cyan]{short}[/cyan])")

    bits = []
    if added:
        bits.append(f"[green]Added {added} line{'s' if added != 1 else ''}[/green]")
    if removed:
        bits.append(f"[red]Removed {removed} line{'s' if removed != 1 else ''}[/red]")
    if note:
        from rich.markup import escape
        bits.append(f"[dim]{escape(note)}[/dim]")
    
    if bits:
        _console.print(f"  [dim]{CONT}[/dim]  " + "  ".join(bits))
    
    if diff_text:
        import re
        lines = diff_text.strip("\n").split("\n")

        old_ln = 0
        new_ln = 0

        # Build each row as a Text object with explicit styles so code that
        # contains square brackets (Dict[str, Any], xs[0], …) is NOT parsed
        # as Rich markup — that was mangling and concatenating diff lines.
        for line in lines:
            if line.startswith("---") or line.startswith("+++"):
                continue

            if line.startswith("@@"):
                match = re.search(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if match:
                    old_ln = int(match.group(1))
                    new_ln = int(match.group(2))
                continue

            row = Text()
            if line.startswith("+"):
                row.append(f"{new_ln:>6} ", style="dim green")
                row.append("+ ", style="green")
                row.append(line[1:], style="green")
                new_ln += 1
            elif line.startswith("-"):
                row.append(f"{old_ln:>6} ", style="dim red")
                row.append("- ", style="red")
                row.append(line[1:], style="red")
                old_ln += 1
            else:
                # Unchanged context line (may start with a leading space).
                text = line[1:] if line.startswith(" ") else line
                row.append(f"{new_ln:>6} ", style="dim")
                row.append("  ")
                row.append(text, style="dim")
                old_ln += 1
                new_ln += 1
            _console.print(row)
        _console.print()


F = TypeVar("F", bound=Callable[..., Any])


def cc_menu(
    label: str,
    *,
    enter_status: str = "RUN",
    exit_status: str = "DONE",
    silent_exit: bool = True,
) -> Callable[[F], F]:
    """Decorator: announce a menu's entry/exit in Claude-Code style.

    Works on sync and async callables. Catches exceptions to print a
    red completion line, then re-raises.

    Example::

        @cc_menu("System Kernel")
        async def kernel_menu(): ...
    """

    def _wrap(fn: F) -> F:
        is_coro = inspect.iscoroutinefunction(fn)

        if is_coro:
            @functools.wraps(fn)
            async def _async(*args, **kwargs):
                t0 = time.time()
                try:
                    result = await fn(*args, **kwargs)
                except Exception as exc:
                    cc_action(f"{label} failed after {_fmt_elapsed(time.time() - t0)}: {exc}", status="ERROR")
                    raise
                return result
            return _async  # type: ignore[return-value]

        @functools.wraps(fn)
        def _sync(*args, **kwargs):
            t0 = time.time()
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                cc_action(f"{label} failed after {_fmt_elapsed(time.time() - t0)}: {exc}", status="ERROR")
                raise
            return result
        return _sync  # type: ignore[return-value]

    return _wrap


def cc_step(
    label: str,
    *,
    spinner: bool = True,
    spinner_label: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator: wrap a single step (sync or async) with an action line + spinner.

    The action line announces the step; if ``spinner=True`` a transient
    ``✢ {spinner_label}…`` spinner runs for the duration.
    """

    def _wrap(fn: F) -> F:
        is_coro = inspect.iscoroutinefunction(fn)
        sp_label = spinner_label or label

        if is_coro:
            @functools.wraps(fn)
            async def _async(*args, **kwargs):
                cc_action(label, status="RUN")
                if spinner:
                    with cc_spinner(sp_label):
                        return await fn(*args, **kwargs)
                return await fn(*args, **kwargs)
            return _async  # type: ignore[return-value]

        @functools.wraps(fn)
        def _sync(*args, **kwargs):
            cc_action(label, status="RUN")
            if spinner:
                with cc_spinner(sp_label):
                    return fn(*args, **kwargs)
            return fn(*args, **kwargs)
        return _sync  # type: ignore[return-value]

    return _wrap


def cc_engine_call(engine_name: str) -> Callable[[F], F]:
    """Decorator for an async LLM ``__call__``: prints a spinner + result line.

    The wrapped method emits:
        ``● {engine_name} → invoking…`` (via spinner)
        ``  ⎿  Response in 1.2s · 3.4k tokens``
    """

    def _wrap(fn: F) -> F:
        @functools.wraps(fn)
        async def _async(self, prompt: str, *args, **kwargs):
            label = getattr(self, "model", None) or getattr(self, "model_id", None) or engine_name
            t0 = time.time()
            with cc_spinner(f"{engine_name}:{label}") as sp:
                try:
                    result = await fn(self, prompt, *args, **kwargs)
                except Exception as exc:
                    cc_action(f"{engine_name} ({label}) errored: {exc}", status="ERROR")
                    raise
                tokens = len(str(result)) // 4 if result else 0
                sp.add_tokens(tokens)
            cc_result(
                f"{engine_name}:{label}",
                note=f"{_fmt_elapsed(time.time() - t0)} · ~{_fmt_tokens(tokens)} tokens",
            )
            return result
        return _async  # type: ignore[return-value]

    return _wrap


__all__ = [
    "cc_action",
    "cc_agent_done",
    "cc_code_change",
    "cc_divider",
    "cc_engine_call",
    "cc_file_list",
    "cc_log_activity",
    "cc_log_event",
    "cc_menu",
    "cc_prompt_footer",
    "cc_result",
    "cc_searched",
    "cc_spinner",
    "cc_step",
    "cc_tip",
    "cc_tool_call",
    "cc_tool_output",
    "CCSpinner",
    "expand_pending",
    "has_pending_expansion",
]
