"""
Swarm Inspector — Forensic Control Room & Code Sandbox.

Extracted from swarm_menu.py for maintainability.
Provides phase inspection, code viewing/editing, sandbox execution, and optimization.
"""

import re
import sys
import time
import inspect
import subprocess
import logging
from pathlib import Path

from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Confirm

from interface.core import (
    console, USER_PREFS, clear_screen,
    get_header, wait_for_user, get_input, extract_target_directory,
)

logger = logging.getLogger(__name__)


# ── Utilities ─────────────────────────────────────────────────────

def safe_panel(text: str, title: str, border_style: str = "green", max_chars: int = 3000):
    """Render a Panel safely, truncating if content is too large."""
    try:
        display_text = (
            text if len(text) <= max_chars
            else text[:max_chars] + "\n\n[dim]... (output truncated for display)[/dim]"
        )
        console.print(Panel(display_text, title=title, border_style=border_style))
    except Exception as render_err:
        logger.warning(f"Panel render failed: {render_err}")
        console.print(f"\n[bold {border_style}]{title}[/bold {border_style}]")
        console.print(text[:500] if text else "(empty)")


# ── Phase Inspector ───────────────────────────────────────────────

async def swarm_phase_inspector(final_results, memory_config, config, llm):
    """Browse, inspect, and manipulate agent outputs and generated code."""
    while True:
        clear_screen()
        console.print(get_header())
        console.print(Panel(
            "[bold cyan]🕵️ Forensic Swarm Control Room & Code Sandbox[/bold cyan]\n"
            "Browse, inspect, and manipulate agent outputs and generated code in real time.",
            expand=False,
        ))

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
                has_code = (
                    "[bold green]Yes (Python)[/bold green]"
                    if "code_file" in trace else "No"
                )
            table.add_row(str(i), key, status_str, duration_str, actions_str, has_code)

        console.print(table)
        console.print(
            "\n[bold dim]Options:[/bold dim] Enter a phase number [1-{}] to inspect, "
            "[bold green]A[/bold green] to View All Panels, or "
            "[bold yellow]0[/bold yellow] to exit Control Room.".format(len(final_results))
        )

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
                    safe_panel(item[2], title=f"❌ {key} Failed", border_style="red")
                else:
                    safe_panel(item[2], title=f"✅ {key} Complete", border_style="green")
            wait_for_user(force=True)
            continue

        idx = int(choice) - 1
        await inspect_single_phase(final_results[idx], memory_config, config, llm)


# ── Single Phase Inspector ────────────────────────────────────────

async def inspect_single_phase(item, memory_config, config, llm):
    """Drill into a single swarm phase for detailed inspection and manipulation."""
    key = item[0]

    while True:
        clear_screen()
        console.print(get_header())
        console.print(Panel(f"[bold cyan]🕵️ Phase Control Room: {key}[/bold cyan]", expand=False))

        if isinstance(item[1], Exception):
            console.print(Panel(item[2], title="❌ Phase Error Traceback", border_style="red"))
            console.print("\n[bold yellow]0[/bold yellow] Back to Control Room")
            get_input("Press Enter to go back", choices=["0"], default="0")
            break

        trace = item[1]
        p_res = item[2]
        code_file_path = trace.get("code_file")

        # Details table
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
            clear_screen()
            console.print(Panel(p_res, title=f"📖 {key} Full Raw Output", border_style="cyan"))
            wait_for_user(force=True)
        elif sub_choice == "2" and code_file_path:
            await view_and_edit_code(code_file_path)
        elif sub_choice == "3" and code_file_path:
            await execute_sandbox_code(code_file_path)
        elif sub_choice == "4" and code_file_path:
            await optimize_sandbox_code(code_file_path, config, llm)
        elif sub_choice == "5":
            await _rerun_phase(item, key, p_res, trace, config, llm)


