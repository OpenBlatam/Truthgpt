# enhanced_dynamic_terminal.py
"""
Improved Dynamic TruthGPT Terminal v2.0
================================================
- Left panel: continuous agent live log
- Right-top panel: configuration dashboard
- Right-bottom panel: command output
- Advanced workflow integration (DynamicWorkflow, papers)
- Non-blocking user input
- Fully customizable (themes, intervals, workflows)
- Default workflow to apply papers and system checks

Usage:
    python enhanced_dynamic_terminal.py
"""

import asyncio
import json
import logging
import sys
import threading
import time
import queue
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

# ----------------------------------------------------------------------
# Rich UI components
# ----------------------------------------------------------------------
try:
    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich import box
    from rich.live import Live
    from rich.columns import Columns
except ImportError:
    print("Please install 'rich': pip install rich")
    sys.exit(1)

# ----------------------------------------------------------------------
# Local imports – adjust as needed
# ----------------------------------------------------------------------
try:
    from dynamic_workflow import DynamicWorkflow, action_system_check, action_run_model_inference, action_save_output
    from terminal_view import LiveTerminal
    from latency_optimizations import apply_chain_of_draft, apply_elastic_reasoning, apply_fp16_stability
    from papers.chain_of_draft import ChainOfDraft
    from papers.elastic_reasoning import ElasticReasoning
    from papers.fp16_stability import FP16Stability
except ImportError:
    DynamicWorkflow = None
    LiveTerminal = None
    apply_chain_of_draft = None
    apply_elastic_reasoning = None
    apply_fp16_stability = None
    ChainOfDraft = None
    ElasticReasoning = None
    FP16Stability = None

# ----------------------------------------------------------------------
# Configuration management
# ----------------------------------------------------------------------
CONFIG_FILE = Path(__file__).parent / "terminal_config.json"

DEFAULT_CONFIG = {
    "agent_name": "TruthGPT-Dynamic-Agent",
    "theme": "blue",
    "refresh_rate": 4,
    "max_log_lines": 150,
    "workflow_interval": 5,
    "plugins": [],
    "continuous_mode": True,
    "active_papers": [],
    "workflow_file": "default_workflow.yaml",
    "elastic_reasoning_budget": {"think": 50, "solve": 150},
    "chain_of_draft_variant": "baseline"
}


def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                # asegurar claves por defecto
                for k, v in DEFAULT_CONFIG.items():
                    cfg.setdefault(k, v)
                return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, Any]):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)


# ----------------------------------------------------------------------
# Event system
# ----------------------------------------------------------------------
class AgentEmitter:
    def __init__(self):
        self.listeners: List[Callable] = []
        self.lock = threading.Lock()

    def subscribe(self, callback: Callable):
        with self.lock:
            self.listeners.append(callback)

    def emit(self, event_type: str, data: Any):
        with self.lock:
            for cb in self.listeners:
                try:
                    cb(event_type, data)
                except Exception:
                    pass


# ----------------------------------------------------------------------
# Agent log buffer
# ----------------------------------------------------------------------
class LogBuffer:
    def __init__(self, max_lines: int = 150):
        self.max_lines = max_lines
        self.lines: List[str] = []
        self.lock = threading.Lock()

    def add(self, line: str):
        with self.lock:
            self.lines.append(line)
            if len(self.lines) > self.max_lines:
                self.lines = self.lines[-self.max_lines:]

    def get_all(self) -> List[str]:
        with self.lock:
            return list(self.lines)

    def clear(self):
        with self.lock:
            self.lines.clear()


