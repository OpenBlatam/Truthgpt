"""
Core Utilities & Shared State for TruthGPT Interface
"""
import os
import sys
import time
import json
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

# Load .env variables from workspace root
try:
    from dotenv import load_dotenv
    # Find the workspace root (e.g., containing '.git' or named 'blatam-academy')
    _current = Path(__file__).resolve().parent
    _workspace_env = None
    for _ in range(20):
        if (_current / ".git").exists() or _current.name == "blatam-academy":
            if (_current / ".env").exists():
                _workspace_env = _current / ".env"
                break
        if _current.parent == _current:
            break
        _current = _current.parent
    
    # If we found the workspace root env, load it with override=True to prioritize it
    if _workspace_env:
        load_dotenv(_workspace_env, override=True)
    else:
        # Fallback to standard local upward search
        _current = Path(__file__).resolve().parent
        for _ in range(10):
            _env_path = _current / ".env"
            if _env_path.exists():
                load_dotenv(_env_path, override=True)
                break
            if _current.parent == _current:
                break
            _current = _current.parent
except Exception:
    pass

# Heavy imports deferred for speed
_console = None

def get_console():
    global _console
    if _console is None:
        from rich.console import Console
        _console = Console()
    return _console

class LazyConsole:
    def __getattr__(self, name):
        return getattr(get_console(), name)
    def __repr__(self):
        return repr(get_console())
    def __enter__(self):
        return get_console().__enter__()
    def __exit__(self, exc_type, exc_val, exc_tb):
        return get_console().__exit__(exc_type, exc_val, exc_tb)

console = LazyConsole()
# psutil and ctypes moved to lazy handlers for speed

# Lazy load flags
_HAS_PROMPT_TOOLKIT = None

def _check_prompt_toolkit():
    global _HAS_PROMPT_TOOLKIT
    if _HAS_PROMPT_TOOLKIT is None:
        try:
            import prompt_toolkit
            _HAS_PROMPT_TOOLKIT = True
        except ImportError:
            _HAS_PROMPT_TOOLKIT = False
    return _HAS_PROMPT_TOOLKIT

def disable_quick_edit():
    """Disables QuickEdit mode in Windows Terminal to allow mouse clicks to be captured by the app."""
    if os.name == 'nt':
        import ctypes
        try:
            kernel32 = ctypes.windll.kernel32
            h_input = kernel32.GetStdHandle(-10) # STD_INPUT_HANDLE
            mode = ctypes.c_uint()
            kernel32.GetConsoleMode(h_input, ctypes.byref(mode))
            
            # Disable QuickEdit (0x0040)
            # Enable Mouse Input (0x0010)
            # Enable Extended Flags (0x0080)
            # Enable Window Input (0x0008)
            new_mode = (mode.value & ~0x0040) | 0x0010 | 0x0080 | 0x0008
            kernel32.SetConsoleMode(h_input, new_mode)
            
            # Also try to enable Virtual Terminal Processing for output
            h_output = kernel32.GetStdHandle(-11) # STD_OUTPUT_HANDLE
            out_mode = ctypes.c_uint()
            kernel32.GetConsoleMode(h_output, ctypes.byref(out_mode))
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(h_output, out_mode.value | 0x0004)
        except Exception:
            pass

# Initialize Console (Quickly)
disable_quick_edit()
# console is already a LazyConsole proxy

# --- Path Initialization ---
current_dir = Path(__file__).resolve().parent.parent
CONFIG_PATH = current_dir / "user_preferences.json"

def load_user_prefs() -> Dict[str, Any]:
    defaults = {
        "user_name": "Explorer", 
        "preferred_engine": "deepseek", 
        "theme": "claude",
        "continuous_mode": False,
        "mcp_servers": ["http://localhost:8000"],
        "api_keys": {
            "telegram": "",
            "discord": "",
            "slack": "",
            "whatsapp": "",
            "openai": "",
            "deepseek": "",
            "anthropic": "",
            "google": "",
            "openrouter": ""
        },
        "api_credits": {
            "claude": 10.00,
            "openai": 10.00,
            "google": 10.00
        },
        "ensemble_mode": "race",
        "google_access_token": "",
        "google_service_account": ""
    }
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text())
            if isinstance(loaded, dict):
                if "api_keys" in loaded and isinstance(loaded["api_keys"], dict):
                    defaults["api_keys"].update(loaded["api_keys"])
                if "api_credits" in loaded and isinstance(loaded["api_credits"], dict):
                    defaults["api_credits"].update(loaded["api_credits"])
                defaults.update(loaded)
        except Exception:
            # Corruption detected - rename file to heal system state and boot defaults
            try:
                corrupt_backup = CONFIG_PATH.with_suffix(".corrupt")
                if CONFIG_PATH.exists():
                    if corrupt_backup.exists():
                        corrupt_backup.unlink()
                    CONFIG_PATH.rename(corrupt_backup)
            except Exception:
                pass
    return defaults

def save_user_prefs(prefs: Dict[str, Any]):
    try:
        # Atomic write: write to temp file first, then rename/replace
        temp_path = CONFIG_PATH.with_suffix(".tmp")
        temp_path.write_text(json.dumps(prefs, indent=4))
        if temp_path.exists():
            if CONFIG_PATH.exists():
                CONFIG_PATH.unlink()
            temp_path.rename(CONFIG_PATH)
    except Exception:
        # Fallback to direct write if rename/replace fails (e.g. windows locking)
        try:
            CONFIG_PATH.write_text(json.dumps(prefs, indent=4))
        except Exception as e:
            import logging
            logging.getLogger().error(f"Failed to write user preferences: {e}")
    _invalidate_llm_client_cache()


def _invalidate_llm_client_cache() -> None:
    """Force swarm/client to rebuild LLM engine after prefs change (ensemble, engines)."""
    try:
        import interface.swarm_menu as swarm_menu
        swarm_menu._client_cache = None
    except Exception:
        pass

USER_PREFS = load_user_prefs()

# Populate environment variables from USER_PREFS api_keys
if "api_keys" in USER_PREFS:
    key_mapping = {
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY"
    }
    for pref_key, env_key in key_mapping.items():
        val = USER_PREFS["api_keys"].get(pref_key)
        if val and not os.environ.get(env_key):
            os.environ[env_key] = val

# --- Global System State ---
SYSTEM_LOGS = []
system_history = []
background_missions = []
BLOCKCHAIN_READY = False

