# dynamic_terminal_refactored.py
"""
TruthGPT Dynamic Terminal Refactored v3.0
============================================
- Dual-pane live TUI: Agent Reasoning (left) & Terminal Output (right)
- Full terminal command execution via subprocess bridge
- Dynamic workflow engine with personalization
- Continuous agent loop with configurable intervals
- Configurable via terminal_config.json
- Handles git commands, system tools, etc.

Usage:
    python dynamic_terminal_refactored.py
"""

import asyncio
import json
import logging
import subprocess
import sys
import threading
import time
import queue
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

# ---- Rich UI ----
try:
    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
    from rich import box
except ImportError:
    print("Rich is required: pip install rich")
    sys.exit(1)

# ---- Optional paper imports ----
try:
    from papers.chain_of_draft import ChainOfDraft
    from papers.elastic_reasoning import ElasticReasoning
    from papers.fp16_stability import FP16Stability
except ImportError:
    ChainOfDraft = None
    ElasticReasoning = None
    FP16Stability = None

# ---- Configuration ----
CONFIG_FILE = Path(__file__).parent / "terminal_config.json"
DEFAULT_CONFIG = {
    "agent_name": "TruthGPT-Dynamic",
    "theme": "blue",
    "refresh_rate": 4,
    "max_log_lines": 200,
    "workflow_interval": 5,
    "continuous_mode": True,
    "max_iterations": 0,
    "active_papers": [],
    "elastic_reasoning_budget": {"think": 50, "solve": 150},
    "chain_of_draft_variant": "baseline",
    "fp16_enabled": False,
    "terminal_shell": "bash",   # or cmd
    "workflow_file": "default_workflow.yaml"
}

def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    return DEFAULT_CONFIG.copy()

def save_config(cfg: Dict[str, Any]):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)

# ---- Thread-safe log buffers ----
class LogBuffer:
    def __init__(self, max_lines: int = 200):
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

# ---- Terminal Bridge ----
class TerminalBridge:
    """Executes shell commands in background thread, captures output."""
    def __init__(self, shell: str = "bash"):
        self.shell = shell
        self.output_buffer = LogBuffer(500)
        self.command_queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def execute(self, command: str):
        """Non-blocking: put command in queue."""
        self.command_queue.put(command)
        self.output_buffer.add(f"$ {command}")

    def _worker(self):
        """Background worker that executes commands sequentially."""
        while self.running:
            try:
                cmd = self.command_queue.get(timeout=1)
                self._run_command(cmd)
            except queue.Empty:
                continue

    def _run_command(self, cmd: str):
        try:
            if sys.platform == "win32":
                # Windows: default to cmd.exe
                shell_cmd = ["cmd", "/c", cmd]
            else:
                shell_cmd = [self.shell, "-c", cmd]
            proc = subprocess.Popen(
                shell_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=False
            )
            for line in proc.stdout:
                self.output_buffer.add(line.rstrip())
            proc.wait()
            self.output_buffer.add(f"[Exit code: {proc.returncode}]")
        except Exception as e:
            self.output_buffer.add(f"[Error: {e}]")

    def stop(self):
        self.running = False
        self.thread.join(timeout=2)

# ---- Dynamic Workflow Engine (simplified) ----
import yaml
from typing import Callable

class WorkflowStep:
    def __init__(self, name, action, params=None):
        self.name = name
        self.action = action
        self.params = params or {}

class DynamicWorkflow:
    def __init__(self, config_path: Optional[Path] = None):
        self.steps: List[WorkflowStep] = []
        self.actions: Dict[str, Callable] = {}
        if config_path and config_path.exists():
            self.load(config_path)

    def load(self, path: Path):
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        self.steps = []
        for step_data in data.get("workflow", []):
            self.steps.append(WorkflowStep(
                step_data["name"],
                step_data["action"],
                step_data.get("params", {})
            ))

    def register_action(self, name: str, func: Callable):
        self.actions[name] = func

    def run(self, ctx: Dict[str, Any] = None):
        results = []
        for step in self.steps:
            if step.action in self.actions:
                try:
                    res = self.actions[step.action](**step.params, ctx=ctx)
                    results.append((step.name, "ok", res))
                except Exception as e:
                    results.append((step.name, "error", str(e)))
            else:
                results.append((step.name, "skipped", "action not registered"))
        return results