# ----------------------------------------------------------------------
# Continuous agent (asyncio)
# ----------------------------------------------------------------------
class ContinuousAgent:
    def __init__(self, emitter: AgentEmitter, config: Dict[str, Any], log_buffer: LogBuffer):
        self.emitter = emitter
        self.config = config
        self.log_buffer = log_buffer
        self.running = False
        self.iteration = 0
        self._loop = None
        self._task = None

    def _log(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_buffer.add(f"[{ts}] {message}")

    async def _workflow_cycle(self):
        self._log("Starting workflow cycle...")
        wf_file = Path(__file__).parent / self.config.get("workflow_file", "default_workflow.yaml")
        if DynamicWorkflow and wf_file.exists():
            try:
                wf = DynamicWorkflow(config_path=wf_file)
                # registrar acciones
                wf.register_action("system_check", action_system_check)
                wf.register_action("run_model_inference", action_run_model_inference)
                wf.register_action("save_output", action_save_output)
                # personalizar según preferencias
                overrides = self.config.get("workflow_overrides", {})
                result = await wf.run(personalization_overrides=overrides)
                self._log(f"Workflow completed: {result}")
            except Exception as e:
                self._log(f"Workflow error: {e}")
        else:
            # Simulación básica con aplicación de papers
            self._log("Simulated workflow active")
            await self._simulated_cycle()

    async def _simulated_cycle(self):
        # Aplica papers configurados a un prompt de ejemplo
        prompt = "Explain the asymptotic complexity of quicksort."
        active = self.config.get("active_papers", [])
        for paper in active:
            try:
                if paper == "chain_of_draft" and apply_chain_of_draft:
                    variant = self.config.get("chain_of_draft_variant", "baseline")
                    prompt = apply_chain_of_draft(prompt, variant=variant)
                    self._log(f"Applied Chain-of-Draft ({variant})")
                elif paper == "elastic_reasoning" and apply_elastic_reasoning:
                    t = self.config.get("elastic_reasoning_budget", {}).get("think", 50)
                    s = self.config.get("elastic_reasoning_budget", {}).get("solve", 150)
                    prompt = apply_elastic_reasoning(prompt, t_budget=t, s_budget=s, wrapper=True)
                    self._log(f"Applied Elastic Reasoning (t={t},s={s})")
                elif paper == "fp16_stability" and apply_fp16_stability:
                    self._log("FP16 stability applied (simulated)")
                else:
                    self._log(f"Paper '{paper}' not applicable or missing")
            except Exception as e:
                self._log(f"Error applying paper {paper}: {e}")
        # Enviar a modelo si estuviera disponible (simular respuesta)
        self._log(f"Final prompt (truncated): {prompt[:100]}...")
        self._log("Cycle complete.")

    async def _run(self):
        self.running = True
        self._log(f"Agent '{self.config['agent_name']}' started.")
        while self.running:
            self.iteration += 1
            self._log(f"📍 Iteration {self.iteration}")
            await self._workflow_cycle()
            await asyncio.sleep(self.config["workflow_interval"])
        self._log("Agent stopped.")

    def start(self):
        self._loop = asyncio.new_event_loop()
        self._task = self._loop.create_task(self._run())
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)


# ----------------------------------------------------------------------
# Command processor
# ----------------------------------------------------------------------
class CommandProcessor:
    def __init__(self, config: Dict[str, Any], log_buffer: LogBuffer, agent: ContinuousAgent):
        self.config = config
        self.log_buffer = log_buffer
        self.agent = agent
        self.output_lines = []

    def execute(self, cmd: str) -> str:
        parts = cmd.strip().split()
        if not parts:
            return ""
        action = parts[0].lower()
        try:
            if action == "help":
                return self._help()
            elif action == "status":
                return self._status()
            elif action == "start":
                return self._start()
            elif action == "stop":
                return self._stop()
            elif action == "config":
                return self._config(parts[1:])
            elif action == "workflow":
                return self._workflow(parts[1:])
            elif action == "papers":
                return self._papers(parts[1:])
            elif action == "clear":
                return self._clear()
            elif action == "exit" or action == "quit":
                return "EXIT"
            else:
                return f"Unknown command: {action}. Type 'help' for commands."
        except Exception as e:
            return f"Command error: {e}"

    def _help(self):
        return (
            "Available commands:\n"
            "  help                     - Show this help\n"
            "  status                   - Show agent status\n"
            "  start                    - Start continuous agent\n"
            "  stop                     - Stop continuous agent\n"
            "  config [show|set <key> <value>|save|load]\n"
            "  workflow [load <file>|show|run]\n"
            "  papers [list|apply <name>|remove <name>]\n"
            "  clear                    - Clear log/output\n"
            "  exit / quit              - Exit terminal"
        )

    def _status(self):
        agent_running = self.agent.running
        return f"Agent running: {agent_running}, iteration: {self.agent.iteration}"

    def _start(self):
        if not self.agent.running:
            self.agent.start()
            return "Agent started."
        return "Agent already running."

    def _stop(self):
        if self.agent.running:
            self.agent.stop()
            return "Agent stop requested."
        return "Agent not running."

    def _config(self, args):
        if not args:
            return "Usage: config [show|set <key> <value>|save|load]"
        sub = args[0].lower()
        if sub == "show":
            return json.dumps(self.config, indent=2)
        elif sub == "set" and len(args) >= 3:
            key = args[1]
            value = args[2]
            # intentar convertir a número o booleano
            try:
                if value.lower() in ("true", "yes"):
                    value = True
                elif value.lower() in ("false", "no"):
                    value = False
                else:
                    value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
            self.config[key] = value
            return f"Set {key} = {value}"
        elif sub == "save":
            save_config(self.config)
            return "Configuration saved."
        elif sub == "load":
            self.config.update(load_config())
            return "Configuration loaded."
        else:
            return "Invalid config command."

    def _workflow(self, args):
        if not args:
            return "Usage: workflow [load <file>|show|run]"
        sub = args[0].lower()
        if sub == "load" and len(args) >= 2:
            filename = args[1]
            self.config["workflow_file"] = filename
            return f"Workflow file set to {filename}"
        elif sub == "show":
            wf_file = self.config.get("workflow_file", "default_workflow.yaml")
            path = Path(__file__).parent / wf_file
            if path.exists():
                return path.read_text(encoding='utf-8')
            else:
                return f"Workflow file '{wf_file}' not found."
        elif sub == "run":
            # trigger a manual cycle via agent (enqueue)
            # we can't directly call async, but we can emit request
            self.agent._log("Manual workflow run requested (will execute next cycle).")
            return "Workflow run scheduled."
        else:
            return "Invalid workflow command."

    def _papers(self, args):
        if not args:
            return "Usage: papers [list|apply <name>|remove <name>]"
        sub = args[0].lower()
        if sub == "list":
            papers_dir = Path(__file__).parent / "papers"
            if papers_dir.exists():
                available = [p.stem for p in papers_dir.glob("*.py")]
            else:
                available = []
            active = self.config.get("active_papers", [])
            return f"Available papers: {available}\nActive papers: {active}"
        elif sub == "apply" and len(args) >= 2:
            paper = args[1]
            active = self.config.setdefault("active_papers", [])
            if paper not in active:
                active.append(paper)
            return f"Paper '{paper}' activated."
        elif sub == "remove" and len(args) >= 2:
            paper = args[1]
            active = self.config.get("active_papers", [])
            if paper in active:
                active.remove(paper)
            return f"Paper '{paper}' deactivated."
        else:
            return "Invalid papers command."

    def _clear(self):
        self.log_buffer.clear()
        return "Log and output cleared."