# Cached values for UI responsiveness
def _fast_count_papers() -> int:
    try:
        from pathlib import Path
        _current = Path(__file__).resolve().parent
        _workspace_root = None
        for _ in range(20):
            if (_current / ".git").exists() or _current.name == "blatam-academy":
                _workspace_root = _current
                break
            if _current.parent == _current:
                break
            _current = _current.parent
            
        if not _workspace_root:
            _workspace_root = Path(__file__).resolve().parent.parent # fallback
            
        p = _workspace_root / "truthgpt_collected" / "integration_code" / "papers"
        if p.exists():
            categories = ['research', 'architecture', 'inference', 'memory', 'redundancy', 'techniques', 'code', 'best']
            return sum(len(list(p.glob(d + '/paper_*.py'))) for d in categories if (p / d).exists())
    except Exception:
        pass
    return 66

_CACHED_PAPER_COUNT = _fast_count_papers()
_LAST_PAPER_SCAN = 0


def log_event(layer: str, event: str, status: str = "DONE"):
    timestamp = time.strftime("%H:%M:%S")
    SYSTEM_LOGS.append({"time": timestamp, "layer": layer, "event": event, "status": status})
    
    # Persist to cross-session history ledger
    try:
        from interface.history_menu import _persist_event
        from datetime import datetime
        _persist_event({
            "time": timestamp,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "layer": layer,
            "event": event,
            "status": status,
            "kind": "event",
        })
    except Exception:
        pass
    
    theme = USER_PREFS.get("theme", "industrial")
    if theme in ["claude", "anthropic", "minimalist"]:
        from interface.cc_style import cc_log_event
        cc_log_event(layer, event, status)
    else:
        # Standard industrial log
        console.print(f"[dim]{timestamp}[/dim] [[bold orange3]{layer.upper()}[/bold orange3]] [white]{event}[/white] -> [bold green]{status}[/bold green]")

def log_activity(module: str, task: str, status: str = "Completed"):
    timestamp = time.strftime('%H:%M:%S')
    system_history.append({
        "time": timestamp,
        "module": module,
        "task": task,
        "status": status
    })
    if len(system_history) > 20:
        system_history.pop(0)
    
    # Persist to cross-session history ledger
    try:
        from interface.history_menu import _persist_event
        from datetime import datetime
        _persist_event({
            "time": timestamp,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "module": module,
            "task": task,
            "status": status,
            "kind": "activity",
        })
    except Exception:
        pass
    
    theme = USER_PREFS.get("theme", "industrial")
    if theme in ["claude", "anthropic", "minimalist"]:
        from interface.cc_style import cc_log_activity
        cc_log_activity(module, task, status)