# ---- Core Agent ----
class DynamicAgent:
    def __init__(self, config: Dict[str, Any], terminal: TerminalBridge):
        self.cfg = config
        self.terminal = terminal
        self.thought_buffer = LogBuffer(config["max_log_lines"])
        self.terminal_buffer = terminal.output_buffer
        self.workflow = DynamicWorkflow(Path(self.cfg.get("workflow_file", "default_workflow.yaml")))
        self._register_default_actions()
        self.running = True
        self.iteration = 0
        self.max_iterations = config.get("max_iterations", 0)

    def _register_default_actions(self):
        self.workflow.register_action("system_check", self._action_system_check)
        self.workflow.register_action("run_command", self._action_run_command)
        self.workflow.register_action("inference", self._action_inference_dummy)
        self.workflow.register_action("save", self._action_save)

    def _action_system_check(self, **kwargs):
        self.thought_buffer.add("Running system check...")
        self.terminal.execute("echo System OK")
        return "System OK"

    def _action_run_command(self, cmd: str, **kwargs):
        self.thought_buffer.add(f"Executing: {cmd}")
        self.terminal.execute(cmd)
        return f"Command dispatched: {cmd}"

    def _action_inference_dummy(self, prompt: str, max_tokens: int = 64, **kwargs):
        self.thought_buffer.add(f"Inference: {prompt[:40]}...")
        return "[Inference placeholder]"

    def _action_save(self, output: str, **kwargs):
        self.thought_buffer.add(f"Saving result to {output}")
        return "Saved"

    async def start(self):
        self.thought_buffer.add(f"🚀 {self.cfg['agent_name']} started.")
        self.terminal.execute("echo 'Agent ready'")
        while self.running:
            self.iteration += 1
            self.thought_buffer.add(f"--- Iteration {self.iteration} ---")

            # Run dynamic workflow
            workflow_results = self.workflow.run()
            for name, status, result in workflow_results:
                self.thought_buffer.add(f"[{name}] {status}: {result}")

            # Check user input (simulate or via input queue)
            await self._process_user_input()

            if self.max_iterations and self.iteration >= self.max_iterations:
                self.running = False
                break
            await asyncio.sleep(self.cfg.get("workflow_interval", 5))

        self.thought_buffer.add("Agent stopped.")

    async def _process_user_input(self):
        # Placeholder: could read from stdin in a separate thread
        # For now, just log that we are listening
        pass

# ---- TUI Manager ----
class TUI:
    def __init__(self, agent: DynamicAgent, config: Dict[str, Any]):
        self.agent = agent
        self.cfg = config
        self.console = Console()
        self.layout = self._build_layout()
        self.live = Live(self.layout, console=self.console, refresh_per_second=config["refresh_rate"],
                         screen=True, vertical_overflow="visible")

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="thoughts", ratio=1),
            Layout(name="terminal", ratio=2)
        )
        return layout

    def _make_thought_panel(self) -> Panel:
        lines = self.agent.thought_buffer.get_all()[-20:]
        content = "\n".join(lines) if lines else "[dim]Waiting for thoughts...[/dim]"
        return Panel(content, title="🧠 Agent Reasoning", border_style="cyan", height=20)

    def _make_terminal_panel(self) -> Panel:
        lines = self.agent.terminal_buffer.get_all()[-30:]
        content = "\n".join(lines) if lines else "[dim]No terminal output yet.[/dim]"
        return Panel(content, title="💻 Terminal Output", border_style="green", height=20)

    def _make_header(self) -> Panel:
        title = f"{self.cfg['agent_name']} · Iteration: {self.agent.iteration}"
        return Panel(Text(title, style="bold white on blue"), style="blue")

    def _make_footer(self) -> Panel:
        return Panel(Text("Press Ctrl+C to stop", style="bold white on dark_red"))

    def refresh(self):
        self.layout["header"].update(self._make_header())
        self.layout["thoughts"].update(self._make_thought_panel())
        self.layout["terminal"].update(self._make_terminal_panel())
        self.layout["footer"].update(self._make_footer())

    async def run(self):
        with self.live:
            # Start agent in background task
            agent_task = asyncio.create_task(self.agent.start())
            # Refresh TUI periodically
            while self.agent.running:
                self.refresh()
                await asyncio.sleep(1 / self.cfg["refresh_rate"])
            # Final refresh
            self.refresh()
            await asyncio.sleep(2)  # show final state

# ---- Main ----
async def main():
    config = load_config()
    shell = config.get("terminal_shell", "bash")
    terminal_bridge = TerminalBridge(shell=shell)
    agent = DynamicAgent(config, terminal_bridge)
    tui = TUI(agent, config)
    await tui.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Agent terminated by user.")
