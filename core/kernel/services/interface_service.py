import asyncio
import importlib
from typing import Any, Dict
from loguru import logger
from .base_service import BaseService

class InterfaceService(BaseService):
    """
    Interface/Routing Service.
    Takes the legacy routing responsibilities and converts them into
    a fully decoupled service, matching the new OS architecture.
    """
    def __init__(self):
        super().__init__("InterfaceService")
        # Map dashboard choices to their respective menu handlers
        self.COMMAND_MAP = {
            "0":  ("interface.system_menu", "kernel_menu"),
            "1":  ("interface.swarm_menu", "swarm_menu"),
            "2":  ("interface.model_menu", "models_menu"),
            "3":  ("interface.research_menu", "research_menu"),
            "4":  ("interface.system_menu", "opts_menu"),
            "5":  ("interface.research_menu", "intelligence_labs_menu"),
            "6":  ("interface.comm_menu", "handle_messaging_apps"),
            "7":  ("interface.system_menu", "system_menu"),
            "9":  ("interface.blockchain_menu", "blockchain_menu"),
            "10": ("interface.infra_menu", "infrastructure_menu"),
            "11": ("interface.infra_menu", "task_registry_menu"),
            "13": ("interface.comm_menu", "marketing_intelligence_menu"),
            "15": ("interface.comm_menu", "embodied_rl_menu"),
            "16": ("interface.overdrive_menu", "handle_overdrive_menu"),
            "h":  ("interface.history_menu", "history_menu"),
            "p":  ("interface.core", "handle_personalize"),
        }

    async def _on_start(self):
        logger.info("[InterfaceService] Initializing central command routing.")
        await asyncio.sleep(0.1)

    async def _on_stop(self):
        logger.info("[InterfaceService] Shutting down command routing.")

    async def execute_command(self, choice: str, user_input: str) -> bool:
        """
        Dispatches the chosen command to the corresponding menu handler.
        Returns True if handled, False otherwise.
        """
        if choice in self.COMMAND_MAP:
            module_path, function_name = self.COMMAND_MAP[choice]
            try:
                from interface.core import console
                console.print(f"[bold cyan]●[/bold cyan] [white]Routing to {function_name}...[/white]")
                
                # Record navigation to persistent history
                try:
                    from interface.history_menu import record_action
                    record_action("ROUTER", f"Opened {function_name}", "RUN")
                except Exception:
                    pass
                
                # Import module dynamically
                module = importlib.import_module(module_path)
                handler = getattr(module, function_name)
                
                if asyncio.iscoroutinefunction(handler):
                    console.print(f"[dim]Executing async handler: {function_name}[/dim]")
                    await handler()
                else:
                    console.print(f"[dim]Executing sync handler: {function_name}[/dim]")
                    handler()
                    
                return True
            except Exception as e:
                from rich.console import Console
                import traceback
                Console().print(f"[bold red]Routing Error:[/bold red] Failed to execute {module_path}.{function_name} -> {e}")
                logger.error(f"Handler {function_name} failed: {traceback.format_exc()}")
                return True # Handled (even if failed)
        else:
            # Handle executive reasoning or other generic inputs
            if choice and not choice.isspace():
                from interface.comm_menu import handle_executive_prompt
                try:
                    await handle_executive_prompt(user_input)
                    return True
                except Exception as e:
                    from rich.console import Console
                    Console().print(f"[yellow]Command '{user_input}' not recognized or failed: {e}[/yellow]")
                    return False
        return False
