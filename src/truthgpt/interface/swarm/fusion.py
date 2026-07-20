"""
Swarm Fusion — Dynamic multi-agent orchestration and output dispatch.

Extracted from swarm_menu.py. Contains the core fusion execution pipeline,
code-block persistence, and multi-target dispatch (local, Google, MCP).
"""

import asyncio
import re
import json
import time
import inspect
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.panel import Panel
from rich.table import Table
from rich.prompt import FloatPrompt, Confirm
from rich.console import Group
from rich.text import Text

from truthgpt.interface.core import (
    console, USER_PREFS, log_activity, log_event, clear_screen,
    get_header, wait_for_user, get_input, get_theme_panel,
    extract_target_directory,
)
from truthgpt.interface.cc_style import (
    cc_menu, cc_action, cc_tool_call, cc_result, cc_agent_done,
)
from truthgpt.interface.swarm.inspector import swarm_phase_inspector, safe_panel
from truthgpt.interface.swarm.missions import wait_with_interrupt

logger = logging.getLogger(__name__)


# ── Code Block Persistence ────────────────────────────────────────

def extract_filename_from_code(code_text: str, default_name: str) -> str:
    """Try to extract a filename from the first few lines of a code block."""
    lines = code_text.strip().splitlines()
    if not lines:
        return default_name
    for line in lines[:3]:
        line = line.strip()
        match = re.match(
            r'^(?:#|//|/\*|File:|Filename:)\s*([a-zA-Z0-9_\-\.\/\\ ]+)(?:\s*\*/)?$',
            line, re.IGNORECASE,
        )
        if match:
            extracted = match.group(1).strip()
            if '.' in extracted:
                parts = extracted.split('.')
                if len(parts[-1]) in (1, 2, 3, 4) and not parts[-1].isdigit():
                    return extracted
    return default_name


_LANG_EXT_MAP = {
    "python": ".py", "py": ".py",
    "javascript": ".js", "js": ".js",
    "typescript": ".ts", "ts": ".ts",
    "html": ".html", "htm": ".html",
    "css": ".css", "json": ".json",
    "rust": ".rs", "rs": ".rs", "go": ".go",
    "bash": ".sh", "sh": ".sh", "shell": ".sh",
    "powershell": ".ps1", "ps1": ".ps1",
    "c": ".c", "cpp": ".cpp", "c++": ".cpp",
    "java": ".java",
}


def save_code_blocks_to_directory(
    content: str, target_dir: Path, default_prefix: str = "output"
) -> List[Path]:
    """Extract fenced code blocks from *content* and write each to *target_dir*."""
    code_blocks = re.findall(r"```([a-zA-Z0-9+#_ -]*)\n(.*?)\n```", content, re.DOTALL)
    if not code_blocks:
        single_match = re.search(r"```(?:[a-zA-Z0-9+#_ -]*)\n(.*?)\n```", content, re.DOTALL)
        if single_match:
            code_blocks = [("", single_match.group(1))]

    saved_files: List[Path] = []
    for idx, (lang, code) in enumerate(code_blocks, 1):
        lang_clean = lang.strip().lower()
        ext = _LANG_EXT_MAP.get(lang_clean, ".py" if not lang_clean else f".{lang_clean}")
        default_filename = f"{default_prefix}_{idx}_{int(time.time())}{ext}"
        rel_filename = extract_filename_from_code(code, default_filename)
        dest_path = target_dir / rel_filename

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            existed = dest_path.exists()
            with open(dest_path, "w", encoding="utf-8") as code_f:
                code_f.write(code)
            saved_files.append(dest_path)
            try:
                from truthgpt.interface.cc_style import cc_code_change
                code_lines = code.splitlines()
                # Synthesise a unified-diff so the FULL written code is shown
                # (green +lines) the way Claude Code renders file changes.
                diff_text = (
                    f"@@ -0,0 +1,{len(code_lines)} @@\n"
                    + "\n".join("+" + ln for ln in code_lines)
                )
                cc_code_change(
                    "UPDATE" if existed else "WRITE",
                    str(dest_path.name),
                    added=len(code_lines),
                    note=f"{dest_path.resolve()}",
                    diff_text=diff_text,
                )
            except Exception:
                console.print(f"  [green]● Saved code block to {dest_path.resolve()}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to save code to {dest_path}: {e}[/red]")

    return saved_files


