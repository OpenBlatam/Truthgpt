"""
Swarm Intelligence Hub — Menu router and TUI entry point.

This module is the slim facade that ties together the submodules under
``interface.swarm.*``. All handler functions are re-exported here so
existing callers (e.g. ``from interface.swarm_menu import swarm_menu``)
continue to work without changes.
"""

import io
import logging
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from interface.core import (
    console, USER_PREFS, get_header, wait_for_user, get_input,
    get_theme_panel,
)

# ── Re-exports from submodules (backwards compatibility) ──────────

from interface.swarm.handlers import (                        # noqa: F401
    handle_swarm_ask,
    handle_swarm_telemetry,
    handle_persona_tuning,
    handle_expert_matrix,
    handle_mcp_connect,
    handle_math_verification,
    handle_agent_composer,
)
from interface.swarm.missions import (                        # noqa: F401
    handle_continuous_mission,
    handle_background_missions,
    BackgroundMission,
    wait_with_interrupt,
)
from interface.swarm.fusion import (                          # noqa: F401
    handle_swarm_fusion,
    execute_swarm_dispatch,
    save_code_blocks_to_directory,
    extract_filename_from_code,
    run_google_simulation,
    run_mcp_simulation,
)
from interface.swarm.inspector import (                       # noqa: F401
    swarm_phase_inspector,
    inspect_single_phase,
    view_and_edit_code,
    execute_sandbox_code,
    optimize_sandbox_code,
    safe_panel,
)

logger = logging.getLogger(__name__)

_client_cache = None


# ── Swarm Menu TUI (prompt_toolkit) ───────────────────────────────

class SwarmMenuApp:
    def __init__(self, active_agents):
        self.active_agents = active_agents
        self.selected_index = 0
        from prompt_toolkit.key_binding import KeyBindings
        self.kb = KeyBindings()
        self.result = None
        self._setup_keybindings()

        # Numeric keys for Active Experts
        for i in range(1, 10):
            @self.kb.add(str(i))
            def _(event, i=i):
                event.app.exit(result=str(i))

    def _setup_keybindings(self):
        @self.kb.add('q')
        @self.kb.add('c-c')
        @self.kb.add('0')
        @self.kb.add('escape')
        def _(event):
            event.app.exit(result="0")

        _hotkeys = {
            'a': 'A', 'f': 'F', 'b': 'B', 'm': 'M',
            's': 'S', 't': 'T', 'x': 'X', 'c': 'C', 'p': 'P',
        }
        for lower, val in _hotkeys.items():
            @self.kb.add(lower)
            @self.kb.add(lower.upper())
            def _(event, v=val):
                event.app.exit(result=v)

    def get_layout(self):
        from prompt_toolkit.application import get_app
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.formatted_text import ANSI
        from prompt_toolkit.layout.containers import Window, WindowAlign, HSplit
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.mouse_events import MouseEventType

        def set_choice(val):
            self.result = val
            get_app().exit(result=val)

        # Header
        header_console = Console(file=io.StringIO(), force_terminal=True, width=120)
        from interface.core import get_claude_header
        swarm_updates = [
            "Recursive Reasoning Enabled",
            "Expert Matrix Optimized",
            "Swarm Fusion Engine v2.4",
            "Latency: 12ms Cluster-Wide",
        ]
        header_console.print(get_claude_header(updates=swarm_updates))
        static_content = FormattedTextControl(ANSI(header_console.file.getvalue()))

        list_items = []

        def make_item(lid, name, val, index):
            def get_formatted_text():
                is_selected = self.selected_index == index
                style_prefix = "underline cyan" if is_selected else ""
                return [
                    ('class:dot', '             ● '),
                    ('class:id', f' {lid} '),
                    (f'class:name {style_prefix}', f' {name} '),
                ]

            def mouse_handler(mouse_event):
                if mouse_event.event_type == MouseEventType.MOUSE_MOVE:
                    self.selected_index = index
                elif mouse_event.event_type == MouseEventType.MOUSE_UP:
                    set_choice(val)

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
            list_items.append(Window(content=FormattedTextControl(ANSI(h_console.file.getvalue())), height=1))
            for i, agent in enumerate(self.active_agents):
                list_items.append(make_item(str(i + 1), agent.name, str(i + 1), 9 + i))

        list_items.append(Window(height=1))
        list_items.append(make_item("0", "🔙 Back to Kernel", "0", 20))

        # Footer
        footer_text = [
            ("class:prompt_seg", " ❯ SWARM HUB "),
            ("", " "),
            ("class:shortcut_seg", " ENTER "), ("class:shortcut_label", " Select "),
            ("class:shortcut_seg", " 0 "), ("class:shortcut_label", " Back "),
            ("", "  "),
            ("class:load_label", "SWARM LOAD: "), ("class:load_bar", "█▓▒░ 14%"),
            ("", "  "),
            ("class:version_seg", " Node: CLUSTER-7 "),
        ]

        return Layout(HSplit([
            Window(content=static_content, wrap_lines=True, ignore_content_height=True),
            HSplit(list_items),
            Window(height=1),
            Window(content=FormattedTextControl(footer_text), height=1),
        ]))

    async def run(self):
        from prompt_toolkit.styles import Style
        from prompt_toolkit.application import Application

        style = Style.from_dict({
            'dot': 'bold cyan', 'id': 'bold white', 'name': 'white',
            'prompt_seg': 'bg:magenta black bold',
            'shortcut_seg': 'bg:white black bold',
            'shortcut_label': 'white',
            'load_label': 'dim', 'load_bar': 'bold magenta',
            'version_seg': 'bg:#222222 dim',
        })
        app = Application(
            layout=self.get_layout(), key_bindings=self.kb,
            style=style, mouse_support=True, full_screen=True,
        )
        self.result = await app.run_async()
        return self.result


# ── Main Router ───────────────────────────────────────────────────

async def swarm_menu():
    """Top-level swarm hub loop — dispatches to the appropriate handler."""
    global _client_cache
    from agents.client import AgentClient
    from agents.engines import engine_registry

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
                console.print(Panel(
                    "[italic dim]Pensando... analizando contexto y seleccionando herramientas óptimas.[/italic dim]",
                    title="[bold plum1]Thinking[/bold plum1]",
                    border_style="plum1",
                ))
                response = await target.process(prompt, context={"user_id": "cli"})
                content = response.content if hasattr(response, "content") else str(response)
                console.print(get_theme_panel(content, title=f"🤖 {target.name} Response"))
                wait_for_user(force=True)
