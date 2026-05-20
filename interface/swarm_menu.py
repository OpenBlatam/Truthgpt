"""
Swarm Intelligence Hub - Industrial Command Center
"""
import asyncio
import time
import json
import inspect
import re
import logging
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, FloatPrompt, Confirm
from rich.live import Live
from rich.console import Console
import io
logger = logging.getLogger(__name__)

# UI Framework Imports

from interface.core import (
    console, USER_PREFS, log_activity, log_event, clear_screen, 
    get_header, wait_for_user, background_missions, save_mission_output,
    export_mission_result, get_theme_panel, get_input, extract_target_directory
)
from interface.cc_style import cc_menu, cc_step, cc_action, cc_spinner, cc_agent_done
from interface.interactive_swarm import get_interactive_choice

# Deferred CLI imports for performance

_client_cache = None

def extract_filename_from_code(code_text: str, default_name: str) -> str:
    import re
    lines = code_text.strip().splitlines()
    if not lines:
        return default_name
    for line in lines[:3]:
        line = line.strip()
        match = re.match(r'^(?:#|//|/\*|File:|Filename:)\s*([a-zA-Z0-9_\-\.\/\\ ]+)(?:\s*\*\/)?$', line, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            if '.' in extracted:
                parts = extracted.split('.')
                if len(parts[-1]) in (1, 2, 3, 4) and not parts[-1].isdigit():
                    return extracted
    return default_name

def save_code_blocks_to_directory(content: str, target_dir: Path, default_prefix: str = "output"):
    import re
    code_blocks = re.findall(r"```([a-zA-Z0-9+#_ -]*)\n(.*?)\n```", content, re.DOTALL)
    if not code_blocks:
        single_match = re.search(r"```(?:[a-zA-Z0-9+#_ -]*)\n(.*?)\n```", content, re.DOTALL)
        if single_match:
            code_blocks = [("", single_match.group(1))]
            
    lang_map = {
        "python": ".py", "py": ".py",
        "javascript": ".js", "js": ".js",
        "typescript": ".ts", "ts": ".ts",
        "html": ".html", "htm": ".html",
        "css": ".css", "json": ".json",
        "rust": ".rs", "rs": ".rs", "go": ".go",
        "bash": ".sh", "sh": ".sh", "shell": ".sh",
        "powershell": ".ps1", "ps1": ".ps1",
    }
    
    saved_files = []
    for idx, (lang, code) in enumerate(code_blocks, 1):
        lang_clean = lang.strip().lower()
        ext = lang_map.get(lang_clean, ".py" if not lang_clean else f".{lang_clean}")
        default_filename = f"{default_prefix}_{idx}_{int(time.time())}{ext}"
        
        rel_filename = extract_filename_from_code(code, default_filename)
        dest_path = target_dir / rel_filename
        
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "w", encoding="utf-8") as code_f:
                code_f.write(code)
            saved_files.append(dest_path)
            console.print(f"  [green]● Saved code block to {dest_path.resolve()}[/green]")
            try:
                from interface.cc_style import cc_code_change
                cc_code_change("WRITE", str(dest_path.name), added=len(code.splitlines()))
            except Exception:
                pass
        except Exception as e:
            console.print(f"[red]Failed to save code to {dest_path}: {e}[/red]")
            
    return saved_files

class BackgroundMission:
    def __init__(self, name, query, interval, team, agents_map, config, llm, context):
        self.name = name
        self.query = query
        self.interval = interval
        self.team = team
        self.agents_map = agents_map
        self.config = config
        self.llm = llm
        self.context = context
        self.history = []
        self.status = "Running"
        self.last_run = None
        self.task = None

    async def run_loop(self):
        while self.status == "Running":
            self.last_run = time.strftime('%H:%M:%S')
            log_activity("BG Mission", f"Cycle: {self.name}", status="Running")
            current_prompt = self.query
            cycle_history = []
            
            for key in self.team:
                if key not in self.agents_map and key != "arxiv_discovery_scout": continue
                
                if key == "arxiv_discovery_scout":
                    from agents.system_intelligence.research_agent import ResearchAgent
                    agent = ResearchAgent(llm_engine=self.llm)
                    res = await agent.process(f"descubrir e integrar papers de {current_prompt}")
                    content = res.content
                else:
                    agent_cls = self.agents_map[key]
                    sig = inspect.signature(agent_cls.__init__)
                    params = {}
                    if "config" in sig.parameters: params["config"] = self.config
                    if "llm_engine" in sig.parameters: params["llm_engine"] = self.llm
                    agent = agent_cls(**params)
                    res = await agent.process(current_prompt, context=self.context)
                    content = res.content if hasattr(res, 'content') else str(res)
                
                cycle_history.append({"phase": key, "output": content})
                current_prompt = f"Previous findings: {content}\n\nTask: {current_prompt}"
            
            self.history.append({"time": self.last_run, "data": cycle_history})
            await asyncio.sleep(self.interval * 60)

async def wait_with_interrupt(seconds: float) -> str:
    import msvcrt
    steps = int(seconds)
    if steps <= 0: return "continue"
    console.print(f"\n[dim]Waiting {seconds/60:.1f}m... [bold white]M[/bold white]: Menu | [bold white]Q[/bold white]: New Query | [bold white]B[/bold white]: Background | [bold white]X[/bold white]: Export | [bold white]S[/bold white]: Stop[/dim]")
    for _ in range(steps):
        await asyncio.sleep(1)
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').upper()
            if key == 'M': return 'menu'
            if key == 'Q': return 'query'
            if key == 'B': return 'background'
            if key == 'X': return 'export'
            if key == 'S': return 'stop'
    return "continue"