# ----------------------------------------------------------------------
# UI Layout builder
# ----------------------------------------------------------------------
def build_layout(config: Dict[str, Any], log_buffer: LogBuffer, output_text: str) -> Layout:
    layout = Layout()
    layout.split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=3)
    )
    layout["right"].split_column(
        Layout(name="right_top", ratio=1),
        Layout(name="right_bottom", ratio=2)
    )

    # Left panel - Agent log
    lines = log_buffer.get_all()
    log_text = "\n".join(lines[-config["max_log_lines"]:]) or "No activity yet."
    left_panel = Panel(
        log_text,
        title="🤖 Continuous Agent Log",
        border_style=config["theme"],
        box=box.ROUNDED,
        height=30
    )
    layout["left"].update(left_panel)

    # Right top - Configuration dashboard
    theme = config["theme"]
    # Create a table showing key config values
    cfg_table = Table(box=box.SIMPLE, border_style=theme)
    cfg_table.add_column("Key", style="bold")
    cfg_table.add_column("Value")
    keys_to_show = [
        "agent_name", "continuous_mode", "workflow_interval",
        "active_papers", "workflow_file", "elastic_reasoning_budget",
        "chain_of_draft_variant", "theme", "refresh_rate"
    ]
    for key in keys_to_show:
        val = config.get(key, "")
        if isinstance(val, (dict, list)):
            val = json.dumps(val)
        cfg_table.add_row(key, str(val))
    config_panel = Panel(
        cfg_table,
        title="⚙️ Configuration Dashboard",
        border_style=theme,
        box=box.ROUNDED,
    )
    layout["right_top"].update(config_panel)

    # Right bottom - Command output
    output_panel = Panel(
        output_text or "Awaiting commands...",
        title="📟 Command Output",
        border_style=theme,
        box=box.ROUNDED,
        height=20
    )
    layout["right_bottom"].update(output_panel)

    return layout


# ----------------------------------------------------------------------
# Main terminal loop
# ----------------------------------------------------------------------
def input_thread_func(input_queue: queue.Queue, stop_event: threading.Event):
    """Lee stdin en hilo separado y pone comandos en cola."""
    while not stop_event.is_set():
        try:
            user_input = input()
            if user_input:
                input_queue.put(user_input)
        except EOFError:
            break
        except Exception:
            pass


async def amain():
    # Configuración inicial
    config = load_config()

    # Crea los componentes
    log_buffer = LogBuffer(max_lines=config["max_log_lines"])
    emitter = AgentEmitter()
    agent = ContinuousAgent(emitter, config, log_buffer)
    processor = CommandProcessor(config, log_buffer, agent)

    # El agente no se inicia automáticamente; usar 'start' command.
    # Pero podemos iniciarlo si continuous_mode=True
    if config.get("continuous_mode", True):
        agent.start()

    console = Console()
    output_text = "Bienvenido a TruthGPT Dynamic Terminal v2.0. Escribe 'help' para ver comandos.\n"
    input_queue = queue.Queue()
    stop_event = threading.Event()
    input_thread = threading.Thread(target=input_thread_func, args=(input_queue, stop_event), daemon=True)
    input_thread.start()

    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            while True:
                # Procesar comandos del usuario
                while not input_queue.empty():
                    cmd = input_queue.get_nowait()
                    result = processor.execute(cmd)
                    if result == "EXIT":
                        stop_event.set()
                        live.stop()
                        return
                    output_text += f"\n> {cmd}\n{result}\n"
                    # Mantener longitud máxima
                    lines = output_text.splitlines()
                    if len(lines) > 200:
                        output_text = "\n".join(lines[-200:])

                # Construir layout
                layout = build_layout(config, log_buffer, output_text)
                live.update(layout)
                live.refresh()
                await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        agent.stop()
        save_config(config)
        console.print("\n[bold]TruthGPT Dynamic Terminal closed.[/bold]")


def main():
    try:
        asyncio.run(amain())
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
