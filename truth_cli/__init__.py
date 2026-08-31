import sys
import os
import io

# Fix Windows cp1252 encoding crash with emojis
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import typer
import asyncio
from .core import setup_paths

# Ensure paths are set up before any other imports
setup_paths()

app = typer.Typer(
    name="truth",
    help="🚀 TruthGPT CLI - Enterprise ML & Optimization Platform",
    add_completion=True,
    no_args_is_help=False
)

# Sub-app registration
swarm_app = typer.Typer(name="swarm", help="🐝 Multi-agent swarm orchestration commands")
app.add_typer(swarm_app)

papers_app = typer.Typer(name="papers", help="📄 SOTA research paper discovery commands")
app.add_typer(papers_app)

plugins_app = typer.Typer(name="plugins", help="🔌 Plugin management and discovery")
app.add_typer(plugins_app)

cloud_app = typer.Typer(name="cloud", help="💎 TruthGPT Cloud subscriptions, formal verification & SaaS")
app.add_typer(cloud_app)

# Optimization: Only load command modules if we're actually calling a subcommand
# This significantly speeds up the minimalist dashboard entry point.
if len(sys.argv) > 1 and sys.argv[1] not in ["--help", "-h"]:
    from .model_cmds import register_model_commands
    from .system_cmds import register_system_commands
    from .swarm_cmds import register_swarm_commands
    from .paper_cmds import register_paper_commands
    from .plugin_cmds import register_plugin_commands
    from .continuity_cmds import register_continuity_commands
    from .cloud_cmds import register_cloud_commands

    register_model_commands(app)
    register_system_commands(app)
    register_swarm_commands(swarm_app)
    register_paper_commands(papers_app)
    register_plugin_commands(plugins_app)
    register_continuity_commands(app)
    register_cloud_commands(cloud_app)

@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """Default callback that launches the dashboard if no command is provided."""
    if ctx.invoked_subcommand is None:
        # Load the main.py that sits next to this package by explicit path, so we
        # can never accidentally import a stray "main" module from another clone
        # on sys.path (the cause of "cannot import name 'main_loop' from 'main'").
        import importlib.util
        from pathlib import Path

        main_path = Path(__file__).resolve().parent.parent / "main.py"
        if not main_path.exists():
            raise SystemExit(f"Entry point not found: {main_path}")

        spec = importlib.util.spec_from_file_location("main", main_path)
        main_mod = importlib.util.module_from_spec(spec)
        # Register before exec so intra-repo `from main import kernel` resolves here.
        sys.modules["main"] = main_mod
        spec.loader.exec_module(main_mod)

        if not hasattr(main_mod, "main_loop"):
            raise SystemExit(
                f"'main_loop' is missing from {main_path}. The loaded file may be "
                "from a different/older TruthGPT version."
            )

        try:
            asyncio.run(main_mod.main_loop())
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    app()