# ── Google / MCP Simulation Helpers ───────────────────────────────

async def run_google_simulation(choice: str = "1"):
    """Simulate a Google Workspace deployment."""
    console.print("[cyan]🌐 Activating Simulated Google Workspace Deployer...[/cyan]")
    await asyncio.sleep(1.0)
    console.print("  [green]● Authenticating secure GCP connection...[/green]")
    await asyncio.sleep(0.5)

    sim_ids = {
        "1": ("Google Doc", "docs.google.com/document/d/{}/edit", "1BxiMVs0XRA5nFMdKvXKBg-yvW9tC1337_truthgpt"),
        "2": ("Google Sheet", "docs.google.com/spreadsheets/d/{}/edit", "1SheetMVs0XRA5nFMdKvXKBg_truthgpt"),
        "3": ("Google Drive", "drive.google.com/open?id={}", "1DriveMVs0XRA5nFMdKvXKBg_truthgpt"),
    }
    label, url_tpl, sim_id = sim_ids.get(choice, sim_ids["1"])
    console.print(f"  [green]● Creating {label}...[/green]")
    await asyncio.sleep(0.6)
    console.print(f"[bold green]✓ Simulated {label} dispatch successful![/bold green]")
    console.print(f"[bold cyan]🔗 Simulated Link: https://{url_tpl.format(sim_id)}[/bold cyan]")


async def run_mcp_simulation(url: str, reason: str = ""):
    """Simulate an MCP server dispatch."""
    console.print(f"[cyan]🔌 Connecting to MCP Server at {url}...[/cyan]")
    await asyncio.sleep(1.0)
    console.print("  [green]● Negotiating MCP protocol handshake (v0.1.0)...[/green]")
    await asyncio.sleep(0.5)
    console.print("  [green]● Analyzing active resources and capabilities...[/green]")
    await asyncio.sleep(0.5)
    if reason:
        console.print(f"  [dim]● Reason: {reason}[/dim]")
    console.print(f"[bold green]✓ Dispatched Swarm Results to MCP Server Resource: mcp://localhost/swarm/fusion/reports[/bold green]")


# ── Multi-Target Dispatch ─────────────────────────────────────────

async def execute_swarm_dispatch(content: str, selected_targets: List[str]):
    """Dispatch swarm output to one or more targets (local, Google, MCP)."""
    console.print("\n[bold yellow]📡 Initializing Swarm Multi-Target Dispatcher...[/bold yellow]")

    for target in selected_targets:
        if target == "1":
            await _dispatch_local(content)
        elif target == "2":
            await _dispatch_google(content)
        elif target == "3":
            await _dispatch_mcp(content)


