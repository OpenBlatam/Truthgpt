# refactored_dynamic_terminal.py
"""
Refactored Dynamic TruthGPT Terminal v3.0
================================================
- Left panel: Continuous agent live log (reasoning + activity)
- Right-top panel: Workflow status & configuration dashboard
- Right-bottom panel: Interactive command prompt & output
- Highly customizable via YAML/JSON
- Non-blocking input, integrated with DynamicWorkflow and research papers

Usage:
    python refactored_dynamic_terminal.py [--config terminal_config.json]
"""

import asyncio
import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

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
    from rich.box import HEAVY
    from rich.prompt import Prompt
except ImportError:
    print("Please install 'rich': pip install rich")
    sys.exit(1)

# ----------------------------------------------------------------------
# Local imports – with fallback for optional modules
# ----------------------------------------------------------------------
try:
    from dynamic_workflow import DynamicWorkflow
    from latency_optimizations import (
        apply_chain_of_draft,
        apply_elastic_reasoning,
        apply_fp16_stability
    )
    WORKFLOW_AVAILABLE = True
except ImportError:
    DynamicWorkflow = None
    WORKFLOW_AVAILABLE = False

try:
    from papers.chain_of_draft import ChainOfDraft
    from papers.elastic_reasoning import ElasticReasoning
    from papers.fp16_stability import FP16Stability
    PAPERS_AVAILABLE = True
except ImportError:
    PAPERS_AVAILABLE = False

# ----------------------------------------------------------------------
# Configuration management
# ----------------------------------------------------------------------
CONFIG_FILE = Path(__file__).parent / "terminal_config.json"

DEFAULT_CONFIG = {
    "agent_name": "TruthGPT-Dynamic-Agent",
    "theme": "blue",
    "refresh_rate": 4,
    "max_log_lines": 200,
    "workflow_interval": 5,
    "plugins": [],
    "continuous_mode": True,
    "active_papers": [],
    "workflow_file": "default_workflow.yaml",
    "elastic_reasoning_budget": {"think": 50, "solve": 150},
    "chain_of_draft_variant": "baseline",
    "custom_workflow_steps": []
}


def load_config() -> Dict[str, Any]:
    """Load configuration from JSON file, merging with defaults."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception as e:
            logging.warning(f"Failed to load config: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, Any]):
    """Persist configuration to JSON."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ----------------------------------------------------------------------
# Event system (thread-safe emitter)
# ----------------------------------------------------------------------
class EventEmitter:
    def __init__(self):
        self._listeners: List[Callable] = []
        self._lock = threading.Lock()

    def subscribe(self, callback: Callable):
        with self._lock:
            self._listeners.append(callback)

    def emit(self, event_type: str, data: Any = None):
        with self._lock:
            for cb in self._listeners:
                try:
                    cb(event_type, data)
                except Exception as e:
                    logging.debug(f"Event callback error: {e}")


# ----------------------------------------------------------------------
# Thread-safe log buffer
# ----------------------------------------------------------------------
class LogBuffer:
    def __init__(self, max_lines: int = 200):
        self._max = max_lines
        self._lines: List[str] = []
        self._lock = threading.Lock()

    def add(self, message: str):
        with self._lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self._lines.append(f"[{timestamp}] {message}")
            if len(self._lines) > self._max:
                self._lines = self._lines[-self._max:]

    def get_all(self) -> List[str]:
        with self._lock:
            return list(self._lines)

    def clear(self):
        with self._lock:
            self._lines.clear()


