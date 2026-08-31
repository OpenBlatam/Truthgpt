"""
Swarm Intelligence Hub — Menu router and TUI entry point.

This module is the slim facade that ties together the submodules under
``interface.swarm.*``. All handler functions are re-exported here so
existing callers (e.g. ``from interface.swarm_menu import swarm_menu``)
continue to work without changes.
"""
from __future__ import annotations

import io
import logging
from typing import Any, List, Optional

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.mouse_events import MouseEventType
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from interface.core import (
    USER_PREFS,
    console,
    get_claude_header,
    get_input,
    get_theme_panel,
    wait_for_user,
)
from interface.tui_base import BaseTUIApp

# ── Re-exports from submodules (backwards compatibility) ──────────

from interface.swarm.handlers import (  # noqa: F401
    handle_agent_composer,
    handle_expert_matrix,
    handle_math_verification,
    handle_mcp_connect,
    handle_persona_tuning,
    handle_swarm_ask,
    handle_swarm_telemetry,
)
from interface.swarm.missions import (  # noqa: F401
    BackgroundMission,
    handle_background_missions,
    handle_continuous_mission,
    wait_with_interrupt,
)
from interface.swarm.fusion import (  # noqa: F401
    execute_swarm_dispatch,
    extract_filename_from_code,
    handle_swarm_fusion,
    run_google_simulation,
    run_mcp_simulation,
    save_code_blocks_to_directory,
)
from interface.swarm.inspector import (  # noqa: F401
    execute_sandbox_code,
    inspect_single_phase,
    optimize_sandbox_code,
    safe_panel,
    swarm_phase_inspector,
    view_and_edit_code,
)

logger = logging.getLogger(__name__)

_client_cache: Optional[Any] = None


# ── Swarm Menu TUI (inheriting BaseTUIApp) ─────────────────────────

class SwarmMenuApp(BaseTUIApp):
    """Interactive Swarm Command Center TUI using prompt_toolkit + Rich."""

    def __init__(self, active_agents: Optional[List[Any]] = None) -> None:
        super().__init__()
        self.active_agents = active_agents or []

        # Register Swarm Hotkeys
        hotkeys = {
            "a": "A",
            "f": "F",
            "b": "B",
            "m": "M",
            "s": "S",
            "t": "T",
            "x": "X",
            "c": "C",
            "p": "P",
            "q": "0",
            "0": "0",
        }
        self.register_hotkeys(hotkeys)

        # Numeric keys for Active Experts
        for i in range(1, 10):

            @self.kb.add(str(i))
            def _(event, expert_idx=i):
                self.set_choice(str(expert_idx))

    def get_layout(self) -> Layout:
        # Header
        header_console = Console(file=io.StringIO(), force_terminal=True, width=120)
        swarm_updates = [
            "Recursive Reasoning Enabled",
            "Expert Matrix Optimized",
            "Swarm Fusion Engine v2.4",
            "Latency: 12ms Cluster-Wide",
        ]
        header_console.print(get_claude_header(updates=swarm_updates))
        static_content = FormattedTextControl(
            ANSI(header_console.file.getvalue()), show_cursor=False
        )

        list_items: List[Any] = []

        def make_item(lid: str, name: str, val: str, index: int) -> Window:
            def get_formatted_text():
                is_selected = self.selected_index == index
                style_prefix = "underline cyan" if is_selected else ""
                return [
                    ("class:dot", "             ● "),
                    ("class:id", f" {lid} "),
                    (f"class:name {style_prefix}", f" {name} "),
                ]

            def mouse_handler(mouse_event):
                if mouse_event.event_type == MouseEventType.MOUSE_MOVE:
                    self.selected_index = index
                elif mouse_event.event_type == MouseEventType.MOUSE_UP:
                    self.set_choice(val)

            content = FormattedTextControl(get_formatted_text, show_cursor=False)
            content.mouse_handler = mouse_handler
            return Window(content=content, height=1, align=WindowAlign.LEFT)

        # Swarm Commands
        list_items.append(Window(height=1))
        list_items.append(make_item("A", "📡 Ask Swarm (Auto-Routing)", "A", 0))
        list_items.append(make_item("F", "🌀 Dynamic Swarm Fusion", "F", 1))
        list_items.append(make_item("C", "⚡ Continuous Mission", "C", 2))
        list_items.append(make_item("B", "📡 Background Missions", "B", 3))
        list_items.append(make_item("M", "🔌 MCP Connectors", "M", 4))
        list_items.append(make_item("S", "📊 Swarm Status", "S", 5))
        list_items.append(make_item("T", "🧮 Math & Verification", "T", 6))
        list_items.append(make_item("X", "🏗️ Agent Composer", "X", 7))
        list_items.append(make_item("P", "🎭 Persona Tuning", "P", 8))

        # Active Experts
        if self.active_agents:
            list_items.append(Window(height=1))
            h_console = Console(file=io.StringIO(), force_terminal=True, width=100)
            h_console.print("  [bold white]ACTIVE EXPERTS[/bold white]")
            list_items.append(
                Window(
                    content=FormattedTextControl(
                        ANSI(h_console.file.getvalue()), show_cursor=False
                    ),
                    height=1,
                )
            )
            for i, agent in enumerate(self.active_agents):
                list_items.append(
                    make_item(str(i + 1), agent.name, str(i + 1), 9 + i)
                )

        list_items.append(Window(height=1))
        list_items.append(make_item("0", "🔙 Back to Kernel", "0", 20))

        # Footer
        footer_text = [
            ("class:prompt_seg", " ❯ SWARM HUB "),
            ("", " "),
            ("class:shortcut_seg", " ENTER "),
            ("class:shortcut_label", " Select "),
            ("class:shortcut_seg", " 0 "),
            ("class:shortcut_label", " Back "),
            ("", "  "),
            ("class:load_label", "SWARM LOAD: "),
            ("class:load_bar", "█▓▒░ 14%"),
            ("", "  "),
            ("class:version_seg", " Node: CLUSTER-7 "),
        ]

        return Layout(
            HSplit(
                [
                    Window(
                        content=static_content,
                        wrap_lines=True,
                        ignore_content_height=True,
                    ),
                    HSplit(list_items),
                    Window(height=1),
                    Window(content=FormattedTextControl(footer_text), height=1),
                ]
            )
        )

    def build_style(self, **overrides: Any):
        return super().build_style(
            prompt_seg="bg:magenta black bold",
            load_bar="bold magenta",
            **overrides,
        )


