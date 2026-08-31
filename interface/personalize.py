"""
Personalization Room & Settings Management for TruthGPT Interface.
==================================================================
Provides interactive configuration menus for user profile settings, multi-engine
reasoning selection, ensemble orchestration modes, themes, and API credentials.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List

from rich.panel import Panel
from rich.table import Table

from interface.config import USER_PREFS, save_user_prefs
from interface.console import clear_screen, console
from interface.constants import (
    AVAILABLE_ENGINES,
    ENGINE_METADATA,
    OPENROUTER_MODEL_NAMES,
    OPENROUTER_MODELS,
)
from interface.prompts import get_input
from interface.registry import MenuRegistry


@MenuRegistry.register("personalize", title="Personalization & Settings", category="Settings")
async def handle_personalize() -> None:
    """Main interactive personalization & settings configuration room."""
    while True:
        clear_screen()
        console.print(Panel("[bold yellow]👤 Personalization & Settings[/bold yellow]", border_style="yellow"))

        engines = USER_PREFS.get("preferred_engine", "deepseek").split(",")
        engine_str = ", ".join([f"[cyan]{e.strip()}[/cyan]" for e in engines])

        table = Table(show_header=False, box=None)
        table.add_row("1. Change Name", f"[dim]Current: {USER_PREFS.get('user_name', 'Explorer')}[/dim]")
        table.add_row("2. Set Engines (Multi-Engine Support)", f"[dim]Active: {engine_str}[/dim]")
        table.add_row("3. Ensemble Mode", f"[dim]Mode: {USER_PREFS.get('ensemble_mode', 'race')}[/dim]")
        table.add_row("4. UI Theme", f"[dim]Theme: {USER_PREFS.get('theme', 'industrial')}[/dim]")
        table.add_row("5. Google OAuth Token", f"[dim]Token: {'SET' if USER_PREFS.get('google_access_token') else 'EMPTY'}[/dim]")
        table.add_row("6. Google Service Account", f"[dim]Path: {USER_PREFS.get('google_service_account', 'EMPTY')}[/dim]")
        table.add_row("7. Set API Credit Balances (Claude/OpenAI/Gemini)", "[dim]Adjust offline starting estimates[/dim]")
        table.add_row("0. Back", "")
        console.print(table)

        choice = get_input("Select setting", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
        if choice == "0":
            break
        elif choice == "1":
            USER_PREFS["user_name"] = get_input("Enter your name", default=USER_PREFS.get("user_name", "Explorer"))
        elif choice == "2":
            table = Table(
                title="🧠 [bold cyan]Neural Reasoning Engines[/bold cyan]",
                border_style="cyan",
                header_style="bold magenta",
                show_lines=True,
            )
            table.add_column("#", justify="center", style="bold cyan")
            table.add_column("Engine Name", style="bold white")
            table.add_column("Provider / Brand", style="dim")
            table.add_column("Default Model", style="green")
            table.add_column("API Key Status", justify="center")

            for idx, eng in enumerate(AVAILABLE_ENGINES, 1):
                brand, model, pref_key, env_key = ENGINE_METADATA[eng]
                key_configured = bool(
                    USER_PREFS.get("api_keys", {}).get(pref_key) or os.getenv(env_key)
                )
                status = "[bold green]Active[/bold green]" if key_configured else "[dim yellow]Key Missing[/dim yellow]"
                table.add_row(str(idx), eng, brand, model, status)

            console.print("\n[bold cyan]Select engines (comma-separated for ensemble):[/bold cyan]")
            console.print(table)

            selection = get_input("Engines", default=",".join(engines))
            parts = [p.strip() for p in selection.split(",")]
            resolved: List[str] = []
            for p in parts:
                if p.isdigit():
                    idx = int(p)
                    if 1 <= idx <= len(AVAILABLE_ENGINES):
                        resolved.append(AVAILABLE_ENGINES[idx - 1])
                else:
                    resolved.append(p)

            # If openrouter is selected, display model sub-menu
            if "openrouter" in resolved:
                console.print("\n[bold yellow]⚡ OpenRouter Model Selection:[/bold yellow]")
                model_table = Table(
                    title="🌐 [bold cyan]Available OpenRouter Models[/bold cyan]",
                    border_style="yellow",
                    header_style="bold magenta",
                    show_lines=True,
                )
                model_table.add_column("#", justify="center", style="bold yellow")
                model_table.add_column("Model ID", style="white")
                model_table.add_column("Friendly Name", style="dim")

                for idx, model_id in enumerate(OPENROUTER_MODELS, 1):
                    model_table.add_row(str(idx), model_id, OPENROUTER_MODEL_NAMES.get(model_id, model_id))

                console.print(model_table)
                model_choice = get_input("Select model # or enter custom model ID", default="1")
                if model_choice.isdigit():
                    m_idx = int(model_choice)
                    if 1 <= m_idx <= len(OPENROUTER_MODELS):
                        selected_model = OPENROUTER_MODELS[m_idx - 1]
                    else:
                        selected_model = OPENROUTER_MODELS[0]
                else:
                    selected_model = model_choice.strip() or OPENROUTER_MODELS[0]

                for i, r in enumerate(resolved):
                    if r == "openrouter":
                        resolved[i] = f"openrouter:{selected_model}"

                console.print(f"[bold green]✓[/bold green] Selected OpenRouter model: [bold white]{selected_model}[/bold white]")

            # Custom model name configuration room
            console.print("\n[bold cyan]🔧 Model Configuration Room:[/bold cyan]")
            USER_PREFS["engine_models"] = USER_PREFS.get("engine_models", {})
            clean_resolved: List[str] = []
            for eng in resolved:
                if ":" in eng:
                    clean_resolved.append(eng)
                    continue
                if eng in ENGINE_METADATA:
                    brand, default_model, pref_key, env_key = ENGINE_METADATA[eng]
                else:
                    brand, default_model, pref_key, env_key = eng.capitalize(), eng, eng, f"{eng.upper()}_API_KEY"
                current_model = USER_PREFS.get("engine_models", {}).get(eng, default_model)
                custom_m = get_input(f"➔ Enter active model for {brand} ({eng})", default=current_model)
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
                default=USER_PREFS.get("ensemble_mode", "race"),
            )
        elif choice == "4":
            USER_PREFS["theme"] = get_input(
                "Select Theme",
                choices=["industrial", "claude", "minimalist"],
                default=USER_PREFS.get("theme", "industrial"),
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


def show_main_dashboard() -> None:
    """Display the main system dashboard with telemetry header."""
    from interface.theming import get_header
    console.print(get_header())