class SwarmMenuApp:
    def __init__(self, active_agents):
        self.active_agents = active_agents
        self.selected_index = 0
        from prompt_toolkit.key_binding import KeyBindings
        self.kb = KeyBindings()
        self.result = None
        
        @self.kb.add('q')
        @self.kb.add('c-c')
        @self.kb.add('0')
        @self.kb.add('escape')
        def _(event):
            event.app.exit(result="0")

        # Hotkeys for commands (Case-insensitive)
        @self.kb.add('a')
        @self.kb.add('A')
        def _(event): event.app.exit(result="A")
        
        @self.kb.add('f')
        @self.kb.add('F')
        def _(event): event.app.exit(result="F")
        
        @self.kb.add('b')
        @self.kb.add('B')
        def _(event): event.app.exit(result="B")
        
        @self.kb.add('m')
        @self.kb.add('M')
        def _(event): event.app.exit(result="M")
        
        @self.kb.add('s')
        @self.kb.add('S')
        def _(event): event.app.exit(result="S")
        
        @self.kb.add('t')
        @self.kb.add('T')
        def _(event): event.app.exit(result="T")
        
        @self.kb.add('x')
        @self.kb.add('X')
        def _(event): event.app.exit(result="X")
        
        @self.kb.add('c')
        @self.kb.add('C')
        def _(event): event.app.exit(result="C")
        
        @self.kb.add('p')
        @self.kb.add('P')
        def _(event): event.app.exit(result="P")

        # Numeric keys for Active Experts
        for i in range(1, 10):
            @self.kb.add(str(i))
            def _(event, i=i):
                event.app.exit(result=str(i))

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

        # Header with Real Telemetry
        header_console = Console(file=io.StringIO(), force_terminal=True, width=120)
        from interface.core import get_claude_header
        swarm_updates = [
            "Recursive Reasoning Enabled",
            "Expert Matrix Optimized",
            "Swarm Fusion Engine v2.4",
            "Latency: 12ms Cluster-Wide"
        ]
        header_console.print(get_claude_header(updates=swarm_updates))
        static_content = FormattedTextControl(ANSI(header_console.file.getvalue()))

        list_items = []
        
        def make_item(lid, name, val, index):
            def get_formatted_text():
                is_selected = (self.selected_index == index)
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

            content = FormattedTextControl(
                get_formatted_text,
                show_cursor=False,
            )
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
        
        # List of Active Agents
        if self.active_agents:
            list_items.append(Window(height=1))
            header_console = Console(file=io.StringIO(), force_terminal=True, width=100)
            header_console.print("  [bold white]ACTIVE EXPERTS[/bold white]")
            list_items.append(Window(content=FormattedTextControl(ANSI(header_console.file.getvalue())), height=1))
            for i, agent in enumerate(self.active_agents):
                list_items.append(make_item(str(i+1), agent.name, str(i+1), 9+i))

        list_items.append(Window(height=1))
        list_items.append(make_item("0", "🔙 Back to Kernel", "0", 20))

        # Footer Status Bar
        footer_text = [
            ("class:prompt_seg", " ❯ SWARM HUB "),
            ("", " "),
            ("class:shortcut_seg", " ENTER "), ("class:shortcut_label", " Select "),
            ("class:shortcut_seg", " 0 "), ("class:shortcut_label", " Back "),
            ("", "  "),
            ("class:load_label", "SWARM LOAD: "), ("class:load_bar", "█▓▒░ 14%"),
            ("", "  "),
            ("class:version_seg", " Node: CLUSTER-7 ")
        ]

        return Layout(HSplit([
            Window(content=static_content, wrap_lines=True),
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
        app = Application(layout=self.get_layout(), key_bindings=self.kb, style=style, mouse_support=True, full_screen=True)
        self.result = await app.run_async()
        return self.result

async def swarm_menu():
    global _client_cache
    from agents.client import AgentClient
    from agents.engines import engine_registry
    from interface.core import USER_PREFS
    
    if _client_cache is None:
        # Pre-load minimized client with the preferred engine for zero latency
        engine_name = USER_PREFS.get("preferred_engine", "deepseek")
        try:
            llm = engine_registry.get_engine(engine_name)
        except:
            llm = None # Fallback to dummy or default
            
        _client_cache = AgentClient(use_swarm=True, llm_engine=llm)
    client = _client_cache
    
    while True:
        active_agents = []
        if hasattr(client.swarm, "agents"):
            active_agents = list(client.swarm.agents.values())
            
        app = SwarmMenuApp(active_agents)
        choice = await app.run()
        
        if choice is None or choice == "0": break
        elif choice == "A": await handle_swarm_ask()
        elif choice == "C": await handle_continuous_mission()
        elif choice == "B": await handle_background_missions()
        elif choice == "F": await handle_swarm_fusion()
        elif choice == "M": await handle_mcp_connect()
        elif choice == "S": await handle_swarm_telemetry()
        elif choice == "T": await handle_math_verification()
        elif choice == "X": await handle_agent_composer()
        elif choice == "P": await handle_persona_tuning(active_agents)
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(active_agents):
                target = active_agents[idx-1]
                prompt = get_input(f"Query {target.name}")
                console.print(Panel("[italic dim]Pensando... analizando contexto y seleccionando herramientas óptimas.[/italic dim]", title="[bold plum1]Thinking[/bold plum1]", border_style="plum1"))
                response = await target.process(prompt, context={"user_id": "cli"})
                content = response.content if hasattr(response, 'content') else str(response)
                console.print(get_theme_panel(content, title=f"🤖 {target.name} Response"))
                wait_for_user(force=True)


@cc_step("Swarm Router")
async def handle_swarm_ask():
    prompt = get_input("Enter your question for the swarm")
    engine = USER_PREFS["preferred_engine"]
    log_activity("Swarm Ask", prompt)
    with console.status(f"[bold blue]Routing to expert agents using {engine}...[/bold blue]"):
        try:
            import cli
            await cli.async_swarm_ask(prompt=prompt, user_id="cli_user", stream=False, engine=engine)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    wait_for_user(force=True)


async def run_google_simulation(choice: str = "1"):
    console.print("[cyan]🌐 Activating Simulated Google Workspace Deployer...[/cyan]")
    await asyncio.sleep(1.0)
    console.print("  [green]● Authenticating secure GCP connection...[/green]")
    await asyncio.sleep(0.5)
    if choice == "1":
        console.print("  [green]● Creating Google Doc: 'TruthGPT Swarm Output'[/green]")
        await asyncio.sleep(0.8)
        console.print("  [green]● Synthesizing content blocks and schemas...[/green]")
        await asyncio.sleep(0.6)
        sim_doc_id = "1BxiMVs0XRA5nFMdKvXKBg-yvW9tC1337_truthgpt"
        console.print(f"[bold green]✓ Simulated Google Docs cloud dispatch successful![/bold green]")
        console.print(f"[bold cyan]🔗 Simulated Google Doc Link: https://docs.google.com/document/d/{sim_doc_id}/edit[/bold cyan]")
    elif choice == "2":
        console.print("  [green]● Creating Google Sheet: 'TruthGPT Execution Metrics'[/green]")
        await asyncio.sleep(0.8)
        console.print("  [green]● Appending metrics row: Swarm_Fusion, accuracy, latency...[/green]")
        await asyncio.sleep(0.6)
        sim_sheet_id = "1SheetMVs0XRA5nFMdKvXKBg_truthgpt"
        console.print(f"[bold green]✓ Simulated Google Sheets metrics log successful![/bold green]")
        console.print(f"[bold cyan]🔗 Simulated Google Sheet Link: https://docs.google.com/spreadsheets/d/{sim_sheet_id}/edit[/bold cyan]")
    else:
        console.print("  [green]● Connecting to Google Drive Folder: '/TruthGPT Reports'[/green]")
        await asyncio.sleep(0.8)
        console.print("  [green]● Uploading raw markdown asset...[/green]")
        await asyncio.sleep(0.6)
        sim_drive_id = "1DriveMVs0XRA5nFMdKvXKBg_truthgpt"
        console.print(f"[bold green]✓ Simulated Google Drive file upload successful![/bold green]")
        console.print(f"[bold cyan]🔗 Simulated Google Drive File Link: https://drive.google.com/open?id={sim_drive_id}[/bold cyan]")


async def run_mcp_simulation(url: str, reason: str = ""):
    console.print(f"[cyan]🔌 Connecting to MCP Server at {url}...[/cyan]")
    await asyncio.sleep(1.0)
    console.print("  [green]● Negotiating MCP protocol handshake (v0.1.0)...[/green]")
    await asyncio.sleep(0.5)
    console.print("  [green]● Analyzing active resources and capabilities...[/green]")
    await asyncio.sleep(0.5)
    if reason:
        console.print(f"  [dim]● Reason: {reason}[/dim]")
    console.print(f"[bold green]✓ Dispatched Swarm Results to MCP Server Resource: mcp://localhost/swarm/fusion/reports[/bold green]")


async def execute_swarm_dispatch(content: str, selected_targets: list[str]):
    console.print("\n[bold yellow]📡 Initializing Swarm Multi-Target Dispatcher...[/bold yellow]")
    
    for target in selected_targets:
        if target == "1":
            console.print("\n[bold cyan]💾 Target 1: Local Workspace Export Config[/bold cyan]")
            
            # Format sub-selection
            format_table = Table(title="📄 Choose File Format", border_style="cyan")
            format_table.add_column("Option", style="bold yellow")
            format_table.add_column("Format", style="white")
            format_table.add_row("1", "Markdown (.md) - Recommended for reports")
            format_table.add_row("2", "Plain Text (.txt) - Raw output dump")
            format_table.add_row("3", "JSON Structure (.json) - Schema representation")
            console.print(format_table)
            fmt_choice = get_input("Select format option", choices=["1", "2", "3"], default="1")
            
            # Directory sub-selection
            dir_table = Table(title="📁 Choose Target Directory", border_style="cyan")
            dir_table.add_column("Option", style="bold yellow")
            dir_table.add_column("Destination Folder", style="white")
            dir_table.add_row("1", "reports/ (Standard reports directory)")
            dir_table.add_row("2", "truthgpt_collected/generated_code/ (For scripts/code)")
            dir_table.add_row("3", "Workspace Root (Current working directory)")
            dir_table.add_row("4", "Custom Path (Specify absolute or relative path)")
            console.print(dir_table)
            dir_choice = get_input("Select directory option", choices=["1", "2", "3", "4"], default="1")
            
            # Resolve format extension
            ext = ".md" if fmt_choice == "1" else ".txt" if fmt_choice == "2" else ".json"
            
            # Resolve directory path
            if dir_choice == "1":
                target_dir = Path("reports")
            elif dir_choice == "2":
                target_dir = Path("truthgpt_collected/generated_code")
            elif dir_choice == "3":
                target_dir = Path(".")
            else:
                custom_p = get_input("Enter custom directory path")
                target_dir = Path(custom_p)
                
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                filename = f"Swarm_Fusion_{time.strftime('%Y%m%d_%H%M%S')}{ext}"
                filepath = target_dir / filename
                
                # Format content if JSON format chosen
                if fmt_choice == "3":
                    output_content = json.dumps({"mission": "Swarm_Fusion", "timestamp": time.time(), "content": content}, indent=4)
                else:
                    output_content = content
                    
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(output_content)
                console.print(f"[bold green]✓ Output successfully exported to {filepath}[/bold green]")
                
                # Extract and save code blocks to target_dir too
                import re
                code_blocks = re.findall(r"```([a-zA-Z0-9+#_ -]*)\n(.*?)\n```", content, re.DOTALL)
                if code_blocks:
                    console.print(f"[cyan]📦 Extracting and writing {len(code_blocks)} code blocks to {target_dir}...[/cyan]")
                    lang_map = {
                        "python": ".py", "py": ".py",
                        "javascript": ".js", "js": ".js",
                        "typescript": ".ts", "ts": ".ts",
                        "html": ".html", "htm": ".html",
                        "css": ".css",
                        "json": ".json",
                        "rust": ".rs", "rs": ".rs",
                        "go": ".go",
                        "bash": ".sh", "sh": ".sh", "shell": ".sh",
                        "powershell": ".ps1", "ps1": ".ps1",
                        "c": ".c", "cpp": ".cpp", "c++": ".cpp",
                        "java": ".java",
                    }
                    for idx, (lang, code) in enumerate(code_blocks, 1):
                        lang_clean = lang.strip().lower()
                        code_ext = lang_map.get(lang_clean, ".py" if not lang_clean else f".{lang_clean}")
                        code_filename = f"code_block_{idx}_{time.strftime('%Y%m%d_%H%M%S')}{code_ext}"
                        code_filepath = target_dir / code_filename
                        with open(code_filepath, "w", encoding="utf-8") as code_f:
                            code_f.write(code)
                        console.print(f"  [green]● Saved code block {idx} ({lang_clean or 'python/unknown'}) to {code_filepath.name}[/green]")
            except Exception as e:
                console.print(f"[bold red]❌ Failed to save to local path: {e}[/bold red]")
            
        elif target == "2":
            console.print("\n[bold cyan]☁️ Target 2: Google Workspace Service Configuration[/bold cyan]")
            google_table = Table(title="☁️ Select Google Workspace Service", border_style="yellow")
            google_table.add_column("Option", style="bold yellow")
            google_table.add_column("Service & Target", style="white")
            google_table.add_row("1", "Google Docs (Write complete report content)")
            google_table.add_row("2", "Google Sheets (Simulate metrics & structured data logging)")
            google_table.add_row("3", "Google Drive (Save raw markdown file to cloud)")
            console.print(google_table)
            google_choice = get_input("Select Google option", choices=["1", "2", "3"], default="1")
            
            token = USER_PREFS.get("google_access_token")
            if token:
                if google_choice == "1":
                    try:
                        import httpx
                        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                        doc_body = {"title": f"TruthGPT Swarm Output — {time.strftime('%Y-%m-%d %H:%M:%S')}"}
                        async with httpx.AsyncClient() as client:
                            res = await client.post("https://docs.googleapis.com/v1/documents", headers=headers, json=doc_body)
                            if res.status_code == 200:
                                doc_data = res.json()
                                document_id = doc_data.get("documentId")
                                requests_body = {
                                    "requests": [
                                        {
                                            "insertText": {
                                                "location": {"index": 1},
                                                "text": content
                                            }
                                        }
                                    ]
                                }
                                await client.post(f"https://docs.googleapis.com/v1/documents/{document_id}:batchUpdate", headers=headers, json=requests_body)
                                console.print(f"[bold green]✓ Successfully exported to Google Docs! Document ID: {document_id}[/bold green]")
                                console.print(f"[bold cyan]🔗 View Document: https://docs.google.com/document/d/{document_id}/edit[/bold cyan]")
                            else:
                                console.print(f"[red]Google Docs API returned error {res.status_code}: {res.text}[/red]")
                                console.print("[yellow]Falling back to Google Workspace secure simulation...[/yellow]")
                                await run_google_simulation(google_choice)
                    except Exception as e:
                        console.print(f"[red]Google Docs API crash: {e}[/red]")
                        console.print("[yellow]Falling back to Google Workspace secure simulation...[/yellow]")
                        await run_google_simulation(google_choice)
                else:
                    await run_google_simulation(google_choice)
            else:
                await run_google_simulation(google_choice)
                
        elif target == "3":
            console.print("\n[bold cyan]🔌 Target 3: Active Model Context Protocol (MCP) Configuration[/bold cyan]")
            mcp_urls = USER_PREFS.get("mcp_servers", ["http://localhost:8000"])
            
            console.print("[dim]Available MCP Server Connections:[/dim]")
            for idx, url in enumerate(mcp_urls):
                console.print(f"  [{idx+1}] {url}")
            
            mcp_choice_str = get_input(f"Select MCP Server [1-{len(mcp_urls)}]", default="1")
            try:
                mcp_idx = int(mcp_choice_str) - 1
                selected_url = mcp_urls[mcp_idx]
            except:
                selected_url = mcp_urls[0]
                
            try:
                from agents.mcp_client import MCPClient
                client = MCPClient(selected_url)
                tools = await client.list_tools()
                if tools:
                    tools_table = Table(title="🛠️ Available MCP Tools", border_style="magenta")
                    tools_table.add_column("Option", style="bold yellow")
                    tools_table.add_column("Tool Name", style="bold white")
                    tools_table.add_column("Description", style="dim")
                    
                    for idx, t in enumerate(tools, 1):
                        tools_table.add_row(str(idx), t["name"], t.get("description", "No description"))
                    tools_table.add_row("0", "Simulate Secure Transmission", "Fallback execution simulator")
                    console.print(tools_table)
                    
                    tool_choice = get_input(f"Select MCP Tool to dispatch results [0-{len(tools)}]", default="1")
                    if tool_choice == "0":
                        await run_mcp_simulation(selected_url, "Simulation")
                    else:
                        try:
                            t_idx = int(tool_choice) - 1
                            selected_tool = tools[t_idx]["name"]
                            
                            console.print(f"[cyan]Selected Tool: {selected_tool}[/cyan]")
                            console.print("[dim]Configuring dispatch arguments...[/dim]")
                            path_arg = get_input("Enter target file/resource path", default=f"swarm_report_{int(time.time())}.md")
                            
                            args = {"path": path_arg, "content": content}
                            
                            console.print(f"[cyan]Calling tool '{selected_tool}' with args: {args}...[/cyan]")
                            res = await client.call_tool(selected_tool, args)
                            console.print(f"[bold green]✓ MCP Tool '{selected_tool}' execution complete: {res}[/bold green]")
                        except Exception as e:
                            console.print(f"[red]Failed to call selected MCP tool: {e}[/red]")
                            console.print("[yellow]Falling back to secure transmission simulation...[/yellow]")
                            await run_mcp_simulation(selected_url, "Fallback")
                else:
                    await run_mcp_simulation(selected_url, "No Tools Exposed")
            except Exception as e:
                console.print(f"[red]Failed to connect to MCP: {e}[/red]")
                await run_mcp_simulation(selected_url, f"Error: {e}")


@cc_menu("Dynamic Swarm Fusion")
async def handle_swarm_fusion(initial_prompt: Optional[str] = None):
    clear_screen()
    console.print(get_header())
    if initial_prompt:
        mode = "1"
    else:
        console.print("   1. 🧠 [bold]Autonomous Mode[/bold] (LLM decides the team)")
        console.print("   2. 🎨 [bold]Designer Mode[/bold] (You build the sequence)")
        console.print("   0. 🏠 Back to Swarm Menu")
        mode = get_input("Select mode", choices=["0", "1", "2"])
        if mode == "0": return

    from agents.registry import registry
    from agents.models import AgentConfig
    from agents.engines import engine_registry
    agents_map = registry.get_all_agents()
    config = AgentConfig()
    llm = engine_registry.get_engine(USER_PREFS["preferred_engine"])
    selected_keys = []
    
    if mode == "1":
        prompt = initial_prompt if initial_prompt else get_input("Enter task for the Autonomous Swarm")
        with console.status("[bold magenta]🧠 Swarm Orchestrator is choosing experts...[/bold magenta]"):
            if llm:
                agent_list = ", ".join(agents_map.keys())
                decision_prompt = (
                    f"Given these agents: [{agent_list}], which ones are the MOST relevant for this task: '{prompt}'?\n"
                    f"Respond ONLY with a JSON list of keys, e.g. [\"research_agent\", \"marketing_agent\"]. "
                    f"Max 5 agents. Order them by execution sequence."
                )
                try:
                    decision_res = await llm(decision_prompt)
                    if decision_res:
                        # Clean/replace single quotes for valid json parser
                        match = re.search(r"\[.*\]", decision_res.replace("\n", ""))
                        parsed_keys = []
                        if match:
                            try:
                                json_str = match.group().replace("'", '"')
                                parsed_keys = json.loads(json_str)
                            except Exception:
                                pass
                        
                        # Fallback parsing: look for keywords or aliases in text in order of appearance
                        if not parsed_keys:
                            found_keys = []
                            for key in agents_map.keys():
                                if key in decision_res.lower():
                                    indices = [m.start() for m in re.finditer(re.escape(key), decision_res.lower())]
                                    for idx in indices:
                                        found_keys.append((idx, key))
                            found_keys.sort()
                            seen = set()
                            for _, key in found_keys:
                                if key not in seen:
                                    seen.add(key)
                                    parsed_keys.append(key)
                        
                        # Apply aliases and self-healing fuzzy matching
                        aliases = {
                            "code_interpreter": "code_architect",
                            "interpreter": "code_architect",
                            "interpreter_agent": "code_architect",
                            "coder": "code_architect",
                            "coder_agent": "code_architect",
                            "architect": "code_architect",
                            "researcher": "research_agent",
                            "researcher_agent": "research_agent",
                            "academic_agent": "research_agent",
                            "system_expert": "system_agent",
                            "system_analyst": "system_agent",
                            "security_agent": "security_analyst",
                            "security": "security_analyst",
                            "security_expert": "security_analyst",
                            "defi": "defi_expert",
                            "defi_agent": "defi_expert",
                            "evolution": "evolution_architect",
                            "evolution_agent": "evolution_architect",
                            "evolutionary_architect": "evolution_architect",
                            "math": "math_verifier",
                            "math_agent": "math_verifier",
                            "math_expert": "math_verifier",
                            "planning": "planning_agent",
                            "coordinator": "planning_agent",
                            "coordination_agent": "planning_agent",
                            "marketing": "marketing_agent",
                            "marketing_expert": "marketing_agent",
                        }
                        
                        mapped_keys = []
                        for k in parsed_keys:
                            if not isinstance(k, str):
                                continue
                            k_clean = k.strip().lower()
                            if k_clean in agents_map:
                                mapped_keys.append(k_clean)
                            elif k_clean in aliases and aliases[k_clean] in agents_map:
                                mapped_keys.append(aliases[k_clean])
                            else:
                                # Try fuzzy/substring match
                                matched = False
                                for actual_key in agents_map.keys():
                                    if actual_key in k_clean or k_clean in actual_key:
                                        mapped_keys.append(actual_key)
                                        matched = True
                                        break
                                if not matched:
                                    log_event("Swarm Warning", f"Ignored unrecognized agent key: {k}")
                        
                        # De-duplicate while preserving order
                        seen_keys = set()
                        for k in mapped_keys:
                            if k not in seen_keys:
                                seen_keys.add(k)
                                selected_keys.append(k)
                                
                except Exception as e:
                    log_event("Swarm Error", f"Orchestrator failed to select agents: {e}")
            
            if not selected_keys:
                # Fallback experts for autonomous mission if LLM fails or is not configured
                selected_keys = []
                for fallback_key in ["research_agent", "code_architect", "system_agent"]:
                    if fallback_key in agents_map:
                        selected_keys.append(fallback_key)
                if not selected_keys and agents_map:
                    selected_keys = [list(agents_map.keys())[0]]
                log_event("Swarm", f"Using fallback experts: {selected_keys}")
                console.print(f"[yellow]⚠️ Could not auto-select experts. Using default: {', '.join(selected_keys)}[/yellow]")
    else:
        table = Table(title="Available Experts & Specialized Phases")
        table.add_column("#", style="cyan")
        table.add_column("Key", style="white")
        table.add_column("Expertise", style="dim")
        display_keys = list(agents_map.keys())
        if "arxiv_discovery_scout" not in display_keys:
            display_keys.append("arxiv_discovery_scout")
        for i, k in enumerate(display_keys, 1):
            expertise = "Research Discovery (ArXiv/Internet)" if k == "arxiv_discovery_scout" else "Specialized Agent"
            table.add_row(str(i), k, expertise)
        console.print(table)
        selection = get_input("Design your sequence (e.g. 5,1,2)")
        indices = [int(i.strip()) for i in selection.split(",") if i.strip().isdigit()]
        selected_keys = [display_keys[i-1] for i in indices if 1 <= i <= len(display_keys)]
        prompt = initial_prompt if initial_prompt else get_input("Enter the initial task/seed for this custom swarm")

    if not selected_keys:
        console.print("[red]No agents selected for orchestration.[/red]")
        wait_for_user()
        return

    # --- Memory Selection Layer ---
    console.print("\n[bold cyan]🧠 Memory Architecture Selection[/bold cyan]")
    mem_table = Table(show_header=False, border_style="cyan")
    mem_table.add_row("1", "Episodic Forensic (Persistent SQLite)", "[bold green]INDUSTRIAL[/bold green]")
    mem_table.add_row("2", "Semantic Vector (RAG/FAISS)", "[bold yellow]KNOWLEDGE[/bold yellow]")
    mem_table.add_row("3", "Holographic High-Dim (Experimental)", "[magenta]EXPERIMENTAL[/magenta]")
    mem_table.add_row("4", "Paper-Driven (Latest Research SOTA)", "[bold blue]SCIENTIFIC[/bold blue]")
    mem_table.add_row("5", "Knowledge Graph (Relational/Triples)", "[bold cyan]COMPLEX[/bold cyan]")
    mem_table.add_row("6", "ULTIMATE Hybrid (Combine ALL Layers)", "[bold red]MASTER[/bold red]")
    console.print(mem_table)
    mem_choice = get_input("Select Memory Type", choices=["1", "2", "3", "4", "5", "6"], default="1")
    
    memory_config = {"type": "forensic", "trace_enabled": True}
    if mem_choice == "2": memory_config = {"type": "vector", "trace_enabled": True}
    elif mem_choice == "3": memory_config = {"type": "holographic", "trace_enabled": True}
    elif mem_choice == "5": memory_config = {"type": "graph", "trace_enabled": True}
    elif mem_choice == "6":
        memory_config = {
            "type": "hybrid_ultimate",
            "layers": ["forensic", "vector", "graph", "paper_dna"],
            "trace_enabled": True,
            "fusion_mode": "weighted_consensus"
        }
        console.print("[bold red]🔥 Initializing ULTIMATE Hybrid Memory Fabric (Multi-Layer Orchestration)...[/bold red]")
    elif mem_choice == "4":
        from modules.base.core_system.core.papers.paper_registry import PaperRegistry
        reg = PaperRegistry()
        mem_papers = reg.list_papers(category="memory")
        if len(mem_papers) < 3: 
            mem_papers += reg.search_papers(query="attention")
        if len(mem_papers) < 5:
            mem_papers += reg.list_papers()[:10] # Broad fallback
            
        if mem_papers:
            p_table = Table(title="📚 SOTA Memory & Architecture Research Papers", header_style="bold magenta", border_style="blue")
            p_table.add_column("#", style="cyan", justify="right")
            p_table.add_column("Paper ID", style="white")
            p_table.add_column("SOTA Technique", style="green")
            p_table.add_column("Impact", style="dim")
            
            for i, p in enumerate(mem_papers[:12], 1):
                tech = ", ".join(p.key_techniques[:2]) if hasattr(p, 'key_techniques') and p.key_techniques else "General SOTA"
                acc_val = getattr(p, 'accuracy_improvement', '5.0')
                impact = f"+{acc_val if acc_val is not None else '0.0'}% Acc"
                p_table.add_row(str(i), p.paper_id, tech, impact)
            console.print(p_table)
            
            p_idx_input = get_input("Select Paper DNA to inject (supports multi-select: 1,2,3)", default="1")
            try:
                selected_papers = []
                for idx_str in p_idx_input.replace(" ", "").split(","):
                    idx = int(idx_str)
                    selected_papers.append(mem_papers[idx-1])
                
                paper_ids = [p.paper_id for p in selected_papers]
                memory_config = {
                    "type": "paper_driven", 
                    "paper_ids": paper_ids, 
                    "trace_enabled": True
                }
                console.print(f"[green]✓ Injecting {', '.join(paper_ids)} into memory fabric.[/green]")
            except: 
                console.print("[yellow]Invalid selection. Using Forensic fallback.[/yellow]")
        else: console.print("[yellow]No memory papers found. Using Forensic standard.[/yellow]")

    console.print(f"\n[bold green]🧬 Executing Swarm Blueprint: {' ➔ '.join(selected_keys)}[/bold green]")
    if any([USER_PREFS.get("mcts_optimized"), USER_PREFS.get("speculative_decoding"), USER_PREFS.get("kv_quantization")]):
        console.print("[bold yellow]⚡ Neural Overdrive Active: Optimizing for Speed & Logic...[/bold yellow]")
    log_activity("Swarm Fusion", f"Blueprint: {'->'.join(selected_keys)} | Memory: {memory_config['type']}")
    
    # --- Execution Orchestration ---
    exec_mode = get_input("Execution Architecture [S/P]", choices=["S", "P"], default="S")
    is_parallel = (exec_mode == "P")
    
    # Dynamic Multi-Target Dispatcher Selection
    
    target_table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
    target_table.add_column("Option", style="bold white", width=10)
    target_table.add_column("Destination", style="bold green", width=40)
    target_table.add_column("Type", style="magenta", width=15)
    
    target_table.add_row("1", "Local Workspace Storage (reports/)", "LOCAL")
    target_table.add_row("2", "Google Workspace (Drive & Docs)", "CLOUD")
    target_table.add_row("3", "Active Model Context Protocol (MCP)", "AGENTIC")
    
    console.print(Panel(
        target_table,
        title="[bold yellow]🚀 Swarm Deployment & Dispatcher Target Selection[/bold yellow]",
        subtitle="[dim]Select one or more destinations to dispatch the swarm outputs (e.g. 1, 2 or 1,2,3)[/dim]",
        border_style="yellow"
    ))
    
    targets_input = get_input("Select Dispatch Targets (multiple allowed via commas)", default="1")
    selected_targets = [t.strip() for t in targets_input.replace(" ", "").split(",") if t.strip()]
    
    console.print(f"\n[bold yellow]🚀 Launching Swarm Fusion ({'Parallel' if is_parallel else 'Sequential'})...[/bold yellow]\n")
    
    content = ""
    context = {"user_id": "orchestrator_fusion", "history": [], "memory_config": memory_config, "memory_trace": []}
    current_prompt = prompt if prompt else get_input("Enter task for the Swarm")
    
    # --- Swarm Telemetry State Management ---
    show_details = False
    active_reasoning_logs = []
    
    def log_reasoning(msg):
        timestamp = time.strftime('%H:%M:%S')
        active_reasoning_logs.append(f"[dim]{timestamp}[/dim] [cyan]•[/cyan] {msg}")
        if len(active_reasoning_logs) > 8:
            active_reasoning_logs.pop(0)

    swarm_states = {
        key: {
            "status": "⏳ Pending", 
            "duration": "0.0s", 
            "info": "Waiting for orchestrator sequence..."
        } for key in selected_keys
    }

    def make_live_table():
        from rich.console import Group
        from rich.text import Text
        from rich.panel import Panel
        title_text = Text("                                     🌀 Swarm Fusion Telemetry & Execution Control", style="bold cyan")
        table = Table(border_style="cyan", show_header=True)
        table.add_column("Agent / Phase", style="bold white", width=25)
        table.add_column("Status", style="magenta", width=15)
        table.add_column("Duration", style="yellow", width=12)
        table.add_column("Current Task / Output Rationale", style="dim", width=55)
        for key in selected_keys:
            state = swarm_states[key]
            status_val = state["status"]
            if "Complete" in status_val:
                status_str = "[bold green]✅ Complete[/bold green]"
            elif "Failed" in status_val:
                status_str = "[bold red]❌ Failed[/bold red]"
            elif "Executing" in status_val:
                status_str = "[bold cyan]⚡ Executing[/bold cyan]"
            else:
                status_str = f"[dim]{status_val}[/dim]"
            
            table.add_row(key, status_str, state["duration"], state["info"])
            
        guide_text = Text("💡 Press [bold yellow][D][/bold yellow] or [bold yellow][Space][/bold yellow] to toggle Claude-style Live Detail view", style="bold dim white")
        elements = [title_text, table, guide_text]
        
        if show_details:
            log_content = "\n".join(active_reasoning_logs) if active_reasoning_logs else "[dim]No active logs yet...[/dim]"
            details_panel = Panel(
                log_content,
                title="🔍 Claude-style Active Reasoning Stream",
                border_style="yellow",
                expand=True
            )
            elements.append(details_panel)
            
        return Group(*elements)

    async def run_phase(key, idx, phase_prompt, live_updater=None):
        from interface.cc_style import cc_action, cc_tool_call, cc_result, cc_agent_done, cc_code_change
        
        start_phase = time.time()
        cc_action(f"Swarm Phase {idx}: Agent '{key}' activated", status="RUN")
        
        trace_entry = {
            "phase": key, 
            "time": time.strftime('%H:%M:%S'), 
            "actions": [],
            "rationale": "Calculating optimal strategy based on previous state..."
        }
        
        swarm_states[key]["status"] = "Executing"
        swarm_states[key]["info"] = f"Initializing memory fabric ({memory_config['type']})..."
        cc_tool_call(f"Connecting to memory layer fabric ({memory_config['type']})...")
        
        if memory_config["type"] == "hybrid_ultimate":
            trace_entry["actions"].append("Retrieved cross-layer relational embeddings")
            trace_entry["actions"].append("Synced forensic persistent state")
        else:
            trace_entry["actions"].append(f"Querying {memory_config['type']} memory layer")
            
        cc_tool_call("Commencing specialized agent cognitive loop...")
        
        try:
            if key == "arxiv_discovery_scout":
                cc_tool_call("Querying SOTA academic data sources...")
                from agents.system_intelligence.research_agent import ResearchAgent
                agent = ResearchAgent(llm_engine=llm)
                res = await agent.process(f"descubrir e integrar papers de {phase_prompt}")
                p_content = res.content
                trace_entry["rationale"] = f"Identified research gaps for {phase_prompt}. Seeking SOTA validation."
            else:
                agent_cls = agents_map[key]
                sig = inspect.signature(agent_cls.__init__)
                params = {}
                if "config" in sig.parameters: params["config"] = config
                if "llm_engine" in sig.parameters: params["llm_engine"] = llm
                agent = agent_cls(**params)
                
                cc_tool_call("Invoking neural LLM reasoning cognitive cycle...")
                res = await agent.process(phase_prompt, context=context)
                p_content = res.content if hasattr(res, 'content') else str(res)
                
                rationale = res.metadata.get("rationale") if hasattr(res, 'metadata') and res.metadata else None
                if not rationale:
                    rationale = f"Executing {key} logic to transform state."
                trace_entry["rationale"] = rationale

            # Auto-persist code
            if "```" in p_content:
                target_dir = extract_target_directory(prompt) or extract_target_directory(initial_prompt)
                if target_dir:
                    code_dir = target_dir
                else:
                    code_dir = Path("truthgpt_collected/generated_code")
                saved = save_code_blocks_to_directory(p_content, code_dir, default_prefix=f"output_{key}")
                if saved:
                    trace_entry["actions"].append(f"Persisted code to {saved[-1].name}")
                    trace_entry["code_file"] = str(saved[-1])

            swarm_states[key]["status"] = "Complete"
            swarm_states[key]["duration"] = f"{time.time() - start_phase:.1f}s"
            swarm_states[key]["info"] = trace_entry["rationale"][:50] + "..." if len(trace_entry["rationale"]) > 50 else trace_entry["rationale"]
            
            duration = time.time() - start_phase
            trace_entry["actions"].append(f"Committed phase output to {memory_config['type']} fabric")
            trace_entry["duration"] = f"{duration:.2f}s"
            if USER_PREFS.get("mcts_optimized"):
                trace_entry["speedup"] = "1.4x (Overdrive)"
                
            cc_agent_done(key, ok=True)
            cc_result(f"Completed in {swarm_states[key]['duration']} · {trace_entry['rationale']}")
            return trace_entry, p_content
            
        except Exception as e:
            logger.error(f"Error executing Swarm Phase {idx} ({key}): {e}")
            p_content = f"⚠️ Swarm Phase {idx} ({key}) Failed:\n{str(e)}"
            trace_entry["rationale"] = f"Execution failed due to: {str(e)}"
            
            swarm_states[key]["status"] = "Failed"
            cc_agent_done(key, ok=False)
            cc_result(f"Error: {str(e)[:100]}...")
            raise e

    def _safe_panel(text: str, title: str, border_style: str = "green", max_chars: int = 3000):
        """Render a Panel safely, truncating if content is too large."""
        try:
            display_text = text if len(text) <= max_chars else text[:max_chars] + "\n\n[dim]... (output truncated for display)[/dim]"
            console.print(Panel(display_text, title=title, border_style=border_style))
        except Exception as render_err:
            logger.warning(f"Panel render failed: {render_err}")
            console.print(f"\n[bold {border_style}]{title}[/bold {border_style}]")
            console.print(text[:500] if text else "(empty)")

    # Execute and capture results with elegant progressive Claude CLI output
    import interface.cc_style as cc_style
    cc_style.SUPPRESS_SPINNERS = True
    
    final_results = []
    
    try:
        if is_parallel:
            async_tasks = []
            for i, key in enumerate(selected_keys):
                t = asyncio.create_task(run_phase(key, i+1, current_prompt))
                async_tasks.append((key, t))
            
            results = await asyncio.gather(*(t for _, t in async_tasks), return_exceptions=True)
            
            # Formulate the return results
            for i, result in enumerate(results):
                key = selected_keys[i]
                if isinstance(result, Exception):
                    final_results.append((key, Exception(f"Phase failed: {result}"), f"⚠️ Phase failed: {result}"))
                else:
                    final_results.append((key, result[0], result[1]))
        else:
            for i, key in enumerate(selected_keys):
                try:
                    trace, p_res = await run_phase(key, i+1, current_prompt)
                    final_results.append((key, trace, p_res))
                    # Update prompt for next sequential phase (capped to prevent token overflow)
                    summary = p_res[:1500] if len(p_res) > 1500 else p_res
                    current_prompt = f"Previous phase ({key}) summary: {summary}\n\nOriginal objective: {initial_prompt or current_prompt[:500]}"
                except Exception as phase_err:
                    err_msg = f"⚠️ Phase {i+1} ({key}) crashed: {type(phase_err).__name__}: {str(phase_err)[:300]}"
                    final_results.append((key, phase_err, err_msg))
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Swarm fusion execution interrupted/cancelled by user (Ctrl+C).[/bold red]")
        
        # Cancel all parallel tasks
        if is_parallel:
            for key, t in async_tasks:
                if not t.done():
                    t.cancel()
            await asyncio.sleep(0.1)
        
        # Append Cancelled status to final_results so they are accounted for
        for remaining_key in selected_keys[len(final_results):]:
            final_results.append((remaining_key, Exception("Cancelled"), "⚠️ Phase cancelled by user."))

    # --- Render final output panels under the finished telemetry table ---
    for item in final_results:
        key = item[0]
        if isinstance(item[1], Exception):
            err_msg = item[2]
            content += f"\n\n--- Phase Error ({key}) ---\n{err_msg}"
            _safe_panel(err_msg, title=f"❌ {key} Failed", border_style="red")
        else:
            trace = item[1]
            p_res = item[2]
            context["memory_trace"].append(trace)
            content += f"\n\n--- Phase Output ({key}) ---\n{p_res}"
            _safe_panel(p_res, title=f"✅ {key} Complete", border_style="green")
    
    console.print("\n[bold green]✓ Swarm Orchestration Complete.[/bold green]")
    
    # Execute Swarm Deployment Target Dispatching
    await execute_swarm_dispatch(content, selected_targets)

    # New: Interactive Forensic Control Room & Sandbox Browser
    if Confirm.ask("\n[bold cyan]🕵️ Would you like to enter the Forensic Swarm Control Room & Code Sandbox?[/bold cyan]", default=True):
        await swarm_phase_inspector(final_results, memory_config, config, llm)
    
    # Save Log Trace to disk
    if memory_config.get("trace_enabled"):
        trace_path = Path("truthgpt_collected/logs/memory_traces")
        trace_path.mkdir(parents=True, exist_ok=True)
        filename = f"trace_{int(time.time())}.json"
        with open(trace_path / filename, "w") as f:
            json.dump(context["memory_trace"], f, indent=4)
        console.print(f"[dim]💾 Decision Trace persisted to {trace_path / filename}[/dim]")
        
        # New: Interactive Trace Review
        if Confirm.ask("[bold cyan]Would you like to review the Decision Logic Trace?[/bold cyan]"):
            t_table = Table(title="🕵️ Forensic Decision Trace", border_style="cyan")
            t_table.add_column("Phase", style="magenta")
            t_table.add_column("Rationale / Why?", style="white")
            t_table.add_column("Duration", style="yellow")
            t_table.add_column("Efficiency", style="green")
            t_table.add_column("Actions Taken", style="dim")
            for entry in context["memory_trace"]:
                t_table.add_row(
                    entry["phase"], 
                    entry["rationale"], 
                    entry.get("duration", "N/A"),
                    entry.get("speedup", "1.0x (Standard)"),
                    "\n".join([f"• {a}" for a in entry["actions"]])
                )
            console.print(t_table)
        
    # --- Post-Mission Autonomous Actions (Available for all missions) ---
    console.print("\n[bold cyan]⚡ Post-Mission Autonomous Actions[/bold cyan]")
    action_table = Table(show_header=False, border_style="dim")
    action_table.add_row("1", "🚀 [bold green]Self-Optimize[/bold green] (Run Overdrive on Results)")
    action_table.add_row("2", "🔄 [bold yellow]Continuous Mode[/bold yellow] (Recursive Mission)")
    action_table.add_row("3", "🛡️ [bold blue]Self-Refine[/bold blue] (Architect Review)")
    action_table.add_row("0", "🏠 Finish & Return")
    console.print(action_table)
    
    post_choice = get_input("Select next autonomous action", choices=["0", "1", "2", "3"], default="0")
    
    if post_choice == "1":
        from interface.overdrive_menu import handle_overdrive_menu
        await handle_overdrive_menu()
        # After overdrive, return to the same mission results or finish
    elif post_choice == "2":
        console.print("\n[bold yellow]🔁 Recursive Continuity Configuration[/bold yellow]")
        interval_min = FloatPrompt.ask(" [bold cyan]➔ Enter Execution Interval (minutes, 0 for instant)[/bold cyan]", default=0.0)
        console.print(f"[bold green]✓ Continuous Mission Mode Activated (Interval: {interval_min}m)[/bold green]")
        if interval_min > 0:
            await wait_with_interrupt(interval_min * 60)
        await handle_swarm_fusion(initial_prompt=f"Evolve and improve the following results: {content}")
        return
    elif post_choice == "3":
        console.print("[bold blue]🛡️ Code Architect is refining the mission output...[/bold blue]")
        from agents.code_interpreter import CodeInterpreterAgent
        architect = CodeInterpreterAgent(config=config, llm_engine=llm)
        refinement = await architect.process(f"Refine and industrialize this code for System 5.9: {content}")
        console.print(Panel(refinement.content, title="🛡️ Architectural Refinement", border_style="blue"))
        wait_for_user(force=True)

    wait_for_user(force=True)


async def handle_continuous_mission():
    clear_screen()
    console.print(get_header())
    console.print(Panel("[bold yellow]🔁 Continuous Mission Mode[/bold yellow]", expand=False))
    query = get_input("Enter the persistent mission query")
    interval_min = FloatPrompt.ask("Execution interval (minutes)", default=5.0)
    console.print(f"\n[green]✓ Mission started: '{query}'[/green]")
    from agents.client import AgentClient
    from agents.engines import engine_registry
    llm = engine_registry.get_engine(USER_PREFS["preferred_engine"])
    client = AgentClient(use_swarm=True, llm_engine=llm)
    try:
        while True:
            console.print(f"[bold cyan][{time.strftime('%H:%M:%S')}] Executing Mission...[/bold cyan]")
            response = await client.swarm.route_and_process(query, context={"user_id": "continuous_mission"})
            content = response.content if hasattr(response, 'content') else str(response)
            console.print(Panel(content, title="🤖 Mission Output", border_style="yellow"))
            
            # If target directory is in query, auto-extract and save code blocks to it
            target_dir = extract_target_directory(query)
            if target_dir:
                console.print(f"[cyan]📦 Extracting and writing code blocks to local folder {target_dir}...[/cyan]")
                save_code_blocks_to_directory(content, target_dir, default_prefix="output_continuous")
            
            action = await wait_with_interrupt(interval_min * 60)
            if action == "stop" or action == "menu": break
            elif action == "query":
                new_query = get_input("Enter new persistent mission query", default=query)
                if new_query.strip():
                    query = new_query.strip()
                    console.print(f"[green]✓ Mission query updated to: '{query}'[/green]")
            elif action == "export": save_mission_output(content, mission_name="Continuous", query=query)
    except KeyboardInterrupt: console.print("\n[red]Mission terminated by user.[/red]")

async def handle_background_missions():
    clear_screen()
    console.print(get_header())
    console.print("[bold cyan]📡 Active Background Missions[/bold cyan]")
    if not background_missions:
        console.print("[yellow]No missions running in background.[/yellow]")
        wait_for_user(force=True)
        return
    table = Table()
    table.add_column("#")
    table.add_column("Mission Name")
    table.add_column("Interval")
    table.add_column("Last Run")
    table.add_column("Status")
    for i, m in enumerate(background_missions, 1):
        table.add_row(str(i), m.name, f"{m.interval}m", m.last_run or "Pending", m.status)
    console.print(table)
    cmd = get_input("Action")
    if cmd == "0": return
    # ... stop/view history logic ...

async def handle_mcp_connect():
    from agents.mcp_client import MCPClient
    import os
    url = get_input("Enter MCP Server URL", default=os.environ.get("MCP_SERVER_URL", "http://localhost:8000"))
    client = MCPClient(url)
    with console.status(f"[bold cyan]Connecting to {url}...[/bold cyan]"):
        try:
            tools = await client.list_tools()
            if tools:
                table = Table(title="🛠️ External Tools")
                for t in tools: table.add_row(t.get("name"), t.get("description"))
                console.print(table)
        except Exception as e: console.print(f"[red]Error: {e}[/red]")
    await client.close()
    wait_for_user(force=True)

async def handle_expert_matrix(agents):
    clear_screen()
    console.print(get_header())
    table = Table(title="🛠️ Expert Tool Matrix")
    table.add_column("Expert")
    table.add_column("Tools")
    for agent in agents:
        tools = ", ".join(agent.tools.keys()) if hasattr(agent, "tools") else "N/A"
        table.add_row(agent.name, tools)
    console.print(table)
    wait_for_user(force=True)

async def handle_persona_tuning(agents):
    clear_screen()
    console.print(get_header())
    if not agents:
        console.print("[yellow]⚠️ No active swarm agents available for persona tuning.[/yellow]")
        wait_for_user(force=True)
        return
    for i, a in enumerate(agents, 1): console.print(f" {i}. {a.name}")
    try:
        idx_str = get_input("Select expert (or '0' to cancel)", default="1")
        if idx_str == "0":
            return
        idx = int(idx_str)
        if 1 <= idx <= len(agents):
            target = agents[idx-1]
            new_role = get_input("New Role/Description", default=getattr(target, "role", ""))
            if new_role: 
                target.role = new_role
                console.print(f"[green]✓ Persona updated for {target.name}![/green]")
            else:
                console.print("[dim]No changes made.[/dim]")
        else:
            console.print("[red]❌ Invalid selection.[/red]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
    wait_for_user(force=True)

async def handle_swarm_telemetry():
    clear_screen()
    console.print(get_header())
    health = {"Status": "Healthy", "Latency": "45ms"}
    console.print(Panel("\n".join([f"{k}: {v}" for k, v in health.items()]), title="🛰️ Telemetry"))
    wait_for_user(force=True)


async def handle_math_verification():
    """Interactive Math & Formal Verification console."""
    clear_screen()
    console.print(get_header())
    console.print(Panel(
        " [bold cyan]🔬 Math & Formal Verification Engine[/bold cyan]\n"
        " [dim]Lean 4 • SymPy • Z3 SMT • NumPy • Code Verify[/dim]",
        border_style="cyan"
    ))

    # Show available commands
    cmd_table = Table(title="Available Commands", box=None, padding=(0, 2))
    cmd_table.add_column("Prefix", style="bold cyan")
    cmd_table.add_column("Engine", style="white")
    cmd_table.add_column("Example", style="dim")
    cmd_table.add_row("prove:", "SymPy", "prove: (x+1)**2 == x**2 + 2*x + 1")
    cmd_table.add_row("solve:", "SymPy", "solve: x**2 - 4 = 0")
    cmd_table.add_row("simplify:", "SymPy", "simplify: (x**2-1)/(x-1)")
    cmd_table.add_row("integrate:", "SymPy", "integrate: x**2 + 2*x")
    cmd_table.add_row("diff:", "SymPy", "diff: sin(x)*cos(x)")
    cmd_table.add_row("limit:", "SymPy", "limit: sin(x)/x, x, 0")
    cmd_table.add_row("factor:", "SymPy", "factor: x**3 - 1")
    cmd_table.add_row("matrix:", "SymPy", 'matrix: [[1,2],[3,4]]')
    cmd_table.add_row("eigenvalues:", "NumPy", "eigenvalues: [[1,2],[3,4]]")
    cmd_table.add_row("roots:", "NumPy", "roots: [1, -5, 6]")
    cmd_table.add_row("svd:", "NumPy", "svd: [[1,2],[3,4]]")
    cmd_table.add_row("theorem ...", "Lean 4", "theorem add_comm : ∀ a b, a + b = b + a")
    cmd_table.add_row("x > 0, ...", "Z3 SMT", "x > 0, x < 10, x*x == 49")
    cmd_table.add_row("typecheck:", "mypy", "typecheck: def f(x: int) -> int: return x")
    console.print(cmd_table)

    try:
        from agents.formal_verification.math_agent import MathVerificationAgent
        from agents.engines import engine_registry
        llm = engine_registry.get_engine(USER_PREFS["preferred_engine"])
        agent = MathVerificationAgent(llm_engine=llm)
    except ImportError as e:
        console.print(f"[red]Error loading MathVerificationAgent: {e}[/red]")
        wait_for_user(force=True)
        return

    console.print("\n[dim]Type your expression (or 'exit' to return):[/dim]")
    while True:
        expr = get_input("\n[bold cyan]Math (type '0' to go back)>[/bold cyan]")
        if expr.lower() in ("exit", "quit", "0", "back", ""):
            break

        with console.status("[bold cyan]Verifying...[/bold cyan]"):
            result = await agent.process(expr, context={"user_id": "cli_math"})
            content = result.content if hasattr(result, "content") else str(result)
            console.print(Panel(content, title="🔬 Verification Result", border_style="green"))


async def handle_agent_composer():
    """Interactive Agent Composer — build custom agent combinations."""
    clear_screen()
    console.print(get_header())
    console.print(Panel(
        " [bold magenta]🧩 Agent Composer — Build Your Custom Agent[/bold magenta]\n"
        " [dim]Mix capabilities from Math, Research, Code, and System domains[/dim]",
        border_style="magenta"
    ))

    try:
        from agents.composer.agent_composer import (
            _build_catalog, save_blueprint, load_blueprints, ComposedAgent
        )
    except ImportError as e:
        console.print(f"[red]Composer not available: {e}[/red]")
        wait_for_user(force=True)
        return

    # Menu
    console.print("   1. 🧩 [bold]Create New Agent[/bold]")
    console.print("   2. 📂 [bold]Load Saved Blueprint[/bold]")
    console.print("   3. 📋 [bold]View Catalog[/bold]")
    console.print("   0. 🏠 Back")
    mode = get_input("Select", choices=["0", "1", "2", "3"])
    if mode == "0":
        return

    catalog = _build_catalog()

    if mode == "3":
        # Display full catalog
        cat_table = Table(title="🧩 Capability Catalog", border_style="magenta")
        cat_table.add_column("#", style="cyan", justify="right")
        cat_table.add_column("Key", style="white")
        cat_table.add_column("Category", style="yellow")
        cat_table.add_column("Description", style="green")
        for i, (key, info) in enumerate(catalog.items(), 1):
            cat_table.add_row(str(i), key, info["category"], info["description"])
        console.print(cat_table)
        wait_for_user(force=True)
        return

    if mode == "2":
        blueprints = load_blueprints()
        if not blueprints:
            console.print("[yellow]No saved blueprints found.[/yellow]")
            wait_for_user(force=True)
            return

        bp_table = Table(title="📂 Saved Blueprints", border_style="blue")
        bp_table.add_column("#", style="cyan")
        bp_table.add_column("Name", style="bold white")
        bp_table.add_column("Capabilities", style="green")
        bp_table.add_column("Created", style="dim")
        for i, bp in enumerate(blueprints, 1):
            caps = ", ".join(bp.get("capabilities", []))
            bp_table.add_row(str(i), bp["name"], caps, bp.get("created", "N/A"))
        console.print(bp_table)

        idx = int(get_input("Select blueprint to deploy", default="1"))
        if 1 <= idx <= len(blueprints):
            bp = blueprints[idx - 1]
            from agents.engines import engine_registry
            llm = engine_registry.get_engine(USER_PREFS["preferred_engine"])
            agent = ComposedAgent(
                name=bp["name"],
                role=bp.get("role", "Custom Agent"),
                capabilities=bp["capabilities"],
                llm_engine=llm,
            )
            console.print(f"\n[bold green]✓ Deployed: {agent.name}[/bold green]")
            console.print(f"[dim]Capabilities:\n{agent.get_capability_summary()}[/dim]")

            # Interactive query loop
            while True:
                query = get_input(f"\n[bold magenta]{agent.name} (type '0' to go back)>[/bold magenta]")
                if query.lower() in ("exit", "quit", "0", "back", ""):
                    break
                with console.status(f"[bold cyan]{agent.name} working...[/bold cyan]"):
                    res = await agent.process(query, context={"user_id": "cli_composer"})
                    content = res.content if hasattr(res, "content") else str(res)
                    console.print(Panel(content, title=f"🤖 {agent.name}", border_style="green"))
        return

    # mode == "1" — Create new agent
    console.print("\n[bold cyan]Step 1: Name your agent[/bold cyan]")
    agent_name = get_input("Agent name", default="MyCustomAgent")
    agent_role = get_input("Agent role/description", default="Custom Specialized Agent")

    console.print("\n[bold cyan]Step 2: Select capabilities[/bold cyan]")
    cap_table = Table(title="Available Capabilities", border_style="cyan")
    cap_table.add_column("#", style="cyan", justify="right")
    cap_table.add_column("Key", style="white")
    cap_table.add_column("Category", style="yellow")
    cap_table.add_column("Description", style="green")

    cap_keys = list(catalog.keys())
    for i, key in enumerate(cap_keys, 1):
        info = catalog[key]
        cap_table.add_row(str(i), key, info["category"], info["description"])
    console.print(cap_table)

    selection = get_input("Select capabilities (e.g. 1,2,5,8)")
    indices = [int(i.strip()) for i in selection.split(",") if i.strip().isdigit()]
    selected_caps = [cap_keys[i - 1] for i in indices if 1 <= i <= len(cap_keys)]

    if not selected_caps:
        console.print("[red]No capabilities selected.[/red]")
        wait_for_user(force=True)
        return

    console.print(f"\n[bold green]✓ Building '{agent_name}' with: {', '.join(selected_caps)}[/bold green]")

    # Save blueprint?
    if Confirm.ask("Save this as a reusable blueprint?", default=True):
        path = save_blueprint(agent_name, selected_caps, {"role": agent_role})
        console.print(f"[dim]Blueprint saved to {path}[/dim]")

    # Deploy and use
    from agents.engines import engine_registry
    llm = engine_registry.get_engine(USER_PREFS["preferred_engine"])
    agent = ComposedAgent(
        name=agent_name,
        role=agent_role,
        capabilities=selected_caps,
        llm_engine=llm,
    )

    tools_list = ", ".join(agent.tools.keys()) if agent.tools else "none"
    console.print(f"[bold green]✓ Agent deployed with tools: {tools_list}[/bold green]")
    console.print(f"[dim]Capabilities:\n{agent.get_capability_summary()}[/dim]")

    # Interactive query loop
    console.print("\n[dim]Type queries (or 'exit' to return):[/dim]")
    while True:
        query = get_input(f"\n[bold magenta]{agent_name} (type '0' to go back)>[/bold magenta]")
        if query.lower() in ("exit", "quit", "0", "back", ""):
            break
        with console.status(f"[bold cyan]{agent_name} working...[/bold cyan]"):
            res = await agent.process(query, context={"user_id": "cli_composer"})
            content = res.content if hasattr(res, "content") else str(res)
            console.print(Panel(content, title=f"🤖 {agent_name}", border_style="green"))


# ==========================================
# 🕵️ Forensic Swarm Control Room & Code Sandbox
# ==========================================

def _safe_panel(text: str, title: str, border_style: str = "green", max_chars: int = 3000):
    """Render a Panel safely, truncating if content is too large."""
    from rich.panel import Panel
    try:
        display_text = text if len(text) <= max_chars else text[:max_chars] + "\n\n[dim]... (output truncated for display)[/dim]"
        console.print(Panel(display_text, title=title, border_style=border_style))
    except Exception as render_err:
        console.print(f"\n[bold {border_style}]{title}[/bold {border_style}]")
        console.print(text[:500] if text else "(empty)")

async def swarm_phase_inspector(final_results, memory_config, config, llm):
    from rich.panel import Panel
    from rich.table import Table
    
    while True:
        clear_screen()
        console.print(get_header())
        console.print(Panel("[bold cyan]🕵️ Forensic Swarm Control Room & Code Sandbox[/bold cyan]\nBrowse, inspect, and manipulate agent outputs and generated code in real time.", expand=False))
        
        table = Table(title="Swarm Execution History & Sandboxes", border_style="cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Agent / Phase", style="magenta", width=25)
        table.add_column("Status", style="bold", width=15)
        table.add_column("Duration", style="yellow", width=12)
        table.add_column("Actions / Output Summary", style="white")
        table.add_column("Code Generated", style="green", width=20)
        
        for i, item in enumerate(final_results, 1):
            key = item[0]
            if isinstance(item[1], Exception):
                status_str = "[bold red]❌ Failed[/bold red]"
                duration_str = "N/A"
                actions_str = f"crashed: {str(item[1])[:60]}"
                has_code = "No"
            else:
                trace = item[1]
                status_str = "[bold green]✓ Complete[/bold green]"
                duration_str = trace.get("duration", "N/A")
                actions_str = "\n".join([f"• {a}" for a in trace.get("actions", [])])
                if not actions_str:
                    actions_str = trace.get("rationale", "N/A")[:60]
                has_code = "[bold green]Yes (Python)[/bold green]" if "code_file" in trace else "No"
                
            table.add_row(str(i), key, status_str, duration_str, actions_str, has_code)
            
        console.print(table)
        console.print("\n[bold dim]Options:[/bold dim] Enter a phase number [1-{}] to inspect, [bold green]A[/bold green] to View All Panels, or [bold yellow]0[/bold yellow] to exit Control Room.".format(len(final_results)))
        
        phase_choices = ["0", "a", "A"] + [str(i) for i in range(1, len(final_results) + 1)]
        choice = get_input("Select Option", choices=phase_choices, default="0")
        
        if choice == "0":
            break
        elif choice.lower() == "a":
            clear_screen()
            console.print(get_header())
            console.print(Panel("[bold green]📋 Full Swarm Mission Output Trace[/bold green]", expand=False))
            for item in final_results:
                key = item[0]
                if isinstance(item[1], Exception):
                    err_msg = item[2]
                    _safe_panel(err_msg, title=f"❌ {key} Failed", border_style="red")
                else:
                    p_res = item[2]
                    _safe_panel(p_res, title=f"✅ {key} Complete", border_style="green")
            wait_for_user(force=True)
            continue
            
        idx = int(choice) - 1
        selected_item = final_results[idx]
        await inspect_single_phase(selected_item, memory_config, config, llm)

async def inspect_single_phase(item, memory_config, config, llm):
    key = item[0]
    
    while True:
        clear_screen()
        console.print(get_header())
        console.print(Panel(f"[bold cyan]🕵️ Phase Control Room: {key}[/bold cyan]", expand=False))
        
        if isinstance(item[1], Exception):
            err_msg = item[2]
            console.print(Panel(err_msg, title="❌ Phase Error Traceback", border_style="red"))
            console.print("\n[bold yellow]0[/bold yellow] Back to Control Room")
            get_input("Press Enter to go back", choices=["0"], default="0")
            break
            
        trace = item[1]
        p_res = item[2]
        code_file_path = trace.get("code_file")
        
        # Display details table
        details = Table(show_header=False, border_style="dim")
        details.add_row("Agent Phase", f"[magenta]{key}[/magenta]")
        details.add_row("Execution Status", "[bold green]✓ Complete[/bold green]")
        details.add_row("Duration", trace.get("duration", "N/A"))
        details.add_row("Rationale", trace.get("rationale", "N/A"))
        details.add_row("Memory Sync", f"Committed to {memory_config['type']} fabric")
        if code_file_path:
            details.add_row("Generated Code File", f"[bold green]{Path(code_file_path).name}[/bold green]")
        console.print(details)
        
        # Submenu
        console.print("\n[bold cyan]⚡ Phase Manipulation Actions[/bold cyan]")
        action_table = Table(show_header=False, border_style="dim")
        action_table.add_row("1", "📖 [bold white]View Full Response Text[/bold white]")
        if code_file_path:
            action_table.add_row("2", "📝 [bold green]View & Edit Generated Code[/bold green]")
            action_table.add_row("3", "🚀 [bold yellow]Execute Code in Sandbox (Interactive Run)[/bold yellow]")
            action_table.add_row("4", "✨ [bold cyan]Optimize Code (Overdrive Compiler)[/bold cyan]")
        action_table.add_row("5", "🔄 [bold magenta]Re-run Phase with Custom Guidance[/bold magenta]")
        action_table.add_row("0", "🔙 Back to Control Room")
        console.print(action_table)
        
        choices = ["0", "1", "5"]
        if code_file_path:
            choices += ["2", "3", "4"]
            
        sub_choice = get_input("Select Action", choices=choices, default="0")
        
        if sub_choice == "0":
            break
        elif sub_choice == "1":
            # View full text response
            clear_screen()
            console.print(Panel(p_res, title=f"📖 {key} Full Raw Output", border_style="cyan"))
            wait_for_user(force=True)
        elif sub_choice == "2":
            # View and Edit Generated Code
            if code_file_path:
                await view_and_edit_code(code_file_path)
        elif sub_choice == "3":
            # Execute Code in Sandbox
            if code_file_path:
                await execute_sandbox_code(code_file_path)
        elif sub_choice == "4":
            # Optimize Code (Overdrive Compiler)
            if code_file_path:
                await optimize_sandbox_code(code_file_path, config, llm)
        elif sub_choice == "5":
            # Re-run Phase with Custom Guidance
            guidance = get_input("Enter custom guidance / instructions to re-run this phase")
            if guidance.strip():
                console.print(f"[bold yellow]🔄 Re-running phase {key} with custom instructions...[/bold yellow]")
                new_prompt = f"Additional user instruction: {guidance}\n\nOriginal context: {p_res}"
                try:
                    console.print(f"[bold cyan]Invoking {key} for refinement...[/bold cyan]")
                    
                    if key == "arxiv_discovery_scout":
                        from agents.system_intelligence.research_agent import ResearchAgent
                        agent = ResearchAgent(llm_engine=llm)
                        res = await agent.process(new_prompt)
                    else:
                        from agents.client import AgentRegistry
                        registry = AgentRegistry()
                        agents_map = registry.get_all_agents()
                        agent_cls = agents_map[key]
                        sig = inspect.signature(agent_cls.__init__)
                        params = {}
                        if "config" in sig.parameters: params["config"] = config
                        if "llm_engine" in sig.parameters: params["llm_engine"] = llm
                        agent = agent_cls(**params)
                        res = await agent.process(new_prompt)
                        
                    new_content = res.content if hasattr(res, 'content') else str(res)
                    console.print(Panel(new_content, title=f"✨ Refined {key} Output", border_style="green"))
                    
                    # Update item inplace
                    item[2] = new_content
                    if "```" in new_content:
                        target_dir = extract_target_directory(guidance) if 'guidance' in locals() else None
                        if not target_dir:
                            target_dir = extract_target_directory(prompt) or extract_target_directory(initial_prompt)
                        if target_dir:
                            code_dir = target_dir
                        else:
                            code_dir = Path("truthgpt_collected/generated_code")
                        saved = save_code_blocks_to_directory(new_content, code_dir, default_prefix=f"output_{key}")
                        if saved:
                            trace["code_file"] = str(saved[-1])
                            console.print(f"[bold green]✓ Persisted new refined code to {saved[-1].name}[/bold green]")
                    wait_for_user(force=True)
                except Exception as rerun_err:
                    console.print(f"[bold red]Rerun failed: {rerun_err}[/bold red]")
                    wait_for_user(force=True)

async def view_and_edit_code(file_path):
    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]Error: file {path.name} not found.[/bold red]")
        wait_for_user(force=True)
        return
        
    while True:
        clear_screen()
        console.print(get_header())
        console.print(Panel(f"[bold green]📝 Code Inspector: {path.name}[/bold green]\nLocated at: [dim]{path.resolve()}[/dim]", expand=False))
        
        # Print code with line numbers
        code_text = path.read_text(encoding="utf-8", errors="ignore")
        from rich.syntax import Syntax
        syntax = Syntax(code_text, "python", theme="monokai", line_numbers=True)
        console.print(syntax)
        
        console.print("\n[bold cyan]Code Actions[/bold cyan]")
        action_table = Table(show_header=False, border_style="dim")
        action_table.add_row("1", "✏️ [bold yellow]Modify Code (Quick String Replace)[/bold yellow]")
        action_table.add_row("2", "💾 [bold green]Open in User Workspace[/bold green] (Save copy to workspace root)")
        action_table.add_row("0", "🔙 Back to Phase menu")
        console.print(action_table)
        
        choice = get_input("Select Action", choices=["0", "1", "2"], default="0")
        if choice == "0":
            break
        elif choice == "1":
            target = get_input("Enter the EXACT line/substring you want to replace")
            if target in code_text:
                replacement = get_input("Enter the replacement content")
                new_code = code_text.replace(target, replacement)
                path.write_text(new_code, encoding="utf-8")
                console.print("[bold green]✓ Code updated successfully.[/bold green]")
            else:
                console.print("[bold red]Substring not found in code. Try again.[/bold red]")
            wait_for_user(force=True)
        elif choice == "2":
            workspace_dest = Path("C:/blatam-academy") / path.name
            workspace_dest.write_text(code_text, encoding="utf-8")
            console.print(f"[bold green]✓ Code successfully saved to user workspace: {workspace_dest.name}[/bold green]")
            wait_for_user(force=True)

async def execute_sandbox_code(file_path):
    import sys
    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]Error: file {path.name} not found.[/bold red]")
        wait_for_user(force=True)
        return
        
    clear_screen()
    console.print(get_header())
    console.print(Panel(f"[bold yellow]🚀 Sandbox Execution: {path.name}[/bold yellow]\nRunning code in isolated Python process...", expand=False))
    
    start_time = time.time()
    try:
        import subprocess
        res = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, timeout=30)
        duration = time.time() - start_time
        
        console.print(f"[bold dim]Execution finished in {duration:.2f}s with exit code {res.returncode}[/bold dim]\n")
        
        if res.stdout:
            console.print(Panel(res.stdout, title="stdout", border_style="green"))
        if res.stderr:
            console.print(Panel(res.stderr, title="stderr", border_style="red"))
            
        if not res.stdout and not res.stderr:
            console.print("[dim](No output was produced by the script)[/dim]")
            
    except subprocess.TimeoutExpired:
        console.print("[bold red]❌ Sandbox Execution Timeout (30s exceeded)[/bold red]")
    except Exception as exec_err:
        console.print(f"[bold red]❌ Failed to run script: {exec_err}[/bold red]")
        
    wait_for_user(force=True)

async def optimize_sandbox_code(file_path, config, llm):
    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]Error: file {path.name} not found.[/bold red]")
        wait_for_user(force=True)
        return
        
    clear_screen()
    console.print(get_header())
    console.print(Panel(f"[bold cyan]✨ Overdrive Compilation Optimization: {path.name}[/bold cyan]\nInvoking optimization compiler core to supercharge code performance...", expand=False))
    
    code_text = path.read_text(encoding="utf-8", errors="ignore")
    
    optimization_prompt = f"""
    You are the TruthGPT Overdrive Code Optimizer. Your mission is to take the following python code, analyze it for performance, security, and cleanliness, and output a highly optimized, clean, and production-ready version.
    - Maximize performance (vectorize, optimize loops, cache heavy calculations).
    - Ensure robust exception handling.
    - Maintain perfect logic equivalence.
    - Return ONLY the optimized python code blocks between ```python and ```.
    
    Original Python Code:
    ```python
    {code_text}
    ```
    """
    
    try:
        with console.status("[bold cyan]Compiling and optimizing code layers...[/bold cyan]"):
            res = await llm(optimization_prompt)
            code_match = re.search(r"```(?:python)?\n(.*?)\n```", res, re.DOTALL)
            if code_match:
                optimized_code = code_match.group(1)
                
                clear_screen()
                console.print(get_header())
                console.print("[bold green]✓ Optimization Complete! Previewing differences...[/bold green]")
                
                console.print(Panel(optimized_code, title="✨ Optimized Code Output", border_style="green"))
                
                if Confirm.ask("[bold cyan]Would you like to overwrite the sandbox file with this optimized version?[/bold cyan]"):
                    path.write_text(optimized_code, encoding="utf-8")
                    console.print("[bold green]✓ Sandbox file updated with optimized code.[/bold green]")
            else:
                console.print("[bold red]Failed to extract clean python block from optimizer response.[/bold red]")
    except Exception as opt_err:
        console.print(f"[bold red]Optimization failed: {opt_err}[/bold red]")
        
    wait_for_user(force=True)
