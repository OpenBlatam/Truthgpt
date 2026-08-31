"""
Interactive Dashboard — Main kernel dashboard TUI.

Refactored to use BaseTUIApp for shared keybinding/styling logic.
"""

import io
import shutil

from rich.console import Console
from prompt_toolkit.application import get_app
from prompt_toolkit.layout.containers import VSplit, HSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Button, Box, Shadow, TextArea
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.mouse_events import MouseEventType

from interface.core import (
    console as rich_console, USER_PREFS, get_header, get_system_telemetry,
)
from interface.cc_style import cc_action, cc_divider
from interface.tui_base import BaseTUIApp


class InteractiveDashboardApp(BaseTUIApp):
    def __init__(self, extended=True):
        super().__init__()
        self.extended = extended

        # Persistent command input area
        self.command_input = TextArea(
            multiline=False,
            prompt=' ❯ ',
            style='class:command_input',
            accept_handler=self._on_accept,
        )

        # Extra keybinding: Ctrl+O to expand pending
        @self.kb.add('c-o')
        def _(event):
            try:
                from interface.cc_style import expand_pending
                event.app.run_in_terminal(lambda: expand_pending())
            except Exception:
                pass

    def _on_accept(self, buffer):
        text = buffer.document.text.strip()
        if text:
            self.result = text
            get_app().exit(result=text)

    def render_rich_content(self):
        c = self.reset_console()
        c.print(get_header())

        if self.is_claude_theme():
            c.print()
            return self.render_rich_to_ansi()

        c.print(f" [dim]System Status: [bold green]ONLINE[/bold green] | Mode: {'Extended' if self.extended else 'Standard'}[/dim]")
        c.print("[dim]────────────────────────────────────────────────────────────────────────────────[/dim]")
        return self.render_rich_to_ansi()

    def get_layout(self):
        theme = self.current_theme()

        if self.is_claude_theme():
            main_content = self._build_claude_menu()
        else:
            main_content = self._build_grid_menu()

        static_content = FormattedTextControl(
            text=self.render_rich_content,
            show_cursor=False,
            modal=True,
        )

        footer_control = FormattedTextControl(self._get_footer_text)

        root_container = HSplit([
            Window(content=static_content, wrap_lines=True, ignore_content_height=True),
            main_content,
            Window(height=1, char=" "),
            Window(height=1, char="─", style="class:dim"),
            self.command_input,
            Window(height=1, char="─", style="class:dim"),
            Window(height=1, char=" "),
            Window(content=footer_control, height=1, align=WindowAlign.LEFT),
        ], align=WindowAlign.LEFT)

        if self.is_claude_theme():
            return Layout(root_container, focused_element=self.command_input)
        return Layout(Shadow(Box(root_container, padding=1)), focused_element=self.command_input)

    # ── Menu Builders ─────────────────────────────────────────────

    def _build_claude_menu(self):
        """Claude-style minimalist vertical list."""
        list_items = []

        def make_item(lid, name, val, index):
            def mouse_handler(mouse_event):
                if mouse_event.event_type == MouseEventType.MOUSE_MOVE:
                    self.selected_index = index
                elif mouse_event.event_type == MouseEventType.MOUSE_UP:
                    self.selected_index = index
                    self.set_choice(val)

            content = FormattedTextControl(
                [
                    ('class:dot', ' ' * 12 + ' * '),
                    ('class:id', f'{lid:>2} '),
                    ('class:name', f' {name}'),
                ],
                focusable=True,
                show_cursor=False,
            )
            content.mouse_handler = mouse_handler
            return Window(content=content, height=1, cursorline=True, align=WindowAlign.LEFT)

        list_items.append(make_item("K", "🛡️ Kernel", "0", 0))
        list_items.append(make_item("1", "🐝 Swarm", "1", 1))
        list_items.append(make_item("2", "🚀 Frontier", "2", 2))
        list_items.append(make_item("3", "🔍 Research", "3", 3))

        if self.extended:
            list_items.append(Window(height=1, char=" "))
            list_items.append(Window(height=1))
            list_items.append(make_item("4", "⚙️ Opts", "4", 4))
            list_items.append(make_item("5", "🧠 Labs", "5", 5))
            list_items.append(make_item("6", "📱 Comm", "6", 6))
            list_items.append(make_item("9", "⛓️ Web3", "9", 7))
            list_items.append(make_item("10", "🖥️ Node", "10", 8))
            list_items.append(make_item("H", "📜 History", "h", 9))
            list_items.append(make_item("P", "👤 Settings", "p", 10))

        list_items.append(Window(height=1))
        list_items.append(make_item("99", "➕ Toggle View", "99", 11))
        list_items.append(make_item("R", "🔄 Reboot", "reboot", 13))
        list_items.append(make_item("X", "🚪 Exit", "exit", 12))

        return HSplit(list_items)

    def _build_grid_menu(self):
        """Original industrial button grid."""
        def make_btn(text, val, width=22):
            return Button(text, handler=lambda: self.set_choice(val), width=width)

        core_row = VSplit([
            make_btn("K: 🛡️ Kernel", "0"),
            make_btn("1: 🐝 Swarm", "1"),
            make_btn("2: 🚀 Frontier", "2"),
            make_btn("3: 🔍 Research", "3"),
        ], padding=2, align=WindowAlign.CENTER)

        rows = [core_row]
        if self.extended:
            rows.append(VSplit([make_btn("4: ⚙️ Opts", "4"), make_btn("5: 🧠 Labs", "5"), make_btn("6: 📱 Comm", "6"), make_btn("9: ⛓️ Web3", "9")], padding=2, align=WindowAlign.CENTER))
            rows.append(VSplit([make_btn("10: 🖥️ Node", "10"), make_btn("11: 📊 Tasks", "11"), make_btn("13: 📊 Market", "13"), make_btn("15: 🤖 RL", "15")], padding=2, align=WindowAlign.CENTER))
            rows.append(VSplit([make_btn("16: ⚡ Overdrive", "16"), make_btn("P: 👤 Settings", "p"), make_btn("R: 🔄 Reboot", "reboot"), make_btn("99: ➕ Toggle View", "99"), make_btn("X: 🚪 Exit", "exit")], padding=1, align=WindowAlign.CENTER))
        else:
            rows.append(VSplit([make_btn("R: 🔄 Reboot", "reboot"), make_btn("99: ➕ Extended View", "99"), make_btn("X: 🚪 Exit", "exit")], padding=2))

        return HSplit(rows, padding=1)

    # ── Footer ────────────────────────────────────────────────────

    def _get_footer_text(self):
        tel = get_system_telemetry()
        load_pct = tel["load"]
        filled = int(load_pct / 10)
        load_bar = "█" * filled + "░" * (10 - filled)

        try:
            from interface.cc_style import has_pending_expansion
            expand_active = has_pending_expansion()
        except Exception:
            expand_active = False

        return [
            ('class:footer_key', ' ❯ COMMAND INPUT '),
            ('class:footer_sep', '  '),
            ('class:footer_hint', ' ENTER '),
            ('class:footer_label', 'Submit  '),
            ('class:footer_hint', ' ESC '),
            ('class:footer_label', 'Exit  '),
            ('class:footer_hint' if expand_active else 'class:footer_sep', ' CTRL+O '),
            ('class:footer_label', 'Expand   ' if expand_active else 'Expand (no pending)   '),
            ('class:footer_sep', '│ '),
            ('class:load_label', f' LOAD: {load_bar} {load_pct:.0f}% '),
            ('class:footer_sep', '│ '),
            ('class:session_label', f' SESSION: {tel["session_id"]} '),
            ('class:footer_sep', '│ '),
            ('class:version_seg', f' {tel["version"]} '),
        ]


async def get_dashboard_choice(extended=True):
    app = InteractiveDashboardApp(extended=extended)
    return await app.run()