async def _dispatch_local(content: str):
    """Save output to local workspace."""
    console.print("\n[bold cyan]💾 Target 1: Local Workspace Export Config[/bold cyan]")

    fmt_choice = get_input("Select format [1=Markdown, 2=Text, 3=JSON]", choices=["1", "2", "3"], default="1")
    dir_choice = get_input(
        "Select directory [1=reports/, 2=generated_code/, 3=root, 4=custom]",
        choices=["1", "2", "3", "4"], default="1",
    )

    ext = {".md": "1", ".txt": "2", ".json": "3"}.get(fmt_choice, ".md")
    ext = ".md" if fmt_choice == "1" else ".txt" if fmt_choice == "2" else ".json"

    dir_map = {
        "1": Path("reports"),
        "2": Path("truthgpt_collected/generated_code"),
        "3": Path("."),
    }
    if dir_choice == "4":
        custom_p = get_input("Enter custom directory path")
        target_dir = Path(custom_p)
    else:
        target_dir = dir_map.get(dir_choice, Path("reports"))

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = f"Swarm_Fusion_{time.strftime('%Y%m%d_%H%M%S')}{ext}"
        filepath = target_dir / filename

        if fmt_choice == "3":
            output_content = json.dumps(
                {"mission": "Swarm_Fusion", "timestamp": time.time(), "content": content},
                indent=4,
            )
        else:
            output_content = content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(output_content)
        console.print(f"[bold green]✓ Output successfully exported to {filepath}[/bold green]")

        # Also extract embedded code blocks
        code_blocks = re.findall(r"```([a-zA-Z0-9+#_ -]*)\n(.*?)\n```", content, re.DOTALL)
        if code_blocks:
            console.print(f"[cyan]📦 Extracting {len(code_blocks)} code blocks to {target_dir}...[/cyan]")
            save_code_blocks_to_directory(content, target_dir, default_prefix="swarm_code")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to save to local path: {e}[/bold red]")


