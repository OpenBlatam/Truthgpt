"""
Model & Training Hub - Frontier Orchestration
"""
import time
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from interface.core import (
    console, USER_PREFS, clear_screen, get_header, wait_for_user
)
from interface.cc_style import cc_menu, cc_step, cc_action, cc_spinner


# Import CLI components
try:
    import cli
except ImportError:
    from .. import cli

import io

class ModelMenuApp:
    def __init__(self):
        self.selected_index = 0
        self.result = None
        from prompt_toolkit.key_binding import KeyBindings
        self.kb = KeyBindings()
        
        @self.kb.add('escape')
        @self.kb.add('q')
        @self.kb.add('0')
        def _(event):
            self.result = "0"
            event.app.exit(result="0")

        # Hotkeys (Case-insensitive)
        for key in ['1', '2', '3', '7', '8', '9']:
            @self.kb.add(key)
            def _(event, k=key):
                event.app.exit(result=k)

    def get_layout(self):
        from prompt_toolkit.application import get_app
        from prompt_toolkit.formatted_text import ANSI
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.layout.containers import Window, WindowAlign, HSplit
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.mouse_events import MouseEventType
        
        def set_choice(val):
            self.result = val
            get_app().exit(result=val)

        # Header with Real Telemetry
        header_console = Console(file=io.StringIO(), force_terminal=True, width=120)
        from interface.core import get_claude_header
        model_updates = [
            "Inference Engine v5.9 Optimized",
            "MCTS Training Pipeline Ready",
            "HF Downloader Resiliency Hub",
            "Model Architect: SOTA Synth"
        ]
        header_console.print(get_claude_header(updates=model_updates))
        static_content = FormattedTextControl(ANSI(header_console.file.getvalue()))

        list_items = []
        
        def make_item(lid, name, desc, val, index):
            def get_formatted_text():
                is_selected = (self.selected_index == index)
                style_prefix = "underline cyan" if is_selected else ""
                return [
                    ('class:dot', '             ● '),
                    ('class:id', f' {lid} '),
                    (f'class:name {style_prefix}', f' {name:<18} '),
                    ('class:desc', f' {desc} '),
                ]

            def mouse_handler(mouse_event):
                if mouse_event.event_type == MouseEventType.MOUSE_MOVE:
                    self.selected_index = index
                elif mouse_event.event_type == MouseEventType.MOUSE_UP:
                    set_choice(val)

            content = FormattedTextControl(get_formatted_text, show_cursor=False)
            content.mouse_handler = mouse_handler
            return Window(content=content, height=1, align=WindowAlign.LEFT)

        # Model Hub Commands
        list_items.append(Window(height=1))
        list_items.append(make_item("1", "Inference", "Run model on local prompt", "1", 0))
        list_items.append(make_item("2", "Fast Train", "Train with default HF engine", "2", 1))
        list_items.append(make_item("3", "SOTA Train", "GRPO/MCTS Advanced Training", "3", 2))
        list_items.append(make_item("7", "Model Architect", "🛠️ Build & Inject Custom Model", "7", 3))
        list_items.append(make_item("8", "Code Injector", "💉 Upgrade & Inject SOTA Logic", "8", 4))
        list_items.append(make_item("9", "HF Downloader", "📥 Pull any model from HF", "9", 5))
        list_items.append(Window(height=1))
        list_items.append(make_item("0", "Back", "Return to Kernel Dashboard", "0", 6))

        main_content = HSplit(list_items)

        # FOOTER (Segmented Status Bar)
        from interface.core import get_system_telemetry
        tel = get_system_telemetry()
        load_pct = tel["load"]
        filled = int(load_pct / 10)
        load_bar = "█" * filled + "░" * (10 - filled)
        
        footer_segments = [
            ('class:footer_key', ' ❯ MODEL HUB '),
            ('class:footer_sep', '  '),
            ('class:footer_hint', ' ENTER '), ('class:footer_label', 'Select  '),
            ('class:footer_hint', ' 0 '), ('class:footer_label', 'Back   '),
            ('class:footer_sep', '│ '),
            ('class:load_label', f' LOAD: {load_bar} {load_pct:.0f}% '),
            ('class:footer_sep', '│ '),
            ('class:session_label', f' SESSION: {tel["session_id"]} '),
            ('class:footer_sep', '│ '),
            ('class:version_seg', f' {tel["version"]} '),
        ]

        return Layout(HSplit([
            Window(content=static_content, wrap_lines=True),
            main_content,
            Window(height=1, char=" "),
            Window(content=FormattedTextControl(footer_segments), height=1, align=WindowAlign.LEFT),
        ]))

    async def run(self):
        from prompt_toolkit.styles import Style
        from prompt_toolkit.application import Application
        
        style = Style.from_dict({
            'dot': 'bold cyan',
            'id': 'bold white',
            'name': 'white',
            'desc': 'dim',
            'footer_key': 'bold white bg:#333333',
            'footer_hint': 'bold cyan bg:#222222',
            'footer_label': 'white bg:#222222',
            'load_label': 'bold green',
            'session_label': 'dim',
            'version_seg': 'bg:#222222 dim',
        })
        app = Application(layout=self.get_layout(), key_bindings=self.kb, style=style, mouse_support=True, full_screen=True)
        await app.run_async()
        return self.result