# ----------------------------------------------------------------------
# Continuous Agent (runs in background asyncio loop)
# ----------------------------------------------------------------------
class ContinuousAgent:
    """
    Autonomous agent that executes a personalized workflow in a loop.
    """
    def __init__(self, config: Dict[str, Any], emitter: EventEmitter, log_buffer: LogBuffer):
        self.config = config
        self.emitter = emitter
        self.log = log_buffer
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.iteration = 0
        # Initialize workflow engine
        if WORKFLOW_AVAILABLE and DynamicWorkflow:
            workflow_path = Path(__file__).parent / config.get("workflow_file", "default_workflow.yaml")
            self.workflow = DynamicWorkflow(config_path=workflow_path)
            # Register custom actions
            self._register_default_actions()
        else:
            self.workflow = None

    def _register_default_actions(self):
        if self.workflow:
            self.workflow.register_action("system_check", action_system_check)
            self.workflow.register_action("run_inference", action_run_model_inference)
            self.workflow.register_action("save_output", action_save_output)

    async def _run_loop(self):
        self.emitter.emit("agent_start", {"name": self.config["agent_name"]})
        self.log.add("Agent started.")
        while self.running:
            self.iteration += 1
            self.emitter.emit("iteration_begin", {"iteration": self.iteration})
            self.log.add(f"Iteration {self.iteration}")

            # Execute workflow if available
            if self.workflow:
                try:
                    result = await self.workflow.run()
                    self.log.add(f"Workflow completed: {len(result.get('history', []))} steps")
                    self.emitter.emit("workflow_done", result)
                except Exception as e:
                    self.log.add(f"Workflow error: {e}")
                    self.emitter.emit("workflow_error", str(e))
            else:
                # Simulate a basic step
                self.log.add("Workflow engine not available, using placeholder logic.")
                await asyncio.sleep(1)

            self.emitter.emit("iteration_end", {"iteration": self.iteration})
            await asyncio.sleep(self.config.get("workflow_interval", 5))
        self.log.add("Agent stopped.")
        self.emitter.emit("agent_stop")

    def start(self):
        self.running = True
        self.task = asyncio.ensure_future(self._run_loop())

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()