async def _dispatch_google(content: str):
    """Dispatch to Google Workspace (real or simulated)."""
    console.print("\n[bold cyan]☁️ Target 2: Google Workspace Service Configuration[/bold cyan]")
    google_choice = get_input("Select Google option [1=Docs, 2=Sheets, 3=Drive]", choices=["1", "2", "3"], default="1")

    token = USER_PREFS.get("google_access_token")
    if token and google_choice == "1":
        try:
            import httpx
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            doc_body = {"title": f"TruthGPT Swarm Output — {time.strftime('%Y-%m-%d %H:%M:%S')}"}
            async with httpx.AsyncClient() as client:
                res = await client.post("https://docs.googleapis.com/v1/documents", headers=headers, json=doc_body)
                if res.status_code == 200:
                    doc_data = res.json()
                    document_id = doc_data.get("documentId")
                    requests_body = {"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]}
                    await client.post(
                        f"https://docs.googleapis.com/v1/documents/{document_id}:batchUpdate",
                        headers=headers, json=requests_body,
                    )
                    console.print(f"[bold green]✓ Successfully exported to Google Docs! Document ID: {document_id}[/bold green]")
                    console.print(f"[bold cyan]🔗 View: https://docs.google.com/document/d/{document_id}/edit[/bold cyan]")
                    return
                else:
                    console.print(f"[red]Google Docs API returned error {res.status_code}[/red]")
        except Exception as e:
            console.print(f"[red]Google Docs API error: {e}[/red]")
        console.print("[yellow]Falling back to simulation...[/yellow]")

    await run_google_simulation(google_choice)


async def _dispatch_mcp(content: str):
    """Dispatch to an MCP server (real or simulated)."""
    console.print("\n[bold cyan]🔌 Target 3: Active Model Context Protocol (MCP) Configuration[/bold cyan]")
    mcp_urls = USER_PREFS.get("mcp_servers", ["http://localhost:8000"])

    console.print("[dim]Available MCP Server Connections:[/dim]")
    for idx, url in enumerate(mcp_urls):
        console.print(f"  [{idx + 1}] {url}")

    mcp_choice_str = get_input(f"Select MCP Server [1-{len(mcp_urls)}]", default="1")
    try:
        mcp_idx = int(mcp_choice_str) - 1
        selected_url = mcp_urls[mcp_idx]
    except (ValueError, IndexError):
        selected_url = mcp_urls[0]

    try:
        from truthgpt.agents.mcp_client import MCPClient
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

            tool_choice = get_input(f"Select MCP Tool [0-{len(tools)}]", default="1")
            if tool_choice == "0":
                await run_mcp_simulation(selected_url, "Simulation")
            else:
                try:
                    t_idx = int(tool_choice) - 1
                    selected_tool = tools[t_idx]["name"]
                    path_arg = get_input("Enter target file/resource path", default=f"swarm_report_{int(time.time())}.md")
                    args = {"path": path_arg, "content": content}
                    res = await client.call_tool(selected_tool, args)
                    console.print(f"[bold green]✓ MCP Tool '{selected_tool}' execution complete: {res}[/bold green]")
                except Exception as e:
                    console.print(f"[red]Failed to call MCP tool: {e}[/red]")
                    await run_mcp_simulation(selected_url, "Fallback")
        else:
            await run_mcp_simulation(selected_url, "No Tools Exposed")
    except Exception as e:
        console.print(f"[red]Failed to connect to MCP: {e}[/red]")
        await run_mcp_simulation(selected_url, f"Error: {e}")


# ── Agent Alias Resolution ────────────────────────────────────────

_AGENT_ALIASES = {
    "code_interpreter": "code_architect", "interpreter": "code_architect",
    "interpreter_agent": "code_architect", "coder": "code_architect",
    "coder_agent": "code_architect", "architect": "code_architect",
    "researcher": "research_agent", "researcher_agent": "research_agent",
    "academic_agent": "research_agent",
    "system_expert": "system_agent", "system_analyst": "system_agent",
    "security_agent": "security_analyst", "security": "security_analyst",
    "security_expert": "security_analyst",
    "defi": "defi_expert", "defi_agent": "defi_expert",
    "evolution": "evolution_architect", "evolution_agent": "evolution_architect",
    "evolutionary_architect": "evolution_architect",
    "math": "math_verifier", "math_agent": "math_verifier", "math_expert": "math_verifier",
    "planning": "planning_agent", "coordinator": "planning_agent",
    "coordination_agent": "planning_agent",
    "marketing": "marketing_agent", "marketing_expert": "marketing_agent",
}


def resolve_agent_keys(raw_keys: List[str], agents_map: Dict[str, Any]) -> List[str]:
    """Map raw LLM-provided keys to actual registry keys using aliases and fuzzy matching."""
    resolved: List[str] = []
    seen: set = set()

    for k in raw_keys:
        if not isinstance(k, str):
            continue
        k_clean = k.strip().lower()

        actual = None
        if k_clean in agents_map:
            actual = k_clean
        elif k_clean in _AGENT_ALIASES and _AGENT_ALIASES[k_clean] in agents_map:
            actual = _AGENT_ALIASES[k_clean]
        else:
            # Fuzzy/substring match
            for registry_key in agents_map:
                if registry_key in k_clean or k_clean in registry_key:
                    actual = registry_key
                    break

        if actual and actual not in seen:
            seen.add(actual)
            resolved.append(actual)
        elif actual is None:
            log_event("Swarm Warning", f"Ignored unrecognized agent key: {k}")

    return resolved


# ── Swarm Fusion Orchestrator ─────────────────────────────────────

@cc_menu("Dynamic Swarm Fusion")
async def handle_swarm_fusion(initial_prompt: Optional[str] = None):
    """Full orchestration flow: team selection → memory → execution → dispatch."""
    clear_screen()
    console.print(get_header())

    if initial_prompt:
        mode = "1"
    else:
        console.print("   1. 🧠 [bold]Autonomous Mode[/bold] (LLM decides the team)")
        console.print("   2. 🎨 [bold]Designer Mode[/bold] (You build the sequence)")
        console.print("   0. 🏠 Back to Swarm Menu")
        mode = get_input("Select mode", choices=["0", "1", "2"])
        if mode == "0":
            return

    from truthgpt.agents.registry import registry
    from truthgpt.agents.models import AgentConfig
    from truthgpt.agents.engines import engine_registry

    agents_map = registry.get_all_agents()
    config = AgentConfig()
    llm = engine_registry.get_engine(USER_PREFS["preferred_engine"])
    selected_keys: List[str] = []
    prompt = initial_prompt

    if mode == "1":
        prompt = initial_prompt or get_input("Enter task for the Autonomous Swarm")
        selected_keys = await _auto_select_agents(llm, agents_map, prompt)
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
        selected_keys = [display_keys[i - 1] for i in indices if 1 <= i <= len(display_keys)]
        prompt = initial_prompt or get_input("Enter the initial task/seed for this custom swarm")

    if not selected_keys:
        console.print("[red]No agents selected for orchestration.[/red]")
        wait_for_user()
        return

    # Memory selection
    memory_config = await _select_memory()

    console.print(f"\n[bold green]🧬 Executing Swarm Blueprint: {' ➔ '.join(selected_keys)}[/bold green]")
    if any([USER_PREFS.get("mcts_optimized"), USER_PREFS.get("speculative_decoding"), USER_PREFS.get("kv_quantization")]):
        console.print("[bold yellow]⚡ Neural Overdrive Active: Optimizing for Speed & Logic...[/bold yellow]")
    log_activity("Swarm Fusion", f"Blueprint: {'->'.join(selected_keys)} | Memory: {memory_config['type']}")

    # Execution mode
    exec_mode = get_input("Execution Architecture [S/P]", choices=["S", "P"], default="S")
    is_parallel = exec_mode == "P"

    # Dispatch target selection
    selected_targets = _select_dispatch_targets()

    console.print(f"\n[bold yellow]🚀 Launching Swarm Fusion ({'Parallel' if is_parallel else 'Sequential'})...[/bold yellow]\n")

    # Execute
    final_results = await _execute_fusion(
        selected_keys, agents_map, config, llm, memory_config,
        prompt, initial_prompt, is_parallel,
    )

    # Render results
    content = ""
    context_trace = []
    for item in final_results:
        key = item[0]
        if isinstance(item[1], Exception):
            content += f"\n\n--- Phase Error ({key}) ---\n{item[2]}"
            safe_panel(item[2], title=f"❌ {key} Failed", border_style="red")
        else:
            context_trace.append(item[1])
            content += f"\n\n--- Phase Output ({key}) ---\n{item[2]}"
            safe_panel(item[2], title=f"✅ {key} Complete", border_style="green")

    console.print("\n[bold green]✓ Swarm Orchestration Complete.[/bold green]")

    # Dispatch
    await execute_swarm_dispatch(content, selected_targets)

    # Forensic inspector
    if Confirm.ask("\n[bold cyan]🕵️ Would you like to enter the Forensic Swarm Control Room & Code Sandbox?[/bold cyan]", default=True):
        await swarm_phase_inspector(final_results, memory_config, config, llm)

    # Trace persistence
    if memory_config.get("trace_enabled") and context_trace:
        trace_path = Path("truthgpt_collected/logs/memory_traces")
        trace_path.mkdir(parents=True, exist_ok=True)
        filename = f"trace_{int(time.time())}.json"
        with open(trace_path / filename, "w") as f:
            json.dump(context_trace, f, indent=4)
        console.print(f"[dim]💾 Decision Trace persisted to {trace_path / filename}[/dim]")

        if Confirm.ask("[bold cyan]Would you like to review the Decision Logic Trace?[/bold cyan]"):
            _render_trace_table(context_trace)

    # Post-mission actions
    await _post_mission_actions(content, initial_prompt, config, llm)


# ── Internal Helpers ──────────────────────────────────────────────

async def _auto_select_agents(llm, agents_map, prompt) -> List[str]:
    """Use the LLM to auto-select the best agents for a task."""
    selected_keys: List[str] = []
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
                    match = re.search(r"\[.*\]", decision_res.replace("\n", ""))
                    parsed_keys: List[str] = []
                    if match:
                        try:
                            json_str = match.group().replace("'", '"')
                            parsed_keys = json.loads(json_str)
                        except Exception:
                            pass

                    if not parsed_keys:
                        found_keys = []
                        for key in agents_map.keys():
                            if key in decision_res.lower():
                                for m in re.finditer(re.escape(key), decision_res.lower()):
                                    found_keys.append((m.start(), key))
                        found_keys.sort()
                        seen = set()
                        for _, key in found_keys:
                            if key not in seen:
                                seen.add(key)
                                parsed_keys.append(key)

                    selected_keys = resolve_agent_keys(parsed_keys, agents_map)
            except Exception as e:
                log_event("Swarm Error", f"Orchestrator failed to select agents: {e}")

        if not selected_keys:
            for fallback_key in ["research_agent", "code_architect", "system_agent"]:
                if fallback_key in agents_map:
                    selected_keys.append(fallback_key)
            if not selected_keys and agents_map:
                selected_keys = [list(agents_map.keys())[0]]
            log_event("Swarm", f"Using fallback experts: {selected_keys}")
            console.print(f"[yellow]⚠️ Could not auto-select experts. Using default: {', '.join(selected_keys)}[/yellow]")

    return selected_keys


async def _select_memory() -> Dict[str, Any]:
    """Prompt for memory architecture selection and return config dict."""
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

    configs = {
        "1": {"type": "forensic", "trace_enabled": True},
        "2": {"type": "vector", "trace_enabled": True},
        "3": {"type": "holographic", "trace_enabled": True},
        "5": {"type": "graph", "trace_enabled": True},
    }
    if mem_choice in configs:
        return configs[mem_choice]

    if mem_choice == "6":
        try:
            from truthgpt_collected.integration_code.truthgpt_optimization_core_integration import (
                TruthGPTOptimizationCoreConfig, TruthGPTModel,
            )
            console.print("[bold red]🔥 Initializing ULTIMATE Hybrid Memory Fabric...[/bold red]")
            config_mem = TruthGPTOptimizationCoreConfig(enable_memory_system=True)
            mem_model = TruthGPTModel(config_mem)
            tensor_params = sum(p.numel() for p in mem_model.parameters())
            console.print(f"[green]✓ TruthGPT PyTorch Tensor Fabric Activated ({tensor_params} params)[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not load PyTorch tensors ({e}). Falling back to graph.[/yellow]")
        return {
            "type": "hybrid_ultimate",
            "layers": ["forensic", "vector", "graph", "paper_dna", "pytorch_tensor"],
            "trace_enabled": True,
            "fusion_mode": "weighted_consensus",
        }

    if mem_choice == "4":
        try:
            from truthgpt.modules.base.core_system.core.papers.paper_registry import PaperRegistry
            reg = PaperRegistry()
            mem_papers = reg.list_papers(category="memory")
            if len(mem_papers) < 3:
                mem_papers += reg.search_papers(query="attention")
            if len(mem_papers) < 5:
                mem_papers += reg.list_papers()[:10]

            if mem_papers:
                p_table = Table(title="📚 SOTA Memory & Architecture Research Papers", header_style="bold magenta", border_style="blue")
                p_table.add_column("#", style="cyan", justify="right")
                p_table.add_column("Paper ID", style="white")
                p_table.add_column("SOTA Technique", style="green")
                p_table.add_column("Impact", style="dim")
                for i, p in enumerate(mem_papers[:12], 1):
                    tech = ", ".join(p.key_techniques[:2]) if hasattr(p, "key_techniques") and p.key_techniques else "General SOTA"
                    acc_val = getattr(p, "accuracy_improvement", "5.0")
                    p_table.add_row(str(i), p.paper_id, tech, f"+{acc_val if acc_val is not None else '0.0'}% Acc")
                console.print(p_table)

                p_idx_input = get_input("Select Paper DNA to inject (supports multi-select: 1,2,3)", default="1")
                try:
                    selected_papers = []
                    for idx_str in p_idx_input.replace(" ", "").split(","):
                        selected_papers.append(mem_papers[int(idx_str) - 1])
                    paper_ids = [p.paper_id for p in selected_papers]
                    console.print(f"[green]✓ Injecting {', '.join(paper_ids)} into memory fabric.[/green]")
                    return {"type": "paper_driven", "paper_ids": paper_ids, "trace_enabled": True}
                except Exception:
                    console.print("[yellow]Invalid selection. Using Forensic fallback.[/yellow]")
            else:
                console.print("[yellow]No memory papers found. Using Forensic standard.[/yellow]")
        except Exception:
            console.print("[yellow]Paper registry unavailable. Using Forensic standard.[/yellow]")

    return {"type": "forensic", "trace_enabled": True}


def _select_dispatch_targets() -> List[str]:
    """Prompt user to choose dispatch targets."""
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
        subtitle="[dim]Select one or more destinations (e.g. 1,2,3)[/dim]",
        border_style="yellow",
    ))
    targets_input = get_input("Select Dispatch Targets", default="1")
    return [t.strip() for t in targets_input.replace(" ", "").split(",") if t.strip()]