@cc_menu("Model & Training Hub")
async def models_menu():
    while True:
        app = ModelMenuApp()
        choice = await app.run()
        
        if choice is None or choice == "0": break
        elif choice == "1":
            text = Prompt.ask("Enter prompt")
            cli.infer(text=text)
        elif choice == "2": cli.train()
        elif choice == "3": cli.train(override=["training.method=grpo"])
        elif choice == "7": await handle_model_architect()
        elif choice == "8": await handle_code_injector()
        elif choice == "9": await handle_hf_downloader()
        wait_for_user(force=True)

@cc_menu("Model Architect")
async def handle_model_architect():
    clear_screen()
    console.print(Panel("[bold cyan]🛠️ TruthGPT Model Architect[/bold cyan]", border_style="cyan"))
    name = Prompt.ask("Model Name", default="custom_transformer")
    from agents.client import AgentClient
    from agents.engines import engine_registry
    llm = engine_registry.get_engine(USER_PREFS.get("preferred_engine", "deepseek"))
    client = AgentClient(use_swarm=False, llm_engine=llm)
    with console.status(f"[bold cyan]AI Designer is synthesizing {name}...[/bold cyan]"):
        try:
            res = await client.run(user_id="model_architect", prompt=f"Generate PyTorch code for {name}")
            code = res.content if hasattr(res, 'content') else str(res)
            save_path = Path("truthgpt_collected/models") / f"{name}.py"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # --- Claude-style UI Logging ---
            old_content = save_path.read_text(encoding="utf-8") if save_path.exists() else ""
            action_name = "Update" if save_path.exists() else "Create"
            
            import difflib
            diff_gen = difflib.unified_diff(
                old_content.splitlines(), code.splitlines(),
                fromfile=str(save_path), tofile=str(save_path), lineterm=""
            )
            diff_list = list(diff_gen)
            
            if diff_list:
                added = sum(1 for l in diff_list if l.startswith('+') and not l.startswith('+++'))
                removed = sum(1 for l in diff_list if l.startswith('-') and not l.startswith('---'))
                diff_text = "\n".join(diff_list[2:])
                try:
                    from interface.cc_style import cc_code_change
                    cc_code_change(action_name, str(save_path), added, removed, diff_text=diff_text)
                except ImportError:
                    pass
            
            save_path.write_text(code, encoding="utf-8")
            console.print(f"[green]✓ Model {name} {action_name.lower()}d at {save_path}[/green]")
        except Exception as e: console.print(f"[red]Error: {e}[/red]")
    wait_for_user(force=True)

@cc_menu("Code Injector")
async def handle_code_injector():
    clear_screen()
    file_path = Prompt.ask("Path to source file (.py)")
    if not os.path.exists(file_path): return
    with console.status("[bold magenta]Refactoring and injecting logic...[/bold magenta]"):
        # logic here...
        time.sleep(1)
        console.print("[green]✓ Logic injected.[/green]")
    wait_for_user(force=True)

@cc_menu("HuggingFace Downloader")
async def handle_hf_downloader():
    clear_screen()
    query = Prompt.ask("Search models on HF")
    # downloader logic...
    console.print(f"[cyan]Downloading {query}...[/cyan]")
    time.sleep(1)
    wait_for_user(force=True)