# ----------------------------------------------------------------------
# Workflow personalization helpers
# ----------------------------------------------------------------------
def load_personalization() -> Dict:
    pref_path = Path(__file__).parent / "user_preferences.json"
    if pref_path.exists():
        with open(pref_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def apply_paper(papers: List[str], active: List[str], log_buffer: LogBuffer):
    """Apply selected papers if available."""
    if not PAPERS_AVAILABLE:
        log_buffer.add("Papers module not available.")
        return
    for p in papers:
        if p in active:
            continue
        if p == "chain_of_draft":
            ChainOfDraft.activate()
            active.append(p)
            log_buffer.add("Applied Chain-of-Draft.")
        elif p == "elastic_reasoning":
            ElasticReasoning.activate()
            active.append(p)
            log_buffer.add("Applied Elastic Reasoning.")
        elif p == "fp16_stability":
            FP16Stability.activate()
            active.append(p)
            log_buffer.add("Applied FP16 Stability.")


def remove_paper(paper: str, active: List[str], log_buffer: LogBuffer):
    if paper in active:
        active.remove(paper)
        log_buffer.add(f"Removed paper: {paper}")
        # Deactivation logic would go here


# ----------------------------------------------------------------------
# Terminal UI (Rich Layout)
# ----------------------------------------------------------------------
class DynamicTerminal:
    """
    Main terminal interface with three-panel layout:
    - Left: Agent live log
    - Right-top: Configuration / status
    - Right-bottom: Command output / interactive prompt
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.console = Console()
        self.emitter = EventEmitter()
        self.log_buffer = LogBuffer(max_lines=config.get("max_log_lines", 200))
        self.agent = ContinuousAgent(config, self.emitter, self.log_buffer)
        self.running = False
        self.command_output: List[str] = []
        self.user_input_queue: asyncio.Queue = asyncio.Queue()
        self.layout = self._build_layout()
        self.live = Live(self.layout, console=self.console,
                         refresh_per_second=config.get("refresh_rate", 4),
                         screen=True, vertical_overflow="visible")
        # Subscribe emitter to update UI
        self.emitter.subscribe(self._on_event)

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=1)
        )
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=3)
        )
        layout["right"].split(
            Layout(name="right_top", ratio=1),
            Layout(name="right_bottom", ratio=2)
        )
        return layout

    def _on_event(self, event_type: str, data: Any = None):
        # Update log buffer
        if event_type in ("agent_start", "agent_stop", "iteration_begin", "workflow_done"):
            self.log_buffer.add(f"{event_type}: {data}")

    def _update_header(self):
        agent_name = self.config.get("agent_name", "TruthGPT")
        status = "RUNNING" if self.agent.running else "STOPPED"
        header_panel = Panel(
            Align.center(f"[bold cyan]{agent_name}[/bold cyan] | Status: [bold {"green" if status == "RUNNING" else "red"}]{status}[/]"),
            box=HEAVY
        )
        self.layout["header"].update(header_panel)

    def _update_left_panel(self):
        lines = self.log_buffer.get_all()[-20:]
        content = "\n".join(lines) if lines else "Awaiting events..."
        panel = Panel(content, title="Agent Live Log", border_style="yellow")
        self.layout["left"].update(panel)

    def _update_right_top(self):
        table = Table(title="Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Key")
        table.add_column("Value")
        for k, v in self.config.items():
            if k in ("plugins", "active_papers", "custom_workflow_steps"):
                v = ", ".join(v) if v else "none"
            table.add_row(k, str(v))
        panel = Panel(table, border_style="blue")
        self.layout["right_top"].update(panel)

    def _update_right_bottom(self):
        output_lines = self.command_output[-15:]
        prompt_line = ">>> "  # user input placeholder
        content = "\n".join(output_lines) if output_lines else "Type 'help' for commands."
        content += f"\n[bold green]{prompt_line}[/bold green]"
        panel = Panel(content, title="Command Console", border_style="green")
        self.layout["right_bottom"].update(panel)

    def refresh_ui(self):
        self._update_header()
        self._update_left_panel()
        self._update_right_top()
        self._update_right_bottom()

    def run_command(self, cmd: str):
        parts = cmd.strip().split()
        if not parts:
            return
        command = parts[0].lower()
        args = parts[1:]
        if command == "help":
            self.command_output.append("Commands: help, status, start, stop, config, workflow, papers, clear, exit")
        elif command == "status":
            self.command_output.append(f"Agent running: {self.agent.running}, Iteration: {self.agent.iteration}")
        elif command == "start":
            if not self.agent.running:
                self.agent.start()
                self.command_output.append("Agent started.")
            else:
                self.command_output.append("Agent already running.")
        elif command == "stop":
            if self.agent.running:
                self.agent.stop()
                self.command_output.append("Agent stopped.")
            else:
                self.command_output.append("Agent not running.")
        elif command == "config":
            if args and args[0] == "show":
                self.command_output.append(json.dumps(self.config, indent=2))
            elif args and args[0] == "set" and len(args) >= 3:
                key = args[1]
                value = " ".join(args[2:])
                try:
                    value = json.loads(value)
                except:
                    pass
                self.config[key] = value
                self.command_output.append(f"Set {key} = {value}")
            else:
                self.command_output.append("Usage: config show|set <key> <value>")
        elif command == "workflow":
            if args and args[0] == "run" and self.agent.workflow:
                result = asyncio.run(self.agent.workflow.run())
                self.command_output.append(f"Workflow result: {result}")
            else:
                self.command_output.append("Workflow not available. Type 'workflow run' if engine loaded.")
        elif command == "papers":
            if args and args[0] == "list":
                self.command_output.append(f"Active papers: {self.config.get('active_papers', [])}")
            elif args and args[0] == "apply" and args[1:]:
                apply_paper(args[1:], self.config.get('active_papers', []), self.log_buffer)
                self.command_output.append(f"Applied papers: {args[1:]}")
            elif args and args[0] == "remove" and args[1:]:
                for p in args[1:]:
                    remove_paper(p, self.config.get('active_papers', []), self.log_buffer)
                self.command_output.append(f"Removed papers: {args[1:]}")
        elif command == "clear":
            self.command_output.clear()
        elif command == "exit" or command == "quit":
            self.running = False
            self.agent.stop()
        else:
            self.command_output.append(f"Unknown command: {command}")

    async def async_input_loop(self):
        """Non-blocking input using a separate thread."""
        loop = asyncio.get_running_loop()
        while self.running:
            try:
                # Use input in default thread executor
                user_input = await loop.run_in_executor(None, input, ">>> ")
                if user_input:
                    self.run_command(user_input)
            except EOFError:
                break
            except Exception as e:
                self.command_output.append(f"Input error: {e}")
            await asyncio.sleep(0.1)

    async def run(self):
        self.running = True
        if self.config.get("continuous_mode", True) and not self.agent.running:
            self.agent.start()
        with self.live:
            while self.running:
                self.refresh_ui()
                await asyncio.sleep(1 / self.config.get("refresh_rate", 4))
        self.live.stop()


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Refactored Dynamic TruthGPT Terminal")
    parser.add_argument("--config", type=str, default="terminal_config.json", help="Configuration file")
    args = parser.parse_args()

    cfg = load_config()
    save_config(cfg)  # ensure config file exists with defaults

    terminal = DynamicTerminal(cfg)
    try:
        asyncio.run(terminal.run())
    except KeyboardInterrupt:
        pass
