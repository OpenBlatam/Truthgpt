# ultimate_dynamic_terminal.py
"""
TruthGPT Ultimate Dynamic Terminal v6.0
========================================
Personalized, side-by-side continuous agent monitor with workflow visualization and configuration panel.

Layout:
  ┌─ Status Bar ─────────────────────────────────────────────────┐
  │ Left: Agent Reasoning Log  │ Center: Workflow State │ Right: Terminal & Output │
  │ (continuous thoughts)      │ (steps, progress)      │ (commands, config view)  │
  └──────────────────────────────────────────────────────────────┘

Key upgrades from v5.5:
- User profile integration (user_preferences.json) for theme and behavior.
- DynamicWorkflow integration with async steps, parallel execution, live progress.
- Config panel: toggle between terminal output and configuration viewer.
- Improved command set: personalization commands, workflow step control.
- Performance: use of asyncio for non-blocking workflow execution.
"""

import argparse
import asyncio
import json
import logging
import os
import queue
import re
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# ── Rich UI ────────────────────────────────
try:
    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
except ImportError:
    print("Install 'rich': pip install rich")
    sys.exit(1)

# ── Local imports ──────────────────────────
try:
    from dynamic_workflow import DynamicWorkflow, WorkflowStep
    WORKFLOW_AVAILABLE = True
except ImportError:
    DynamicWorkflow = None
    WorkflowStep = None
    WORKFLOW_AVAILABLE = False

PAPERS_AVAILABLE = False
ChainOfDraft = None
ElasticReasoning = None
FP16Stability = None
try:
    from papers.chain_of_draft import ChainOfDraft
    from papers.elastic_reasoning import ElasticReasoning
    from papers.fp16_stability import FP16Stability
    PAPERS_AVAILABLE = True
except ImportError:
    pass

# ── Configuration files ────────────────────
CONFIG_FILE = Path(__file__).parent / "terminal_config.json"
USER_PREFS_FILE = Path(__file__).parent / "user_preferences.json"

DEFAULT_CONFIG = {
    "agent_name": "TruthGPT-Agent",
    "theme": "dark_blue",
    "refresh_rate": 4,
    "max_log_lines": 100,
    "workflow_interval": 4,
    "plugins": [],
    "continuous_mode": True,
    "active_papers": [],
    "workflow_file": "default_workflow.yaml",
    "elastic_reasoning_budget": {"think": 50, "solve": 150},
    "chain_of_draft_variant": "baseline",
    "custom_workflow_steps": [],
    "colors": {
        "agent_border": "blue",
        "terminal_border": "green",
        "status_bar_style": "bold white on dark_blue",
        "cmd_prompt": "bold yellow"
    },
    "startup_commands": [],
    "on_cycle_hooks": []
}