# ── Main Router ───────────────────────────────────────────────────

async def swarm_menu() -> None:
    """Top-level swarm hub loop — dispatches to the appropriate handler."""
    global _client_cache
    from agents.framework.interfaces.client.client import AgentClient
    from optimization_core.agents.framework.engines.engines import engine_registry

    if _client_cache is None:
        engine_name = USER_PREFS.get("preferred_engine", "deepseek")
        try:
            llm = engine_registry.get_engine(engine_name)
        except Exception:
            llm = None
        _client_cache = AgentClient(use_swarm=True, llm_engine=llm)
    client = _client_cache

    while True:
        active_agents = []
        if hasattr(client.swarm, "agents"):
            active_agents = list(client.swarm.agents.values())

        app = SwarmMenuApp(active_agents)
        choice = await app.run()

        if choice is None or choice == "0":
            break

        _dispatch = {
            "A": handle_swarm_ask,
            "C": handle_continuous_mission,
            "B": handle_background_missions,
            "F": handle_swarm_fusion,
            "M": handle_mcp_connect,
            "S": handle_swarm_telemetry,
            "T": handle_math_verification,
            "X": handle_agent_composer,
        }

        handler = _dispatch.get(choice)
        if handler:
            await handler()
        elif choice == "P":
            await handle_persona_tuning(active_agents)
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(active_agents):
                target = active_agents[idx - 1]
                prompt = get_input(f"Query {target.name}")
                console.print(
                    Panel(
                        "[italic dim]Thinking... selecting optimal tools and context.[/italic dim]",
                        title="[bold plum1]Thinking[/bold plum1]",
                        border_style="plum1",
                    )
                )
                response = await target.process(
                    prompt, context={"user_id": "cli"}
                )
                content = (
                    response.content
                    if hasattr(response, "content")
                    else str(response)
                )
                console.print(
                    get_theme_panel(content, title=f"🤖 {target.name} Response")
                )
                wait_for_user(force=True)