async def handle_personalize():
    from rich.panel import Panel
    from rich.table import Table
    while True:
        clear_screen()
        console.print(Panel("[bold yellow]👤 Personalization & Settings[/bold yellow]", border_style="yellow"))
        
        engines = USER_PREFS.get('preferred_engine', 'deepseek').split(',')
        engine_str = ", ".join([f"[cyan]{e.strip()}[/cyan]" for e in engines])
        
        table = Table(show_header=False, box=None)
        table.add_row("1. Change Name", f"[dim]Current: {USER_PREFS['user_name']}[/dim]")
        table.add_row("2. Set Engines (Multi-Engine Support)", f"[dim]Active: {engine_str}[/dim]")
        table.add_row("3. Ensemble Mode", f"[dim]Mode: {USER_PREFS.get('ensemble_mode', 'race')}[/dim]")
        table.add_row("4. UI Theme", f"[dim]Theme: {USER_PREFS.get('theme', 'industrial')}[/dim]")
        table.add_row("5. Google OAuth Token", f"[dim]Token: {'SET' if USER_PREFS.get('google_access_token') else 'EMPTY'}[/dim]")
        table.add_row("6. Google Service Account", f"[dim]Path: {USER_PREFS.get('google_service_account', 'EMPTY')}[/dim]")
        table.add_row("7. Set API Credit Balances (Claude/OpenAI/Gemini)", "[dim]Adjust offline starting estimates[/dim]")
        table.add_row("0. Back", "")
        console.print(table)
        
        choice = get_input("Select setting", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
        if choice == "0": break
        elif choice == "1":
            USER_PREFS["user_name"] = get_input("Enter your name", default=USER_PREFS["user_name"])
        elif choice == "2":
            from rich.table import Table
            
            available = ["deepseek", "google", "openrouter", "chatgpt", "claude"]
            
            table = Table(
                title="🧠 [bold cyan]Neural Reasoning Engines[/bold cyan]",
                border_style="cyan",
                header_style="bold magenta",
                show_lines=True
            )
            table.add_column("#", justify="center", style="bold cyan")
            table.add_column("Engine Name", style="bold white")
            table.add_column("Provider / Brand", style="dim")
            table.add_column("Default Model", style="green")
            table.add_column("API Key Status", justify="center")

            # Engine metadata map for display
            metadata = {
                "deepseek": ("DeepSeek", "deepseek-reasoner", "deepseek", "DEEPSEEK_API_KEY"),
                "google": ("Google Gemini", "gemini-2.0-flash-exp", "google", "GOOGLE_API_KEY"),
                "openrouter": ("OpenRouter Unified", "anthropic/claude-3.7-sonnet", "openrouter", "OPENROUTER_API_KEY"),
                "chatgpt": ("OpenAI (ChatGPT)", "gpt-4o", "openai", "OPENAI_API_KEY"),
                "claude": ("Anthropic Claude", "claude-3-7-sonnet-latest", "anthropic", "ANTHROPIC_API_KEY"),
            }

            for idx, eng in enumerate(available, 1):
                brand, model, pref_key, env_key = metadata[eng]
                
                # Check status
                key_configured = bool(
                    USER_PREFS.get("api_keys", {}).get(pref_key) or os.getenv(env_key)
                )
                status = "[bold green]Active[/bold green]" if key_configured else "[dim yellow]Key Missing[/dim yellow]"
                
                table.add_row(str(idx), eng, brand, model, status)
                
            console.print("\n[bold cyan]Select engines (comma-separated for ensemble):[/bold cyan]")
            console.print(table)
            
            selection = get_input("Engines", default=",".join(engines))
            # Resolve numbers to names if provided
            parts = [p.strip() for p in selection.split(",")]
            resolved = []
            for p in parts:
                if p.isdigit():
                    idx = int(p)
                    if 1 <= idx <= len(available):
                        resolved.append(available[idx-1])
                else:
                    resolved.append(p)
            
            # If openrouter is selected, show model sub-menu
            if "openrouter" in resolved:
                console.print("\n[bold yellow]⚡ OpenRouter Model Selection:[/bold yellow]")
                
                or_models = [
                    "anthropic/claude-3.7-sonnet",
                    "google/gemini-3.5-flash",
                    "google/gemini-3.5-pro",
                    "deepseek/deepseek-r1",
                    "openai/gpt-4.5-preview",
                    "deepseek/deepseek-chat",
                    "anthropic/claude-3.5-sonnet",
                    "openai/gpt-4o",
                    "meta-llama/llama-3.3-70b-instruct",
                    "qwen/qwen-2.5-72b-instruct"
                ]
                
                model_table = Table(
                    title="🌐 [bold cyan]Available OpenRouter Models[/bold cyan]",
                    border_style="yellow",
                    header_style="bold magenta",
                    show_lines=True
                )
                model_table.add_column("#", justify="center", style="bold yellow")
                model_table.add_column("Model ID", style="white")
                model_table.add_column("Friendly Name", style="dim")
                
                model_names = {
                    "anthropic/claude-3.7-sonnet": "Claude 3.7 Sonnet (Recommended)",
                    "google/gemini-3.5-flash": "Gemini 3.5 Flash",
                    "google/gemini-3.5-pro": "Gemini 3.5 Pro",
                    "deepseek/deepseek-r1": "DeepSeek R1 (Reasoning)",
                    "openai/gpt-4.5-preview": "GPT-4.5 (Research Preview)",
                    "deepseek/deepseek-chat": "DeepSeek V3 (Chat)",
                    "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet",
                    "openai/gpt-4o": "GPT-4o (Omni)",
                    "meta-llama/llama-3.3-70b-instruct": "Llama 3.3 70B Instruct",
                    "qwen/qwen-2.5-72b-instruct": "Qwen 2.5 72B Instruct"
                }
                
                for idx, model_id in enumerate(or_models, 1):
                    model_table.add_row(str(idx), model_id, model_names[model_id])
                
                console.print(model_table)
                
                model_choice = get_input("Select model # or enter custom model ID", default="1")
                selected_model = ""
                if model_choice.isdigit():
                    m_idx = int(model_choice)
                    if 1 <= m_idx <= len(or_models):
                        selected_model = or_models[m_idx - 1]
                    else:
                        selected_model = or_models[0]
                else:
                    selected_model = model_choice.strip() or or_models[0]
                
                # Replace 'openrouter' in resolved with 'openrouter:selected_model'
                for i, r in enumerate(resolved):
                    if r == "openrouter":
                        resolved[i] = f"openrouter:{selected_model}"
                        
                console.print(f"[bold green]✓[/bold green] Selected OpenRouter model: [bold white]{selected_model}[/bold white]")
            
            # Allow selecting custom model names for active standard engines!
            console.print("\n[bold cyan]🔧 Model Configuration Room:[/bold cyan]")
            USER_PREFS["engine_models"] = USER_PREFS.get("engine_models", {})
            clean_resolved = []
            for eng in resolved:
                # If there's a colon (e.g. openrouter:model), ignore it
                if ":" in eng:
                    clean_resolved.append(eng)
                    continue
                if eng in metadata:
                    brand, default_model, pref_key, env_key = metadata[eng]
                else:
                    brand, default_model, pref_key, env_key = eng.capitalize(), eng, eng, f"{eng.upper()}_API_KEY"
                current_model = USER_PREFS.get("engine_models", {}).get(eng, default_model)
                custom_m = get_input(f"➔ Enter active model for {brand} ({eng})", default=current_model)
                if "engine_models" not in USER_PREFS:
                    USER_PREFS["engine_models"] = {}
                val = custom_m.strip()
                if val.isdigit() or val == "":
                    val = current_model if (current_model and not current_model.isdigit()) else default_model
                USER_PREFS["engine_models"][eng] = val
                clean_resolved.append(eng)
            
            USER_PREFS["preferred_engine"] = ",".join(clean_resolved)
        elif choice == "3":
            console.print(
                "[dim]consensus = cluster vote · parallel = all answers · race = fastest engine · "
                "majority = similarity vote · debate = transcript + verdict · bayesian = confidence weights[/dim]"
            )
            USER_PREFS["ensemble_mode"] = get_input(
                "Ensemble Mode", 
                choices=["consensus", "parallel", "race", "majority", "debate", "bayesian"], 
                default=USER_PREFS.get("ensemble_mode", "race")
            )
        elif choice == "4":
            USER_PREFS["theme"] = get_input(
                "Select Theme", 
                choices=["industrial", "claude", "minimalist"], 
                default=USER_PREFS.get("theme", "industrial")
            )
        elif choice == "5":
            USER_PREFS["google_access_token"] = get_input("Paste Google OAuth Token", default=USER_PREFS.get("google_access_token", ""))
        elif choice == "6":
            USER_PREFS["google_service_account"] = get_input("Enter Service Account Path", default=USER_PREFS.get("google_service_account", ""))
        elif choice == "7":
            console.print("\n[bold yellow]💰 Adjust API Credit Balances[/bold yellow]")
            credits = USER_PREFS.setdefault("api_credits", {"claude": 10.00, "openai": 10.00, "google": 10.00})
            
            try:
                credits["claude"] = float(get_input("Claude starting credits ($USD)", default=str(credits.get("claude", 10.00))))
                credits["openai"] = float(get_input("OpenAI starting credits ($USD)", default=str(credits.get("openai", 10.00))))
                credits["google"] = float(get_input("Google starting credits ($USD)", default=str(credits.get("google", 10.00))))
            except ValueError:
                console.print("[red]❌ Invalid input. Please enter numbers only.[/red]")
                time.sleep(1.0)
                continue
            
        save_user_prefs(USER_PREFS)
        console.print("[green]✓ Settings updated.[/green]")
        time.sleep(0.5)


async def show_main_dashboard(extended: bool = False):
    theme = USER_PREFS.get("theme", "industrial")
    if theme in ["claude", "anthropic", "minimalist"]:
        from interface.cc_style import cc_divider, cc_action, cc_prompt_footer
        clear_screen()
        print(get_header())
        core_layers = [
            ("K", "🛡️ Kernel"), ("1", "🐝 Swarm"), ("2", "🚀 Frontier"), ("3", "🔍 Research")
        ]
        for lid, name in core_layers:
            console.print(f"  [bold orange3]{lid:>2}[/bold orange3]  [white]{name}[/white]")
        
        if extended:
            console.print()
            cc_action("ADVANCED & EXTERNAL LAYERS", status="INFO")
            advanced_layers = [
                ("4", "⚙️ Opts"), ("5", "🧠 Labs"), ("6", "📱 Comm"), 
                ("9", "⛓️ Web3"), ("10", "🖥️ Node"), ("11", "📜 Tasks"),
                ("13", "📊 Market"), ("15", "🤖 RL"), ("16", "⚡ Overdrive"),
                ("H", "📜 History"), ("P", "👤 Settings")
            ]
            from rich.columns import Columns
            cols = [f"  [bold cyan]{lid:>2}[/bold cyan] [white]{name}[/white]" for lid, name in advanced_layers]
            console.print(Columns(cols, equal=True, expand=True))
        else:
            console.print(f"\n [dim] (Type '99' or '+' to toggle Extended View) [/dim]")
        
        cc_prompt_footer(context_hint="TruthGPT OS v5.9", interrupt_hint="Type command ID")
        return

    clear_screen()
    console.print(get_header())
    
    core_layers = [
        ("K", "🛡️ Kernel"), ("1", "🐝 Swarm"), ("2", "🚀 Frontier"), ("3", "🔍 Research")
    ]
    for lid, name in core_layers:
        console.print(f"  [bold orange3]{lid:>2}[/bold orange3]  [white]{name}[/white]")
    
    if extended:
        console.print(f"\n [bold white]ADVANCED & EXTERNAL LAYERS[/bold white]\n")
        advanced_layers = [
            ("4", "⚙️ Opts"), ("5", "🧠 Labs"), ("6", "📱 Comm"), 
            ("9", "⛓️ Web3"), ("10", "🖥️ Node"), ("11", "📜 Tasks"),
            ("13", "📊 Market"), ("15", "🤖 RL"), ("16", "⚡ Overdrive"),
            ("H", "📜 History"), ("P", "👤 Settings")
        ]
        from rich.columns import Columns
        cols = [f"  [bold cyan]{lid:>2}[/bold cyan] [white]{name}[/white]" for lid, name in advanced_layers]
        console.print(Columns(cols, equal=True, expand=True))
    else:
        console.print(f"\n [dim] (Type '99' or '+' to toggle Extended View) [/dim]")

    console.print(f"\n [bold white]Type command ID or 'help' to begin.[/bold white]")


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def wait_for_user(force: bool = False, timeout: int = 15):
    if force or not USER_PREFS.get("continuous_mode", False):
        try:
            import msvcrt
            console.print(f"\n[dim]Press Enter to continue... (Auto-continuing in {timeout}s)[/dim]", end="")
            start_time = time.time()
            while time.time() - start_time < timeout:
                if msvcrt.kbhit():
                    msvcrt.getch()
                    console.print()
                    return
                time.sleep(0.1)
            console.print("\n[bold yellow]⌛ Idle timeout. Continuing autonomously...[/bold yellow]")
        except ImportError:
            console.input("\n[dim]Press Enter to continue...[/dim]")
    else:
        time.sleep(1)

def get_header() -> Panel:
    theme = USER_PREFS.get("theme", "industrial")
    if theme in ["claude", "anthropic", "minimalist"]:
        return get_claude_header()
    
    import shutil
    terminal_lines = shutil.get_terminal_size().lines or 24
    from rich.panel import Panel
    from rich.text import Text
    
    if terminal_lines < 30:
        return Panel(
            Text("🚀 TruthGPT Industrial OS  [bold red][R] Reboot[/bold red]", style="bold orange3", justify="center"),
            border_style="orange3",
            padding=(0, 1)
        )
    
    banner = r"""
   _____                      _      _____  _____  _______
  |_   _| __ _   _  | |_  | |_   / ____||  __ \|__   __|
    | |  |  __| | | | | __| | __| | |  __ | |__) |  | |
    | |  | |  | |_| | | |_  | |_  | |__  ||  ___/   | |
    |_|  |_|   \__,_|  \__|  \__|  \_____||_|       |_|
    """
    return Panel(
        Text(banner, style="bold orange3", justify="center"),
        title="[bold purple] TruthGPT Industrial OS [/bold purple]",
        subtitle=f"[bold orange3] truthgpt@kernel [/bold orange3]  [bold red][R] Reboot[/bold red]",
        border_style="orange3",
        padding=(1, 2)
    )

def get_real_budget_stats():
    """Reads actual API budget data from persistence."""
    path = ".api_cost_budget.json"
    stats = {"total_usd": 0.0, "savings_usd": 0.0, "limit": 2.0}
    if os.path.exists(path):
        try:
            import json
            with open(path, 'r') as f:
                data = json.load(f)
                stats["total_usd"] = data.get("metrics", {}).get("total_usd", 0.0)
                stats["savings_usd"] = data.get("savings_usd", 0.0)
        except: pass
    return stats

async def fetch_balances_background():
    """Background task to fetch real API balances without blocking the TUI."""
    import httpx
    import asyncio
    import logging
    import warnings
    
    # Enforce silencing of HTTP library logs to prevent TUI canvas overlap
    warnings.filterwarnings("ignore")
    for logger_name in ["httpx", "httpcore", "urllib3"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
        
    provider = TelemetryProvider
    if provider._BALANCE_FETCHING:
        return
    provider._BALANCE_FETCHING = True
    
    try:
        # Load keys safely
        prefs = load_user_prefs()
        api_keys = prefs.get("api_keys", {})
        
        # 1. Fetch DeepSeek Balance
        deepseek_key = api_keys.get("deepseek") or os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(
                        "https://api.deepseek.com/user/balance",
                        headers={"Authorization": f"Bearer {deepseek_key}"}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("is_available"):
                            infos = data.get("balance_infos", [])
                            if infos:
                                val = float(infos[0].get("total_balance", 0.0))
                                provider._CACHED_BALANCES["deepseek"] = {"val": val, "type": "API"}
            except Exception:
                pass

        # 2. Fetch OpenRouter Balance
        openrouter_key = api_keys.get("openrouter") or os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(
                        "https://openrouter.ai/api/v1/credits",
                        headers={"Authorization": f"Bearer {openrouter_key}"}
                    )
                    if resp.status_code == 200:
                        data = resp.json().get("data", {})
                        total_credits = data.get("total_credits")
                        total_usage = data.get("total_usage")
                        if total_credits is not None and total_usage is not None:
                            val = max(0.0, float(total_credits) - float(total_usage))
                            provider._CACHED_BALANCES["openrouter"] = {"val": val, "type": "API", "usage": float(total_usage)}
                        else:
                            resp_key = await client.get(
                                "https://openrouter.ai/api/v1/auth/key",
                                headers={"Authorization": f"Bearer {openrouter_key}"}
                            )
                            if resp_key.status_code == 200:
                                d_key = resp_key.json().get("data", {})
                                limit = d_key.get("limit")
                                usage = d_key.get("usage", 0.0)
                                if limit is not None and float(limit) > 0.0:
                                    val = max(0.0, float(limit) - float(usage))
                                else:
                                    val = None
                                provider._CACHED_BALANCES["openrouter"] = {"val": val, "type": "API", "usage": float(usage)}
                    else:
                        resp_key = await client.get(
                            "https://openrouter.ai/api/v1/auth/key",
                            headers={"Authorization": f"Bearer {openrouter_key}"}
                        )
                        if resp_key.status_code == 200:
                            d_key = resp_key.json().get("data", {})
                            limit = d_key.get("limit")
                            usage = d_key.get("usage", 0.0)
                            if limit is not None and float(limit) > 0.0:
                                val = max(0.0, float(limit) - float(usage))
                            else:
                                val = None
                            provider._CACHED_BALANCES["openrouter"] = {"val": val, "type": "API", "usage": float(usage)}
            except Exception:
                pass

        provider._LAST_BALANCE_UPDATE = time.time()
    except Exception:
        pass
    finally:
        provider._BALANCE_FETCHING = False

class TelemetryProvider:
    """Encapsulates system telemetry gathering with caching."""
    _SESSION_ID = None
    _LAST_CPU_VAL = 14.0
    _CACHED_STATS = None
    _LAST_UPDATE = 0
    
    # Live API balance cache
    _CACHED_BALANCES = {
        "deepseek": {"val": None, "type": "API"},
        "openrouter": {"val": None, "type": "API"},
        "claude": {"val": None, "type": "Est"},
        "openai": {"val": None, "type": "Est"},
        "google": {"val": None, "type": "Est"}
    }
    _LAST_BALANCE_UPDATE = 0
    _BALANCE_FETCHING = False
    
    @classmethod
    def get_session_id(cls):
        if cls._SESSION_ID is None:
            import uuid
            cls._SESSION_ID = str(uuid.uuid4()).upper()[:5]
        return cls._SESSION_ID

    @classmethod
    def get_stats(cls) -> dict:
        """Gather metrics with a 1-second cache to prevent UI stutter."""
        now = time.time()
        if cls._CACHED_STATS and (now - cls._LAST_UPDATE) < 1.0:
            return cls._CACHED_STATS
            
        try:
            import psutil
            # psutil calls can be slow; we do them once per second max
            cpu = psutil.cpu_percent()
            if cpu > 0.0: cls._LAST_CPU_VAL = cpu
            
            mem = psutil.virtual_memory()
            mem_val = mem.percent
        except (ImportError, Exception):
            cpu = cls._LAST_CPU_VAL
            mem_val = 32.0
            
        cls._CACHED_STATS = {
            "load": cpu if cpu > 0.0 else cls._LAST_CPU_VAL,
            "mem": mem_val,
            "session_id": cls.get_session_id(),
            "version": "TruthGPT v2.4.1"
        }
        cls._LAST_UPDATE = now
        return cls._CACHED_STATS

    @classmethod
    def get_api_balances(cls) -> dict:
        """Returns cached API credit balances, triggering a background fetch if stale."""
        import asyncio
        now = time.time()
        
        # Trigger non-blocking fetch if stale (60s cache)
        if (now - cls._LAST_BALANCE_UPDATE) > 60.0 and not cls._BALANCE_FETCHING:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(fetch_balances_background())
            except RuntimeError:
                # No active event loop, run in a background thread
                import threading
                def run_thread():
                    try:
                        asyncio.run(fetch_balances_background())
                    except Exception:
                        pass
                threading.Thread(target=run_thread, daemon=True).start()
                
        # Dedicate tracking to real costs from .api_cost_budget.json
        prefs = load_user_prefs()
        budget_stats = get_real_budget_stats()
        session_cost = budget_stats.get("total_usd", 0.0)
        pref_engine = prefs.get("preferred_engine", "deepseek").split(",")[0].strip()
        
        res = {}
        # 1. DeepSeek (Has API balance endpoint)
        deepseek_key = prefs.get("api_keys", {}).get("deepseek") or os.getenv("DEEPSEEK_API_KEY")
        ds_cached = cls._CACHED_BALANCES.get("deepseek", {})
        if deepseek_key and ds_cached.get("val") is not None:
            res["DeepSeek"] = (ds_cached["val"], "API Balance")
        else:
            res["DeepSeek"] = (session_cost if pref_engine == "deepseek" else 0.0, "API Cost")
                
        # 2. OpenRouter (Has API balance endpoint)
        openrouter_key = prefs.get("api_keys", {}).get("openrouter") or os.getenv("OPENROUTER_API_KEY")
        or_cached = cls._CACHED_BALANCES.get("openrouter", {})
        if openrouter_key and or_cached.get("val") is not None:
            res["OpenRouter"] = (or_cached["val"], "API Balance")
        else:
            res["OpenRouter"] = (session_cost if "openrouter" in pref_engine else 0.0, "API Cost")

        # Claude, OpenAI, and Gemini do not provide balance endpoints natively.
        # We show the REAL tracked API Cost instead of fake "Estimated Balances"
        anthropic_key = prefs.get("api_keys", {}).get("anthropic") or os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key or "claude" in pref_engine or "anthropic" in pref_engine:
            res["Claude"] = (session_cost if "claude" in pref_engine or "anthropic" in pref_engine else 0.0, "API Cost")
            
        openai_key = prefs.get("api_keys", {}).get("openai") or os.getenv("OPENAI_API_KEY")
        if openai_key or "openai" in pref_engine or "chatgpt" in pref_engine:
            res["OpenAI"] = (session_cost if "openai" in pref_engine or "chatgpt" in pref_engine else 0.0, "API Cost")
            
        google_key = prefs.get("api_keys", {}).get("google") or os.getenv("GOOGLE_API_KEY")
        if google_key or "google" in pref_engine:
            res["Gemini"] = (session_cost if "google" in pref_engine else 0.0, "API Cost")
            
        return res

def get_system_telemetry():
    """Proxy for TelemetryProvider to maintain backward compatibility."""
    return TelemetryProvider.get_stats()

def get_claude_header(updates: list[str] = None):
    """Sentient Cyber-Industrial Header: REAL API TELEMETRY."""
    from rich.text import Text
    from rich.table import Table
    from rich.console import Console
    from rich.text import Text as RichText
    
    theme_color = "plum1"
    version = "v5.9.0-GOLD"
    user_name = USER_PREFS.get("user_name", "Explorer")
    current_path = os.getcwd()
    timestamp = time.strftime("%H:%M:%S")
    uptime = "02:16:12"
    
    # Default updates if none provided
    if updates is None:
        updates = [
            "SOTA Hybrid Architecture v5.9",
            "Zero Latency Neural Boot",
            "API Budget & Cost Live-Sync",
            "Sandbox Security Hardened"
        ]
    
    # --- Real Telemetry ---
    budget_stats = get_real_budget_stats()
    cost_str = f"${budget_stats['total_usd']:.4f}"
    
    import shutil
    terminal_size = shutil.get_terminal_size()
    w = max(80, terminal_size.columns or 100)
    h = terminal_size.lines or 24
    
    if h < 30:
        telemetry = Text()
        telemetry.append(f" {timestamp} ", style="bold white bg:black")
        telemetry.append(" █▓▒░ TRUTHGPT CORE ░▒▓█ ", style="bold black bg:white")
        telemetry.append(f"  COST:[{cost_str}]  ", style="dim")
        stats = TelemetryProvider.get_stats()
        telemetry.append(f" CPU: {stats['load']:.0f}% | RAM: {stats['mem']:.0f}% ", style="white")
        header_line = Text(f"\n── TruthGPT OS {version} ──────────────────────────────────────", style=f"bold {theme_color}")
        final_header = Text()
        final_header.append(telemetry)
        final_header.append(header_line)
        final_header.append("\n")
        return final_header

    telemetry = Text()
    telemetry.append(f" {timestamp} ", style="bold white bg:black")
    telemetry.append(" █▓▒░ TRUTHGPT CORE ░▒▓█ ", style="bold black bg:white")
    telemetry.append(f"  UPTIME:[{uptime}]  COST:[{cost_str}]  ", style="dim")
    
    # Dynamic real-time system telemetry (CPU / RAM / Session ID)
    stats = TelemetryProvider.get_stats()
    sys_status = Text()
    sys_status.append(" ● ", style="bold green")
    sys_status.append(f"CPU: {stats['load']:.0f}% | RAM: {stats['mem']:.0f}% ", style="white")
    sys_status.append(f"({stats['session_id']})", style="dim")
    
    padding = max(1, w - len(telemetry.plain) - len(sys_status.plain) - 2)
    telemetry.append(" " * padding)
    telemetry.append(sys_status)
    
    telemetry.append("\n")
    telemetry.append("● NEURAL LINK: ESTABLISHED ", style="bold green")
    
    # Top Divider with Version (Pure Claude Style)
    header_line = Text(f"\n── TruthGPT OS {version} ", style=f"bold {theme_color}")
    header_line.append("─" * 60, style="dim")
    
    from rich.table import Table
    # Dynamic column widths based on current console width to prevent clutter/wrapping
    left_w = max(42, int(w * 0.35))
    right_w = w - left_w - 2
    
    table = Table.grid(expand=True)
    table.add_column(width=left_w) # Left side
    table.add_column(width=right_w) # Right side (Sidebar)
    
    # Left Content: Logo + Welcome + System status
    left_content = Text()
    
    # TruthGPT Block ASCII Logo (Printed at the top first, beautifully aligned)
    left_content.append("\n    ▀█▀ █▀▄ █ █ ▀█▀ █ █ █▀▀ █▀█ ▀█▀\n", style=theme_color)
    left_content.append("     █  █▀▄ █▄█  █  █▀█ █▄█ █▀  █ \n\n", style=theme_color)
    
    from rich.text import Text as RichText
    
    left_content.append(f" Welcome back {user_name}!\n\n", style="bold white")
    
    line1 = RichText.from_markup(f"[dim] TruthGPT 5.9 · [/dim][bold #00ff00]SOTA[/bold #00ff00][dim] · 128k Context[/dim]\n")
    left_content.append(line1)
    
    line2 = RichText.from_markup(f"[dim] Cascading: [/dim][cyan]ACTIVE[/cyan][dim] · Sandbox: [/dim][bold white]HARDENED[/bold white]\n")
    left_content.append(line2)
    
    left_content.append(f" {current_path}\n", style="dim")
    
    # Right Content: Sidebar (Industrial HUD Stats)
    right_content = Text()
    
    # 1. API Budget & Costs (REAL DATA) - PRIMARY FOCUS
    right_content.append("\n █▓▒░ COST TELEMETRY\n", style="white")
    
    # Global Budget Stats
    spent = budget_stats.get('total_usd', 0.0)
    limit = budget_stats.get('limit', 10.0)
    remaining = max(0.0, limit - spent)
    
    right_content.append(" ├ Budget:      ", style="dim")
    right_content.append(f"${limit:.2f}\n", style="green")
    right_content.append(" ├ Spent:       ", style="dim")
    right_content.append(f"${spent:.4f}\n", style="cyan")
    right_content.append(" ├ Remaining:   ", style="dim")
    right_content.append(f"${remaining:.4f}\n", style="yellow")
    right_content.append(" │\n", style="dim")

    balances = TelemetryProvider.get_api_balances()
    if balances:
        keys = list(balances.keys())
        for i, name in enumerate(keys):
            val, b_type = balances[name]
            prefix = " └ " if i == len(keys) - 1 else " ├ "
            right_content.append(f"{prefix}{name:<10}: ", style="dim")
            if "Balance" in b_type:
                right_content.append(f"${val:.4f}", style="green")
            else:
                right_content.append(f"${val:.4f}", style="cyan")
            right_content.append(f" ({b_type})\n", style="dim")
    
    # 2. Mission Persistence (Background Tasks)
    right_content.append("\n █▓▒░ MISSION PERSISTENCE\n", style="white")
    from interface.core import background_missions
    active_count = len(background_missions)
    right_content.append(f" ├ Active:      {active_count}\n", style="dim")
    right_content.append(f" ├ Status:      ", style="dim")
    right_content.append("RESILIENT\n", style="bold green")
    right_content.append(" └ Continuity:  ", style="dim")
    right_content.append("LOCKED\n", style="bold cyan")
    
    # 3. What's New (Detailed list at the bottom)
    right_content.append("\n What's new\n", style="white")
    for update in updates:
        right_content.append(f" - {update}\n", style="dim")
    
    # 4. Expert Latency
    right_content.append("\n █▓▒░ EXPERT LATENCY\n", style="white")
    right_content.append(" ├ Swarm-Core:  12ms\n", style="dim")
    right_content.append(" └ Frontier-X:  24ms\n", style="dim")
    
    # 5. Knowledge Density (Research Stats) - Optimized with cache
    right_content.append("\n █▓▒░ KNOWLEDGE DENSITY\n", style="white")
    
    global _CACHED_PAPER_COUNT, _LAST_PAPER_SCAN
    current_time = time.time()
    
    # Non-blocking: only show count if already cached by preheat or previous run
    # This prevents the UI from hanging on the first render while registry scans disk
    display_count = str(_CACHED_PAPER_COUNT) if _CACHED_PAPER_COUNT is not None else "Scanning..."
            
    right_content.append(f" ├ Indexed:     {display_count} papers\n", style="dim")
    right_content.append(f" ├ Flow:        ", style="dim")
    right_content.append("⎵⎶⎷▂▃▅▇█▆▅▃ \n", style="bold magenta")
    right_content.append(" └ SOTA-Sync:   ", style="dim")
    right_content.append("100%\n", style="bold green")
    
    # Add the single consolidated row to the table grid
    table.add_row(left_content, right_content)
    
    # Tool Execution HUD (Claude style action bar)
    tool_hud = Text()
    tool_hud.append(" ACTION: ", style="bold black bg:white")
    tool_hud.append(" [READY] ", style="bold cyan")
    tool_hud.append(" IDLE: ", style="dim")
    tool_hud.append("0.0s", style="bold green")
    tool_hud.append(" " * 15)
    tool_hud.append("✔ AGENTIAL MODE: ACTIVE", style="bold green")
    
    # Assemble final output
    final_header = Text()
    final_header.append(telemetry)
    final_header.append("\n")
    final_header.append(tool_hud)
    final_header.append("\n")
    final_header.append(header_line)
    final_header.append("\n")
    
    with console.capture() as capture:
        console.print(table)
    
    from rich.text import Text as RichText
    final_header.append(RichText.from_ansi(capture.get()))
    final_header.append("─" * 80 + "\n", style="dim")
    
    return final_header

def linux_boot_sequence():
    """Truly Instantaneous kernel injection sequence for TruthGPT."""
    clear_screen()
    color = get_theme_color()
    console.print(f"[bold {color}]>>> INJECTING TRUTHGPT KERNEL...[/bold {color}]\n")
    stages = [
        "Initializing Neural Fabric...",
        "Connecting to Swarm Nodes...",
        "Loading Expert Matrices...",
        "Syncing Neural Vault...",
        "Unlocking Overdrive Mode..."
    ]
    for stage in stages:
        # Use simple ASCII dot for maximum compatibility
        console.print(f" [cyan]*[/cyan] [white]{stage}[/white] [dim]... [bold green]OK[/bold green][/dim]")
        time.sleep(0.05) # Perceived speed optimization
    
    console.print(f"\n[bold white bg:black] SESSION ESTABLISHED [/bold white bg:black] [dim]Ready for Agent command.[/dim]\n")

def claude_log_event(layer: str, event: str, status: str = "DONE"):
    """Claude-style log entry: clean and minimal."""
    colors = {"DONE": "green", "RUNNING": "cyan", "ERROR": "red", "PENDING": "dim"}
    color = colors.get(status, "white")
    timestamp = time.strftime("%H:%M:%S")
    console.print(f"[dim]{timestamp}[/dim] [bold plum1]│[/bold plum1] [white]{layer.upper():<8}[/white] [dim]➔[/dim] [{color}]{event}[/{color}]")

def export_mission_result(content: str, mission_name: str = "Mission_Result"):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mission_name = mission_name.replace(" ", "_")
    console.print("\n[bold cyan]📤 Export & Reporting Engine[/bold cyan]")
    fmt = get_input("Export format", choices=["MD", "PDF", "Word"], default="MD").upper()
    filename = f"{mission_name}_{timestamp}"
    try:
        if fmt == "MD":
            path = Path(f"exports/{filename}.md")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            console.print(f"[bold green]✓ Exported to {path}[/bold green]")
            
            # Extract and save code blocks to exports/ too
            import re
            code_blocks = re.findall(r"```([a-zA-Z0-9+#_ -]*)\n(.*?)\n```", content, re.DOTALL)
            if code_blocks:
                console.print(f"[cyan]📦 Extracting and writing {len(code_blocks)} code blocks to exports/...[/cyan]")
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
                    code_filename = f"code_block_{idx}_{timestamp}{code_ext}"
                    code_filepath = path.parent / code_filename
                    with open(code_filepath, "w", encoding="utf-8") as code_f:
                        code_f.write(code)
                    console.print(f"  [green]● Saved code block {idx} ({lang_clean or 'python/unknown'}) to {code_filepath.name}[/green]")
    except Exception as e:
        console.print(f"[red]Export Error: {e}[/red]")

def extract_target_directory(query: Optional[str]) -> Optional[Path]:
    if not query:
        return None
    import re
    from pathlib import Path
    words = query.split()
    for length in range(len(words), 0, -1):
        for start in range(len(words) - length + 1):
            candidate = " ".join(words[start:start+length]).strip("\"'")
            if not candidate:
                continue
            is_path_like = False
            if re.match(r'^[a-zA-Z]:\\', candidate) or re.match(r'^[a-zA-Z]:/', candidate) or candidate.startswith('/') or candidate.startswith('.\\') or candidate.startswith('./'):
                is_path_like = True
            elif '\\' in candidate or '/' in candidate:
                if not candidate.startswith('http'):
                    is_path_like = True
            
            if is_path_like:
                try:
                    path = Path(candidate)
                    if path.exists() and path.is_dir():
                        return path.resolve()
                    if not path.exists():
                        parent = path.parent
                        if parent and parent.exists():
                            return path.resolve()
                except Exception:
                    pass
    return None

def save_mission_output(content: str, mission_name: str = "Mission", query: Optional[str] = None):
    target_dir = extract_target_directory(query)
    if target_dir:
        report_dir = target_dir
    else:
        report_dir = current_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{mission_name}_{time.strftime('%Y%m%d_%H%M%S')}.md"
    filepath = report_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    console.print(f"[bold green]✓ Output exported to {filepath}[/bold green]")
    
    # Extract and save code blocks to report_dir too
    import re
    code_blocks = re.findall(r"```([a-zA-Z0-9+#_ -]*)\n(.*?)\n```", content, re.DOTALL)
    if code_blocks:
        console.print(f"[cyan]📦 Extracting and writing {len(code_blocks)} code blocks to {report_dir}...[/cyan]")
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
            code_filepath = report_dir / code_filename
            with open(code_filepath, "w", encoding="utf-8") as code_f:
                code_f.write(code)
            console.print(f"  [green]● Saved code block {idx} ({lang_clean or 'python/unknown'}) to {code_filepath.name}[/green]")


def get_theme_color() -> str:
    theme = USER_PREFS.get("theme", "industrial")
    if theme in ["claude", "anthropic", "minimalist"]:
        return "plum1"
    return "orange3"

def get_theme_panel(content: Any, title: Optional[str] = None, border_style: Optional[str] = None) -> Panel:
    from rich.panel import Panel
    theme = USER_PREFS.get("theme", "industrial")
    if not border_style:
        border_style = get_theme_color()
        
    if theme in ["claude", "anthropic", "minimalist"]:
        return Panel(content, title=title, border_style=border_style, padding=(1, 2))
    else:
        return Panel(content, title=title, border_style=border_style)

def _build_ctrl_o_keybindings():
    """Build a prompt_toolkit KeyBindings object with ctrl+o => expand pending blocks.

    The handler prints expanded content above the input line (does not exit the prompt).
    """
    try:
        from prompt_toolkit.key_binding import KeyBindings
    except Exception:
        return None
    kb = KeyBindings()

    @kb.add('c-o')
    def _expand(event):
        try:
            from interface.cc_style import expand_pending
        except Exception:
            return
        # run_in_terminal yields control so prints don't corrupt the prompt buffer
        try:
            event.app.run_in_terminal(lambda: expand_pending())
        except Exception:
            pass
    return kb


def get_input(message: str, choices: Optional[List[str]] = None, default: str = "", password: bool = False) -> str:
    """Gets user input with mouse support if available, otherwise fallbacks to Rich.

    Binds ctrl+o to expand the most recent truncated tool output, matching
    Claude Code's ``(ctrl+o to expand)`` UX.
    """
    if _check_prompt_toolkit():
        # Check if an event loop is already running to avoid prompt_toolkit crash/warning
        try:
            import asyncio
            asyncio.get_running_loop()
            in_loop = True
        except RuntimeError:
            in_loop = False

        if not in_loop:
            try:
                from prompt_toolkit import prompt as pt_prompt
                from prompt_toolkit.styles import Style as PTStyle
                # Create a simple style to match terminal
                style = PTStyle.from_dict({
                    'prompt': 'bold cyan',
                })
                kb = _build_ctrl_o_keybindings()
                # Enable mouse support + ctrl+o expand
                result = pt_prompt(
                    f"{message}: ",
                    mouse_support=True,
                    style=style,
                    is_password=password,
                    key_bindings=kb,
                ).strip()
                if not result and default:
                    return default
                return result
            except (EOFError, KeyboardInterrupt):
                return "0"
            except Exception:
                # Fallback to standard Rich prompt if something goes wrong
                pass

    from rich.prompt import Prompt
    return Prompt.ask(message, choices=choices, default=default, password=password)

async def get_choice(title: str, options: Dict[str, str], style_name: str = "plum1") -> str:
    """Displays a full-screen interactive choice menu with mouse support."""
    if not _check_prompt_toolkit():
        # Fallback to static print + Prompt.ask
        from rich.table import Table
        from rich.prompt import Prompt
        table = Table(title=title)
        for k, v in options.items(): table.add_row(k, v)
        console.print(table)
        return Prompt.ask("Select", choices=list(options.keys()))

    from prompt_toolkit.application import Application, get_app
    from prompt_toolkit.layout.containers import VSplit, HSplit, Window, WindowAlign
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.widgets import Button, Label, Box, Shadow
    from prompt_toolkit.styles import Style
    from prompt_toolkit.formatted_text import ANSI
    import io

    class SimpleMenuApp:
        def __init__(self):
            self.result = None
            self.kb = KeyBindings()
            
            @self.kb.add('q')
            @self.kb.add('c-c')
            def _(event):
                event.app.exit()

            # Hotkeys
            for k in options.keys():
                @self.kb.add(k.lower())
                @self.kb.add(k.upper())
                def _(event, val=k):
                    self.result = val
                    event.app.exit()

        def get_layout(self):
            def set_choice(val):
                self.result = val
                get_app().exit(result=val)

            buttons = []
            for k, v in options.items():
                # Split key if multi-char (like BACK)
                label = f" < {k:>8}: {v:<25} > "
                buttons.append(Button(label, handler=lambda val=k: set_choice(val), width=50))

            # Render header once
            from rich.console import Console
            header_console = Console(file=io.StringIO(), force_terminal=True, width=100)
            header_console.print(get_header())
            header_content = ANSI(header_console.file.getvalue())

            root = HSplit([
                Window(content=FormattedTextControl(header_content), ignore_content_height=True),
                Window(height=1),
                Label(f"  [bold {style_name}] {title.upper()} [/bold {style_name}]", style="bold white"),
                Window(height=1),
                HSplit(buttons, padding=1),
                Window(height=1),
                Label("   [dim]Click or press key to select[/dim]", style="italic"),
                Window(height=1),
            ], align=WindowAlign.CENTER)
            
            return Layout(Shadow(Box(root, padding=2)))

        async def run(self):
            pt_style = style_name
            if pt_style == "plum1": pt_style = "#ffbbff"
            elif pt_style == "cyan": pt_style = "ansicyan"
            elif pt_style == "green": pt_style = "ansigreen"
            elif pt_style == "red": pt_style = "ansired"
            
            app = Application(
                layout=self.get_layout(),
                key_bindings=self.kb,
                style=Style.from_dict({'button.focused': f'bg:{pt_style} white'}),
                mouse_support=True,
                full_screen=True
            )
            await app.run_async()
            return self.result

    app = SimpleMenuApp()
    return await app.run()