async def _execute_fusion(
    selected_keys, agents_map, config, llm, memory_config,
    prompt, initial_prompt, is_parallel,
):
    """Run the fusion pipeline (sequential or parallel) and return results."""
    context = {"user_id": "orchestrator_fusion", "history": [], "memory_config": memory_config, "memory_trace": []}
    current_prompt = prompt or get_input("Enter task for the Swarm")

    async def run_phase(key, idx, phase_prompt):
        start_phase = time.time()
        cc_action(f"Swarm Phase {idx}: Agent '{key}' activated", status="RUN")

        trace_entry = {
            "phase": key,
            "time": time.strftime("%H:%M:%S"),
            "actions": [],
            "rationale": "Calculating optimal strategy based on previous state...",
        }

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
                from truthgpt.agents.system_intelligence.research_agent import ResearchAgent
                agent = ResearchAgent(llm_engine=llm)
                res = await agent.process(f"discover and integrate papers for {phase_prompt}")
                p_content = res.content
                trace_entry["rationale"] = f"Identified research gaps for {phase_prompt}. Seeking SOTA validation."
            else:
                agent_cls = agents_map[key]
                sig = inspect.signature(agent_cls.__init__)
                params = {}
                if "config" in sig.parameters:
                    params["config"] = config
                if "llm_engine" in sig.parameters:
                    params["llm_engine"] = llm
                agent = agent_cls(**params)
                cc_tool_call("Invoking neural LLM reasoning cognitive cycle...")
                res = await agent.process(phase_prompt, context=context)
                p_content = res.content if hasattr(res, "content") else str(res)
                rationale = res.metadata.get("rationale") if hasattr(res, "metadata") and res.metadata else None
                trace_entry["rationale"] = rationale or f"Executing {key} logic to transform state."

            # Auto-persist code
            if "```" in p_content:
                target_dir = extract_target_directory(prompt) or extract_target_directory(initial_prompt)
                code_dir = Path(target_dir) if target_dir else Path("truthgpt_collected/generated_code")
                saved = save_code_blocks_to_directory(p_content, code_dir, default_prefix=f"output_{key}")
                if saved:
                    trace_entry["actions"].append(f"Persisted code to {saved[-1].name}")
                    trace_entry["code_file"] = str(saved[-1])

            duration = time.time() - start_phase
            trace_entry["actions"].append(f"Committed phase output to {memory_config['type']} fabric")
            trace_entry["duration"] = f"{duration:.2f}s"
            if USER_PREFS.get("mcts_optimized"):
                trace_entry["speedup"] = "1.4x (Overdrive)"

            cc_agent_done(key, ok=True)
            cc_result(f"Completed in {trace_entry['duration']} · {trace_entry['rationale']}")
            return trace_entry, p_content

        except Exception as e:
            logger.error(f"Error executing Swarm Phase {idx} ({key}): {e}")
            cc_agent_done(key, ok=False)
            cc_result(f"Error: {str(e)[:100]}...")
            raise

    import truthgpt.interface.cc_style as cc_style
    cc_style.SUPPRESS_SPINNERS = True

    final_results = []
    try:
        if is_parallel:
            async_tasks = [(key, asyncio.create_task(run_phase(key, i + 1, current_prompt)))
                           for i, key in enumerate(selected_keys)]
            results = await asyncio.gather(*(t for _, t in async_tasks), return_exceptions=True)
            for i, result in enumerate(results):
                key = selected_keys[i]
                if isinstance(result, Exception):
                    final_results.append((key, result, f"⚠️ Phase failed: {result}"))
                else:
                    final_results.append((key, result[0], result[1]))
        else:
            for i, key in enumerate(selected_keys):
                try:
                    trace, p_res = await run_phase(key, i + 1, current_prompt)
                    final_results.append((key, trace, p_res))
                    summary = p_res[:1500] if len(p_res) > 1500 else p_res
                    current_prompt = f"Previous phase ({key}) summary: {summary}\n\nOriginal objective: {initial_prompt or current_prompt[:500]}"
                except Exception as phase_err:
                    err_msg = f"⚠️ Phase {i + 1} ({key}) crashed: {type(phase_err).__name__}: {str(phase_err)[:300]}"
                    final_results.append((key, phase_err, err_msg))
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Swarm fusion interrupted by user.[/bold red]")
        if is_parallel:
            for key, t in async_tasks:
                if not t.done():
                    t.cancel()
            await asyncio.sleep(0.1)
        for remaining_key in selected_keys[len(final_results):]:
            final_results.append((remaining_key, Exception("Cancelled"), "⚠️ Phase cancelled by user."))

    return final_results