async def _rerun_phase(item, key, p_res, trace, config, llm):
    """Re-run a phase with custom guidance."""
    guidance = get_input("Enter custom guidance / instructions to re-run this phase")
    if not guidance.strip():
        return

    console.print(f"[bold yellow]🔄 Re-running phase {key} with custom instructions...[/bold yellow]")
    new_prompt = f"Additional user instruction: {guidance}\n\nOriginal context: {p_res}"
    try:
        console.print(f"[bold cyan]Invoking {key} for refinement...[/bold cyan]")

        if key == "arxiv_discovery_scout":
            from agents.system_intelligence.research_agent import ResearchAgent
            agent = ResearchAgent(llm_engine=llm)
            res = await agent.process(new_prompt)
        else:
            from agents.registry import registry
            agents_map = registry.get_all_agents()
            agent_cls = agents_map[key]
            sig = inspect.signature(agent_cls.__init__)
            params = {}
            if "config" in sig.parameters:
                params["config"] = config
            if "llm_engine" in sig.parameters:
                params["llm_engine"] = llm
            agent = agent_cls(**params)
            res = await agent.process(new_prompt)

        new_content = res.content if hasattr(res, "content") else str(res)
        console.print(Panel(new_content, title=f"✨ Refined {key} Output", border_style="green"))

        # Update item in-place (item is a list/tuple — only works if list)
        try:
            item[2] = new_content
        except TypeError:
            pass

        if "```" in new_content:
            target_dir = extract_target_directory(guidance)
            if not target_dir:
                target_dir = Path("truthgpt_collected/generated_code")
            from interface.swarm.fusion import save_code_blocks_to_directory
            saved = save_code_blocks_to_directory(new_content, target_dir, default_prefix=f"output_{key}")
            if saved:
                trace["code_file"] = str(saved[-1])
                console.print(f"[bold green]✓ Persisted new refined code to {saved[-1].name}[/bold green]")
        wait_for_user(force=True)
    except Exception as rerun_err:
        console.print(f"[bold red]Rerun failed: {rerun_err}[/bold red]")
        wait_for_user(force=True)


# ── Code Viewer & Editor ─────────────────────────────────────────

async def view_and_edit_code(file_path):
    """View and optionally edit a generated code file."""
    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]Error: file {path.name} not found.[/bold red]")
        wait_for_user(force=True)
        return

    while True:
        clear_screen()
        console.print(get_header())
        console.print(Panel(
            f"[bold green]📝 Code Inspector: {path.name}[/bold green]\n"
            f"Located at: [dim]{path.resolve()}[/dim]",
            expand=False,
        ))

        code_text = path.read_text(encoding="utf-8", errors="ignore")
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


# ── Sandbox Execution ─────────────────────────────────────────────

async def execute_sandbox_code(file_path):
    """Execute a Python file in an isolated subprocess."""
    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]Error: file {path.name} not found.[/bold red]")
        wait_for_user(force=True)
        return

    clear_screen()
    console.print(get_header())
    console.print(Panel(
        f"[bold yellow]🚀 Sandbox Execution: {path.name}[/bold yellow]\n"
        "Running code in isolated Python process...",
        expand=False,
    ))

    start_time = time.time()
    try:
        res = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True, text=True, timeout=30,
        )
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


# ── Code Optimization ─────────────────────────────────────────────

async def optimize_sandbox_code(file_path, config, llm):
    """Invoke the LLM to optimize a code file for performance and robustness."""
    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]Error: file {path.name} not found.[/bold red]")
        wait_for_user(force=True)
        return

    clear_screen()
    console.print(get_header())
    console.print(Panel(
        f"[bold cyan]✨ Overdrive Compilation Optimization: {path.name}[/bold cyan]\n"
        "Invoking optimization compiler core to supercharge code performance...",
        expand=False,
    ))

    code_text = path.read_text(encoding="utf-8", errors="ignore")
    optimization_prompt = (
        "You are the TruthGPT Overdrive Code Optimizer. Your mission is to take the following python code, "
        "analyze it for performance, security, and cleanliness, and output a highly optimized, clean, and "
        "production-ready version.\n"
        "- Maximize performance (vectorize, optimize loops, cache heavy calculations).\n"
        "- Ensure robust exception handling.\n"
        "- Maintain perfect logic equivalence.\n"
        "- Return ONLY the optimized python code blocks between ```python and ```.\n\n"
        f"Original Python Code:\n```python\n{code_text}\n```"
    )

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
