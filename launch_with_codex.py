#!/usr/bin/env python3
"""
🚀 TruthGPT — OpenAI Codex Powered Unified Launcher
=====================================================
Seamlessly bootstraps TruthGPT using OpenAI Codex while preserving
100% of TruthGPT's interfaces, menus, swarms, research modules,
and formal verification capabilities.
"""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure proper encoding on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure current directory and parents are in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(CURRENT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich.text import Text
from rich.columns import Columns

console = Console(width=110)


def get_codex_status() -> Dict[str, Any]:
    """Inspects the local OpenAI Codex installation and environment."""
    status = {
        "cli_installed": False,
        "cli_version": "Not detected",
        "cli_path": None,
        "python_sdk": False,
        "python_sdk_version": "Unknown",
        "cloned_repo": False,
        "repo_path": str(CURRENT_DIR / "openai_codex"),
    }

    # Check CLI binary
    codex_bin = shutil.which("codex") or shutil.which("codex.cmd")
    if codex_bin:
        status["cli_installed"] = True
        status["cli_path"] = codex_bin
        try:
            res = subprocess.run([codex_bin, "--version"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                status["cli_version"] = res.stdout.strip()
        except Exception:
            status["cli_version"] = "Installed"

    # Check Python SDK
    try:
        import openai_codex
        status["python_sdk"] = True
        status["python_sdk_version"] = getattr(openai_codex, "__version__", "0.163.0")
    except ImportError:
        status["python_sdk"] = False

    # Check cloned repo
    repo_dir = CURRENT_DIR / "openai_codex"
    if repo_dir.exists() and (repo_dir / "codex-cli").exists():
        status["cloned_repo"] = True

    return status


def render_header(status: Dict[str, Any]) -> Panel:
    """Render a premium header showing TruthGPT and Codex status."""
    title_text = Text()
    title_text.append("🚀 TruthGPT ", style="bold cyan")
    title_text.append("× ", style="bold white")
    title_text.append("OpenAI Codex ", style="bold green")
    title_text.append("System 6.0 Orchestration Engine\n", style="bold yellow")
    title_text.append("Formal AI Operating System with Neural-Symbolic Reasoning & SOTA Swarm\n\n", style="dim white")

    # Status pills
    cli_color = "green" if status["cli_installed"] else "yellow"
    sdk_color = "green" if status["python_sdk"] else "yellow"
    repo_color = "green" if status["cloned_repo"] else "red"

    title_text.append(f"● Codex CLI: ", style="bold white")
    title_text.append(f"{status['cli_version']} ", style=cli_color)
    title_text.append(" | ", style="dim")
    title_text.append(f"● Python SDK: ", style="bold white")
    title_text.append(f"{status['python_sdk_version']} ", style=sdk_color)
    title_text.append(" | ", style="dim")
    title_text.append(f"● Codex Core Repo: ", style="bold white")
    title_text.append("Synchronized " if status["cloned_repo"] else "Missing ", style=repo_color)

    return Panel(
        Align.center(title_text),
        title="[bold bright_magenta] TRUTHGPT COMMAND CENTER [/bold bright_magenta]",
        subtitle="[bold dim]Preserving 100% of TruthGPT native menus and verification pipelines[/bold dim]",
        border_style="bright_blue",
        padding=(1, 2)
    )


def render_menu() -> Panel:
    """Render the interactive launch mode choices."""
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=None,
        padding=(0, 2)
    )
    table.add_column("Key", style="bold yellow", width=5, justify="center")
    table.add_column("Interface / Mode", style="bold white", width=36)
    table.add_column("Architecture & Features", style="dim white")

    options = [
        ("1", "🚀 TruthGPT Interactive TUI Dashboard", "Full prompt_toolkit TUI, 16+ menus, Swarm Fusion & Paper Registry (Codex active)"),
        ("2", "🎨 Modern Claude-Style Dual UI", "Split-screen conversational interface with live embedded command terminal"),
        ("3", "⚡ Enhanced TruthGPT CLI", "Rich command-line console with SOTA optimization flags and interactive shell"),
        ("4", "🤖 Codex-TruthGPT Swarm Co-Pilot", "Autonomous collaborative agent session pairing Codex with TruthGPT Swarm"),
        ("5", "📊 TruthGPT Cloud & Monetization Server", "FastAPI verification portal and Stripe billing dashboard at http://localhost:8080"),
        ("6", "🖥️ Interactive OpenAI Codex Terminal", "Native Codex CLI workspace session directly attached to optimization_core"),
        ("7", "🔧 Codex Auth & Diagnostic Tools", "Run 'codex login' or 'codex doctor' to configure account and verify environment"),
        ("0", "❌ Exit", "Return to shell")
    ]

    for key, name, desc in options:
        table.add_row(f"[{key}]", name, desc)

    return Panel(
        table,
        title="[bold green] Select Startup Mode [/bold green]",
        border_style="cyan",
        padding=(1, 1)
    )


def activate_codex_in_truthgpt():
    """Ensure Codex is preferred in user preferences and registry."""
    os.environ["TRUTHGPT_USE_CODEX"] = "1"
    os.environ["TRUTHGPT_PREFERRED_ENGINE"] = "codex"

    try:
        from agents.framework.engines.engine_registry import EngineRegistry
        from agents.framework.engines.engine_providers import CodexProvider
        reg = EngineRegistry()
        reg.register("codex", CodexProvider)
        reg.register("openai_codex", CodexProvider)
    except Exception as e:
        console.print(f"[dim]Engine registration notice: {e}[/dim]")


def launch_tui_dashboard():
    """Launch TruthGPT Full Interactive TUI Dashboard without losing anything."""
    console.print("\n[bold cyan]● Booting TruthGPT Kernel with OpenAI Codex Orchestration...[/bold cyan]")
    activate_codex_in_truthgpt()

    # Launch main.py
    script_path = str(CURRENT_DIR / "main.py")
    try:
        # Import and run async kernel loop directly if running in interactive console
        import main
        asyncio.run(main.main_loop())
    except Exception as e:
        # Fallback to subprocess execution
        subprocess.run([sys.executable, script_path, "--codex"])


def launch_modern_claude_ui():
    """Launch TruthGPT Modern Claude-style UI."""
    console.print("\n[bold cyan]● Launching Modern Claude-Style UI with Codex assistance...[/bold cyan]")
    activate_codex_in_truthgpt()
    try:
        from interface.modern_claude_ui import main as modern_main
        modern_main()
    except Exception as e:
        console.print(f"[bold red]Failed to launch Modern UI: {e}[/bold red]")


def launch_enhanced_cli():
    """Launch TruthGPT Enhanced CLI."""
    console.print("\n[bold cyan]● Launching TruthGPT Enhanced CLI...[/bold cyan]")
    activate_codex_in_truthgpt()
    subprocess.run([sys.executable, str(CURRENT_DIR / "enhanced_cli.py"), "interactive"])


def launch_codex_swarm_copilot():
    """Launch an autonomous cooperative session between Codex and TruthGPT Swarm."""
    console.print("\n[bold green]● Initializing Codex-TruthGPT Swarm Co-Pilot...[/bold green]")
    activate_codex_in_truthgpt()

    console.print(Panel(
        "[bold white]You are in the Codex-TruthGPT Swarm Co-Pilot session.[/bold white]\n"
        "[dim]Enter any prompt or programming goal. TruthGPT's multi-agent swarm will coordinate with OpenAI Codex.[/dim]\n"
        "[dim]Type 'exit' or 'back' to return to the launcher.[/dim]",
        border_style="green",
        title="🤖 Swarm Co-Pilot"
    ))

    while True:
        try:
            user_prompt = Prompt.ask("\n[bold cyan]Codex-TruthGPT ❯[/bold cyan]")
            if not user_prompt or user_prompt.strip().lower() in ["exit", "back", "quit"]:
                break

            console.print("[dim cyan]Swarm researching and executing with OpenAI Codex...[/dim cyan]")

            # Run with openai_codex or fallback to codex exec
            answered = False
            try:
                import openai_codex
                if hasattr(openai_codex, "Codex"):
                    with openai_codex.Codex() as codex:
                        thread = codex.thread_start()
                        res = thread.run(user_prompt)
                        ans = getattr(res, "final_response", str(res))
                        console.print(Panel(ans, title="[bold green]OpenAI Codex Output[/bold green]", border_style="green"))
                        answered = True
            except Exception as e:
                console.print(f"[dim yellow]Direct SDK call bypassed: {e}. Trying CLI...[/dim yellow]")

            if not answered:
                codex_bin = shutil.which("codex") or shutil.which("codex.cmd")
                if codex_bin:
                    res = subprocess.run([codex_bin, "exec", "--skip-git-repo-check", user_prompt], text=True, capture_output=True)
                    if res.returncode == 0 and res.stdout.strip():
                        console.print(Panel(res.stdout, title="[bold green]Codex CLI Output[/bold green]", border_style="green"))
                        answered = True
                    else:
                        if res.stderr:
                            console.print(f"[yellow]{res.stderr.strip()}[/yellow]")

            if not answered:
                # Swarm executive fallback
                from interface.comm_menu import handle_executive_prompt
                asyncio.run(handle_executive_prompt(user_prompt))

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]Error in Co-Pilot turn: {e}[/bold red]")


def launch_cloud_server():
    """Launch TruthGPT Cloud Server & Monetization Portal."""
    console.print("\n[bold cyan]● Starting TruthGPT Cloud Verification & Billing Server...[/bold cyan]")
    cloud_script = CURRENT_DIR / "truthgpt_cloud_server.py"
    if cloud_script.exists():
        subprocess.run([sys.executable, str(cloud_script)])
    else:
        console.print("[red]truthgpt_cloud_server.py not found.[/red]")


def launch_native_codex_cli():
    """Launch native interactive Codex CLI."""
    codex_bin = shutil.which("codex") or shutil.which("codex.cmd")
    if codex_bin:
        console.print(f"[green]Starting native Codex CLI: {codex_bin}[/green]")
        subprocess.run([codex_bin])
    else:
        console.print("[red]Codex CLI binary not found in PATH.[/red]")


def launch_codex_tools():
    """Manage Codex configuration and diagnostics."""
    codex_bin = shutil.which("codex") or shutil.which("codex.cmd")
    console.print("\n[bold cyan]🔧 Codex Authentication & Diagnostics[/bold cyan]")
    console.print("  [1] Sign in with ChatGPT (browser)")
    console.print("  [2] Run Codex Doctor (diagnostics)")
    console.print("  [3] Manage MCP Servers for Codex")
    console.print("  [0] Back to main menu")

    sub_choice = Prompt.ask("\nSelect tool option", choices=["0", "1", "2", "3"], default="1")
    if sub_choice == "1" and codex_bin:
        subprocess.run([codex_bin, "login"])
    elif sub_choice == "2" and codex_bin:
        subprocess.run([codex_bin, "doctor"])
    elif sub_choice == "3" and codex_bin:
        subprocess.run([codex_bin, "mcp"])


def run_truthgpt_with_codex():
    """Main entrypoint loop for the launcher."""
    status = get_codex_status()

    # Check CLI flags for direct headless / shortcut boot
    if "--tui" in sys.argv or "-1" in sys.argv or "--codex" in sys.argv:
        launch_tui_dashboard()
        return
    if "--modern" in sys.argv or "-2" in sys.argv:
        launch_modern_claude_ui()
        return
    if "--cli" in sys.argv or "-3" in sys.argv:
        launch_enhanced_cli()
        return
    if "--copilot" in sys.argv or "-4" in sys.argv:
        launch_codex_swarm_copilot()
        return
    if "--cloud" in sys.argv or "-5" in sys.argv:
        launch_cloud_server()
        return
    if "--codex-cli" in sys.argv or "-6" in sys.argv:
        launch_native_codex_cli()
        return

    # Check for direct prompt execution
    for idx, arg in enumerate(sys.argv):
        if arg in ["--prompt", "-p"] and idx + 1 < len(sys.argv):
            prompt_text = sys.argv[idx + 1]
            activate_codex_in_truthgpt()
            from interface.comm_menu import handle_executive_prompt
            asyncio.run(handle_executive_prompt(prompt_text))
            return

    # Interactive Menu Loop
    while True:
        console.clear()
        console.print(render_header(status))
        console.print(render_menu())

        choice = Prompt.ask(
            "\n[bold bright_cyan]Select startup option[/bold bright_cyan]",
            choices=["0", "1", "2", "3", "4", "5", "6", "7"],
            default="1"
        )

        if choice == "0":
            console.print("[bold yellow]👋 Exiting TruthGPT Codex Launcher. Goodbye![/bold yellow]")
            break
        elif choice == "1":
            launch_tui_dashboard()
            break
        elif choice == "2":
            launch_modern_claude_ui()
            break
        elif choice == "3":
            launch_enhanced_cli()
            break
        elif choice == "4":
            launch_codex_swarm_copilot()
        elif choice == "5":
            launch_cloud_server()
        elif choice == "6":
            launch_native_codex_cli()
        elif choice == "7":
            launch_codex_tools()
            Prompt.ask("\nPress Enter to return to launcher...")


if __name__ == "__main__":
    try:
        run_truthgpt_with_codex()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(0)