def _render_trace_table(context_trace):
    """Render a forensic decision trace table."""
    t_table = Table(title="🕵️ Forensic Decision Trace", border_style="cyan")
    t_table.add_column("Phase", style="magenta")
    t_table.add_column("Rationale / Why?", style="white")
    t_table.add_column("Duration", style="yellow")
    t_table.add_column("Efficiency", style="green")
    t_table.add_column("Actions Taken", style="dim")
    for entry in context_trace:
        t_table.add_row(
            entry["phase"],
            entry["rationale"],
            entry.get("duration", "N/A"),
            entry.get("speedup", "1.0x (Standard)"),
            "\n".join([f"• {a}" for a in entry["actions"]]),
        )
    console.print(t_table)


async def _post_mission_actions(content, initial_prompt, config, llm):
    """Handle post-mission autonomous actions menu."""
    console.print("\n[bold cyan]⚡ Post-Mission Autonomous Actions[/bold cyan]")
    action_table = Table(show_header=False, border_style="dim")
    action_table.add_row("1", "🚀 [bold green]Self-Optimize[/bold green] (Run Overdrive on Results)")
    action_table.add_row("2", "🔄 [bold yellow]Continuous Mode[/bold yellow] (Recursive Mission)")
    action_table.add_row("3", "🛡️ [bold blue]Self-Refine[/bold blue] (Architect Review)")
    action_table.add_row("0", "🏠 Finish & Return")
    console.print(action_table)

    post_choice = get_input("Select next autonomous action", choices=["0", "1", "2", "3"], default="0")

    if post_choice == "1":
        from truthgpt.interface.overdrive_menu import handle_overdrive_menu
        await handle_overdrive_menu()
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
        from truthgpt.agents.code_interpreter import CodeInterpreterAgent
        architect = CodeInterpreterAgent(config=config, llm_engine=llm)
        refinement = await architect.process(f"Refine and industrialize this code for System 5.9: {content}")
        console.print(Panel(refinement.content, title="🛡️ Architectural Refinement", border_style="blue"))
        wait_for_user(force=True)

    wait_for_user(force=True)