def load_config() -> Dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception as e:
            logging.warning(f"Config load error: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(cfg: Dict):
    tmp_path = CONFIG_FILE.with_suffix('.tmp')
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        tmp_path.replace(CONFIG_FILE)
    except IOError as e:
        logging.error(f"Config save failed: {e}")

def load_user_prefs() -> Dict:
    if USER_PREFS_FILE.exists():
        try:
            with open(USER_PREFS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"user_name": "user", "theme": "minimalist", "continuous_mode": True}

def save_user_prefs(prefs: Dict):
    tmp_path = USER_PREFS_FILE.with_suffix('.tmp')
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
        tmp_path.replace(USER_PREFS_FILE)
    except IOError as e:
        logging.error(f"User prefs save failed: {e}")

# ── Log Buffer ─────────────────────────────
class LogBuffer:
    def __init__(self, max_lines: int = 100):
        self._lock = threading.Lock()
        self._max = max_lines
        self._lines: List[str] = []
    def add(self, msg: str):
        with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self._lines.append(f"[{ts}] {msg}")
            if len(self._lines) > self._max:
                self._lines = self._lines[-self._max:]
    def get_all(self) -> List[str]:
        with self._lock:
            return list(self._lines)
    def clear(self):
        with self._lock:
            self._lines.clear()

# ── Event Emitter ──────────────────────────
class EventEmitter:
    def __init__(self):
        self._listeners: List[Callable] = []
        self._lock = threading.Lock()
    def subscribe(self, callback: Callable[[str, Any], None]):
        with self._lock:
            self._listeners.append(callback)
    def emit(self, event: str, data: Any = None):
        with self._lock:
            for cb in self._listeners:
                try:
                    cb(event, data)
                except Exception:
                    pass

# ── Workflow Controller (async wrapper) ────
class WorkflowController:
    def __init__(self, workflow_path: str, logger_cb: Callable[[str], None]):
        self.wf = DynamicWorkflow(workflow_path) if WORKFLOW_AVAILABLE and DynamicWorkflow else None
        self.log = logger_cb
        self.steps: List[WorkflowStep] = []
        self.progress_info = {"total": 0, "completed": 0, "current": "", "status": "IDLE"}
        self._step_queue = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.history: List[Dict] = []
    async def initialize(self):
        if not self.wf:
            self.log("Workflow engine not available")
            return
        self.steps = list(self.wf.steps)
        self.progress_info["total"] = len(self.steps)
        self.progress_info["completed"] = 0
        self.progress_info["status"] = "READY"
        # Register default system actions
        self.wf.register_action("log", lambda msg, **kw: self.log(msg))
        self.wf.register_action("sleep", lambda sec: time.sleep(sec))
    async def run_step(self, step: WorkflowStep):
        if self._stop_event.is_set():
            return None
        self.progress_info["current"] = step.name
        self.progress_info["status"] = "RUNNING"
        try:
            result = self.wf.run_step(step)
            await asyncio.sleep(0)  # yield
            return result
        except Exception as e:
            self.log(f"Step {step.name} error: {e}")
            return None
    async def run_all(self, overrides=None):
        if not self.wf:
            return
        self.wf.personalize(overrides or {})
        self.history = []
        for step in self.steps:
            if self._stop_event.is_set():
                self.log("Workflow stopped.")
                break
            result = await self.run_step(step)
            self.history.append({"step": step.name, "status": "ok" if result is not None else "error"})
            self.progress_info["completed"] += 1
        self.progress_info["status"] = "IDLE"
        self.progress_info["current"] = ""
        self.log("Workflow completed.")
    async def start_worker(self):
        loop = asyncio.get_running_loop()
        self._loop = loop
        self._task = loop.create_task(self.run_all())
    async def stop(self):
        if self._task and not self._task.done():
            self._stop_event.set()
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()

# ── Ultimate Terminal Application ───────────
class UltimateDynamicTerminal:
    def __init__(self):
        self.config = load_config()
        self.user_prefs = load_user_prefs()
        self.console = Console()
        self.log_buffer = LogBuffer(max_lines=self.config.get("max_log_lines", 100))
        self.events = EventEmitter()
        self.workflow_ctrl: Optional[WorkflowController] = None
        self.running = True
        self.input_queue = queue.Queue()
        self.command_history: List[str] = []
        self.history_idx = -1
        self.current_cmd = ""
        self.show_config = False  # toggle right panel between terminal and config view
        self.agent_messages = []   # simulated agent thoughts
        self._layout = None
        self._live: Optional[Live] = None
        self._loop: asyncio.AbstractEventLoop = None
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    def _signal_handler(self, signum, frame):
        self.running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
    # ── Logging ──
    def log(self, message: str):
        self.log_buffer.add(message)
    def log_system(self, message: str):
        self.log(f"[SYSTEM] {message}")
    def log_workflow(self, message: str):
        self.log(f"[WORKFLOW] {message}")
    # ── UI Components ──
    def make_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="center", ratio=2),
            Layout(name="right", ratio=3),
        )
        return layout
    def render_header(self) -> Panel:
        agent_name = self.config.get("agent_name", "Agent")
        user_name = self.user_prefs.get("user_name", "User")
        status = f"Agent: {agent_name} | User: {user_name} | Mode: {'Continuous' if self.config.get('continuous_mode') else 'Manual'}"
        return Panel(Text(status, style="bold white"), style="on blue")
    def render_footer(self) -> Panel:
        return Panel(Text("Q: Quit | H: Help | C: Config Toggle | Enter: Execute", style="bold"))
    def render_agent_panel(self) -> Panel:
        lines = self.log_buffer.get_all()[-20:]  # show last 20 lines
        if not lines:
            lines = ["Waiting for agent activity..."]
        return Panel(Text("\n".join(lines), style="white"), title="Agent Reasoning", border_style=self.config.get("colors", {}).get("agent_border", "blue"))
    def render_workflow_panel(self) -> Panel:
        if not self.workflow_ctrl:
            return Panel("No workflow loaded", title="Workflow", border_style="yellow")
        info = self.workflow_ctrl.progress_info
        table = Table(show_header=False, box=None)
        table.add_row("Status", info["status"])
        table.add_row("Total Steps", str(info["total"]))
        table.add_row("Completed", str(info["completed"]))
        table.add_row("Current Step", info["current"] or "-")
        # Show step list with status indicators
        step_lines = []
        for i, step in enumerate(self.workflow_ctrl.steps):
            done = i < info["completed"]
            current = i == info["completed"] and info["status"] == "RUNNING"
            prefix = "✓" if done else ("▶" if current else "○")
            step_lines.append(f"{prefix} {step.name}")
        return Panel(Text("\n".join([table, "", "Steps:"] + step_lines, style="white"), title="Workflow Progress", border_style="green")
    def render_terminal_panel(self) -> Panel:
        if self.show_config:
            cfg_display = json.dumps(self.config, indent=2)
            return Panel(Text(cfg_display, style="bold white"), title="Current Configuration", border_style="red")
        output = self.console.export_text()  # not ideal, we'll maintain a string buffer instead
        # For simplicity, we'll show last command output
        output_str = "\n".join(self.agent_messages[-10:]) if self.agent_messages else "Type a command..."
        return Panel(Text(output_str, style="white"), title="Terminal Output", border_style=self.config.get("colors", {}).get("terminal_border", "green"))
    # ── Command Processing ──
    def execute_command(self, cmd: str):
        self.command_history.append(cmd)
        parts = cmd.strip().split()
        if not parts:
            return
        root = parts[0].lower()
        args = parts[1:]
        if root == "help" or root == "h":
            self.agent_messages.append(self._help_text())
        elif root == "config":
            self._cmd_config(args)
        elif root == "workflow" or root == "wf":
            self._cmd_workflow(args)
        elif root == "agent":
            self._cmd_agent(args)
        elif root == "papers":
            self._cmd_papers(args)
        elif root == "clear" or root == "cls":
            self.log_buffer.clear()
            self.agent_messages.clear()
        elif root == "toggle" or root == "t":
            self.show_config = not self.show_config
        elif root == "prefs":
            self._cmd_prefs(args)
        elif root == "exit" or root == "quit" or root == "q":
            self.running = False
        else:
            self.agent_messages.append(f"Unknown command: {root}")
    def _help_text(self) -> str:
        return (
            "Commands:\n"
            " help, h              : Show this help\n"
            " config show/set KEY VAL : View or change configuration\n"
            " workflow start/stop/pause/load FILE : Control workflow\n"
            " agent start/stop      : Toggle continuous agent\n"
            " papers apply/list     : Use or list research papers\n"
            " prefs show/set KEY VAL: User preferences\n"
            " toggle, t             : Switch right panel (terminal/config)\n"
            " clear, cls            : Clear logs\n"
            " exit, quit, q         : Quit\n"
        )
    def _cmd_config(self, args):
        if not args:
            self.agent_messages.append("Usage: config show|set <key> <value>")
            return
        sub = args[0].lower()
        if sub == "show":
            self.show_config = True
            self.agent_messages.append("Config view toggled ON")
        elif sub == "set" and len(args) >= 3:
            key = args[1]
            value = " ".join(args[2:])
            # Try to convert to number or boolean
            try:
                value = json.loads(value)
            except:
                pass
            if key in self.config:
                self.config[key] = value
                save_config(self.config)
                self.agent_messages.append(f"Config {key} set to {value}")
            else:
                self.agent_messages.append(f"Unknown config key: {key}")
        else:
            self.agent_messages.append("Invalid config command")
    def _cmd_workflow(self, args):
        if not args:
            self.agent_messages.append("Usage: workflow start|stop|pause|load <file>")
            return
        sub = args[0].lower()
        if sub == "start":
            if not self.workflow_ctrl:
                wf_path = self.config.get("workflow_file", "default_workflow.yaml")
                self.workflow_ctrl = WorkflowController(wf_path, self.log_workflow)
                loop = asyncio.get_event_loop() if self._loop else asyncio.new_event_loop()
                asyncio.ensure_future(self.workflow_ctrl.initialize())
            asyncio.ensure_future(self.workflow_ctrl.start_worker())
            self.log_system("Workflow started")
        elif sub == "stop":
            if self.workflow_ctrl:
                asyncio.ensure_future(self.workflow_ctrl.stop())
                self.log_system("Workflow stop requested")
        elif sub == "load" and len(args) >= 2:
            wf_path = args[1]
            self.config["workflow_file"] = wf_path
            save_config(self.config)
            self.workflow_ctrl = WorkflowController(wf_path, self.log_workflow)
            asyncio.ensure_future(self.workflow_ctrl.initialize())
            self.log_system(f"Workflow loaded from {wf_path}")
        else:
            self.agent_messages.append("Invalid workflow command")
    def _cmd_agent(self, args):
        if not args:
            self.agent_messages.append("Usage: agent start|stop")
            return
        sub = args[0].lower()
        if sub == "start":
            self.config["continuous_mode"] = True
            save_config(self.config)
            self.log_system("Continuous agent mode ON")
        elif sub == "stop":
            self.config["continuous_mode"] = False
            save_config(self.config)
            self.log_system("Continuous agent mode OFF")
    def _cmd_papers(self, args):
        if not PAPERS_AVAILABLE:
            self.agent_messages.append("Papers module not available")
            return
        if not args:
            self.agent_messages.append("Usage: papers apply|list")
            return
        sub = args[0].lower()
        if sub == "apply" and len(args) >= 2:
            name = args[1]
            if name in self.config["active_papers"]:
                self.agent_messages.append(f"Paper {name} already active")
            else:
                self.config["active_papers"].append(name)
                save_config(self.config)
                self.log_system(f"Applied paper: {name}")
        elif sub == "list":
            active = ", ".join(self.config["active_papers"]) if self.config["active_papers"] else "None"
            self.agent_messages.append(f"Active papers: {active}")
    def _cmd_prefs(self, args):
        if not args:
            self.agent_messages.append("Usage: prefs show|set <key> <value>")
            return
        sub = args[0].lower()
        if sub == "show":
            self.agent_messages.append(json.dumps(self.user_prefs, indent=2))
        elif sub == "set" and len(args) >= 3:
            key = args[1]
            value = " ".join(args[2:])
            try:
                value = json.loads(value)
            except:
                pass
            self.user_prefs[key] = value
            save_user_prefs(self.user_prefs)
            self.agent_messages.append(f"Preference {key} updated")
    # ── Input Thread ──
    def input_loop(self):
        while self.running:
            try:
                cmd = input(">>> ")
                if cmd:
                    self.input_queue.put(cmd)
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break
    async def async_shell(self):
        while self.running:
            try:
                cmd = await asyncio.get_event_loop().run_in_executor(None, self.input_queue.get, True, 0.5)
                self.execute_command(cmd)
            except queue.Empty:
                await asyncio.sleep(0.1)
    # ── Main Render Loop ──
    async def ui_loop(self, refresh_rate: float = 4):
        layout = self.make_layout()
        with Live(layout, console=self.console, refresh_per_second=refresh_rate, screen=True) as live:
            self._live = live
            while self.running:
                # Update layout
                layout["header"].update(self.render_header())
                layout["left"].update(self.render_agent_panel())
                layout["center"].update(self.render_workflow_panel())
                layout["right"].update(self.render_terminal_panel())
                layout["footer"].update(self.render_footer())
                await asyncio.sleep(1.0 / refresh_rate)
    async def start(self):
        # Initialize async tasks
        self._loop = asyncio.get_running_loop()
        # Start workflow controller if any
        if WORKFLOW_AVAILABLE and self.config.get("workflow_file"):
            self.workflow_ctrl = WorkflowController(self.config["workflow_file"], self.log_workflow)
            await self.workflow_ctrl.initialize()
        # Launch input thread
        input_thread = threading.Thread(target=self.input_loop, daemon=True)
        input_thread.start()
        # Run shell and UI concurrently
        await asyncio.gather(
            self.async_shell(),
            self.ui_loop(refresh_rate=self.config.get("refresh_rate", 4))
        )

# ── Entry Point ────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="TruthGPT Ultimate Dynamic Terminal")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    terminal = UltimateDynamicTerminal()
    try:
        asyncio.run(terminal.start())
    except KeyboardInterrupt:
        pass
    finally:
        print("\nTerminal closed. Goodbye.")

if __name__ == "__main__":
    main()
