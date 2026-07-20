# improved_dynamic_terminal.py
"""
TruthGPT Dynamic Terminal v7.0 (Side-by-Side Enhanced + Git Command)
========================================================================
Layout:
  ┌─ Status Bar ─────────────────────────────────────────────┐
  │ Left: Agent Reasoning & Log    │ Right: Terminal & Output│
  │ (Continuous thoughts, steps)   │ (Command input, results)│
  └──────────────────────────────────────────────────────────┘

New in v7.0:
- Integrated 'git' command: executes any git command (add, push, commit, etc.) in the
  optimization_core directory using subprocess. Enables the agent to perform repo
  management directly from the terminal.
- All previous v6.0 features preserved.
"""

import argparse
import json
import logging
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ── Rich ─────────────────────────────────────
try:
    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    from rich.prompt import Prompt
except ImportError:
    print("Install 'rich': pip install rich")
    sys.exit(1)

# ── Local imports with graceful fallback ────
try:
    from dynamic_workflow import DynamicWorkflow, WorkflowStep
    WORKFLOW_AVAILABLE = True
except ImportError:
    DynamicWorkflow = None
    WORKFLOW_AVAILABLE = False

PAPERS_AVAILABLE = False
ChainOfDraft = None
ElasticReasoning = None
FP16Stability = None
apply_chain_of_draft = None
apply_elastic_reasoning = None
apply_fp16_stability = None
try:
    from papers.chain_of_draft import ChainOfDraft
    from papers.elastic_reasoning import ElasticReasoning
    from papers.fp16_stability import FP16Stability
    from latency_optimizations import apply_chain_of_draft, apply_elastic_reasoning, apply_fp16_stability
    PAPERS_AVAILABLE = True
except ImportError:
    pass

# ── Configuration ───────────────────────────
CONFIG_FILE = Path(__file__).parent / "terminal_config.json"
USER_PREFS_FILE = Path(__file__).parent / "user_preferences.json"
GIT_WORK_DIR = Path(__file__).parent  # optimization_core

DEFAULT_CONFIG = {
    "agent_name": "TruthGPT-Agent",
    "theme": "dark_blue",
    "refresh_rate": 4,               # Hz
    "max_log_lines": 200,
    "workflow_interval": 5,          # seconds between workflow cycles
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

# ── Utility functions ──────────────────────
def load_config() -> Dict:
    """Load configuration, merging with defaults."""
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
    """Atomically save current configuration."""
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
        except Exception as e:
            logging.warning(f"User prefs load error: {e}")
    return {}

# ── Thread‑safe Log Buffer ──────────────────
class LogBuffer:
    """A bounded, thread‑safe buffer for log lines."""
    def __init__(self, max_lines: int = 200):
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

# ── Finite‑State Workflow ──────────────────
from enum import Enum

class WorkflowState(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"

@dataclass
class CommandResult:
    success: bool
    message: str
    data: Any = None

# ── Git Command Executor ───────────────────
def execute_git(args: List[str]) -> CommandResult:
    """Run a git command in the optimization_core directory.
    Returns the output as a string if successful, or an error message."""
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=str(GIT_WORK_DIR),
            capture_output=True,
            text=True,
            timeout=30,
            shell=False
        )
        if proc.returncode == 0:
            return CommandResult(True, proc.stdout.strip() or "Git command completed successfully.")
        else:
            error_msg = proc.stderr.strip() or proc.stdout.strip()
            return CommandResult(False, f"Git failed (code {proc.returncode}): {error_msg}")
    except subprocess.TimeoutExpired:
        return CommandResult(False, "Git command timed out (30s).")
    except FileNotFoundError:
        return CommandResult(False, "Git is not installed or not in PATH.")
    except Exception as e:
        return CommandResult(False, f"Unexpected error: {str(e)}")

# ── Dynamic Terminal Core ──────────────────
class DynamicTerminal:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config if config is not None else load_config()
        self.user_prefs = load_user_prefs()
        self.console = Console()
        self.running = True
        self.live: Optional[Live] = None

        # Log buffer for agent reasoning
        self.agent_log = LogBuffer(self.config["max_log_lines"])
        # Terminal output buffer (right panel)
        self.terminal_output = LogBuffer(self.config["max_log_lines"])

        # Workflow state
        self.workflow_state = WorkflowState.IDLE
        self.workflow: Optional[DynamicWorkflow] = None
        if WORKFLOW_AVAILABLE and self.config["workflow_file"]:
            wf_path = Path(self.config["workflow_file"])
            if wf_path.exists():
                self.workflow = DynamicWorkflow.from_yaml(str(wf_path))
                self.terminal_output.add(f"Loaded workflow: {self.config['workflow_file']}")

        # Input queue for commands
        self.input_queue: queue.Queue = queue.Queue()
        self.command_history: List[str] = []

        # Initialize paper activations
        self._init_papers()

        # Register signal handler
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

    def _init_papers(self):
        if not PAPERS_AVAILABLE or not self.config.get("active_papers"):
            return
        for paper_name in self.config["active_papers"]:
            try:
                if paper_name == "chain_of_draft" and callable(apply_chain_of_draft):
                    apply_chain_of_draft(
                        variant=self.config.get("chain_of_draft_variant", "baseline")
                    )
                    self.agent_log.add(f"Activated paper: Chain of Draft ({self.config['chain_of_draft_variant']})")
                elif paper_name == "elastic_reasoning" and callable(apply_elastic_reasoning):
                    apply_elastic_reasoning(
                        think_budget=self.config.get("elastic_reasoning_budget", {}).get("think", 50),
                        solve_budget=self.config.get("elastic_reasoning_budget", {}).get("solve", 150)
                    )
                    self.agent_log.add("Activated paper: Elastic Reasoning")
                elif paper_name == "fp16_stability" and callable(apply_fp16_stability):
                    apply_fp16_stability()
                    self.agent_log.add("Activated paper: FP16 Stability")
                else:
                    self.agent_log.add(f"Unknown paper '{paper_name}' or function unavailable.")
            except Exception as e:
                self.agent_log.add(f"Error activating paper '{paper_name}': {e}")

    def _handle_exit(self, signum, frame):
        self.running = False
        if self.live:
            self.live.stop()

    def run(self):
        """Main execution loop with side-by-side layout."""
        # Build layout
        layout = Layout()
        layout.split(
            Layout(name="status", size=1),
            Layout(name="main", ratio=1)
        )
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )

        # Update routine
        def update_layout():
            # Status bar
            status_text = Text(
                f"  {self.config['agent_name']}  |  Workflow: {self.workflow_state.value}  |  Press '?' for help  |  Ctrl+C to quit",
                style=self.config["colors"]["status_bar_style"]
            )
            layout["status"].update(Panel(status_text, box=box.MINIMAL))

            # Left panel: agent log
            left_lines = self.agent_log.get_all() or ["[Waiting for thoughts...]"]
            left_content = "\n".join(left_lines[-20:])  # show last 20 lines
            layout["left"].update(
                Panel(
                    Text(left_content),
                    title="Agent Reasoning & Log",
                    border_style=self.config["colors"]["agent_border"],
                    height=30
                )
            )

            # Right panel: terminal output + input prompt
            right_lines = self.terminal_output.get_all() or ["Welcome to TruthGPT Dynamic Terminal v7.0"]
            right_content = "\n".join(right_lines[-20:])
            layout["right"].update(
                Panel(
                    Text(right_content + "\n\n> " + (self.input_buffer if hasattr(self, 'input_buffer') else "")),
                    title="Terminal & Output",
                    border_style=self.config["colors"]["terminal_border"],
                    height=30
                )
            )

        # Input thread
        self.input_buffer = ""
        input_thread = threading.Thread(target=self._input_reader, daemon=True)
        input_thread.start()

        # Workflow thread
        workflow_thread = threading.Thread(target=self._workflow_runner, daemon=True)
        workflow_thread.start()

        # Start Live display
        with Live(console=self.console, refresh_per_second=self.config["refresh_rate"], screen=True) as live:
            self.live = live
            while self.running:
                # Process commands from queue
                while not self.input_queue.empty():
                    cmd = self.input_queue.get_nowait()
                    self._process_command(cmd)

                # Update layout
                update_layout()
                time.sleep(1 / self.config["refresh_rate"])

        # Cleanup
        self.terminal_output.add("Terminal shut down.")
        save_config(self.config)

    def _input_reader(self):
        """Non-blocking input reading."""
        while self.running:
            try:
                # Read a line from stdin
                # We use a simple prompt because Rich's Prompt.readline would be blocking.
                # To integrate with the live display, we'll use a separate thread for input.
                # We'll accumulate a buffer.
                if sys.stdin.isatty():
                    user_input = input()
                    self.input_queue.put(user_input)
                    if user_input.strip():
                        self.command_history.append(user_input.strip())
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break
            except Exception as e:
                self.terminal_output.add(f"Input error: {e}")

    def _workflow_runner(self):
        """Continuous workflow cycle."""
        while self.running:
            if self.workflow_state == WorkflowState.RUNNING and self.workflow:
                try:
                    # Execute a step
                    step = self.workflow.next_step()
                    if step:
                        self.terminal_output.add(f"Executing workflow step: {step.name}")
                        # Simulate step execution (in real use, integrate with agent)
                        result = step.execute()
                        self.terminal_output.add(f"Step '{step.name}' result: {result}")
                    else:
                        # No more steps, pause
                        self.workflow_state = WorkflowState.PAUSED
                        self.terminal_output.add("Workflow completed. Transitioned to PAUSED.")
                except Exception as e:
                    self.terminal_output.add(f"Workflow error: {e}")
            time.sleep(self.config["workflow_interval"])

    def _process_command(self, cmd: str):
        """Dispatch command."""
        cmd = cmd.strip()
        if not cmd:
            return

        # Log the command to terminal output
        self.terminal_output.add(f"$ {cmd}")

        parts = cmd.split()
        command = parts[0].lower()
        args = parts[1:]

        try:
            if command == "help" or command == "?":
                self._cmd_help()
            elif command == "clear":
                self.terminal_output.clear()
                self.agent_log.clear()
            elif command == "config":
                self._cmd_config(args)
            elif command == "workflow":
                self._cmd_workflow(args)
            elif command == "agent":
                self._cmd_agent(args)
            elif command == "paper":
                self._cmd_paper(args)
            elif command == "git":
                self._cmd_git(args)
            else:
                self.terminal_output.add(f"Unknown command: {command}. Type 'help' for available commands.")
        except Exception as e:
            self.terminal_output.add(f"Command error: {e}")

    def _cmd_help(self):
        help_text = """
        Available commands:
        - help, ?               : Show this help
        - clear                 : Clear both panels
        - config show           : Display current configuration
        - config set <key> <val>: Set a configuration value
        - workflow start/stop/pause/resume/status : Control workflow
        - agent start/stop      : Control continuous agent (simulated)
        - paper list            : List available papers
        - paper apply <name>    : Activate a research paper
        - git <args>            : Execute a git command (e.g., git add ., git push)
        """
        self.terminal_output.add(help_text)

    def _cmd_config(self, args):
        if len(args) == 0 or args[0] == "show":
            cfg_text = json.dumps(self.config, indent=2)
            self.terminal_output.add(f"Current config:\n{cfg_text}")
        elif len(args) >= 3 and args[0] == "set":
            key = args[1]
            val_str = " ".join(args[2:])
            try:
                val = json.loads(val_str)
            except:
                val = val_str
            self.config[key] = val
            self.terminal_output.add(f"Set {key} = {val}")
            # If workflow file changed, reload
            if key == "workflow_file" and WORKFLOW_AVAILABLE:
                wf_path = Path(val)
                if wf_path.exists():
                    self.workflow = DynamicWorkflow.from_yaml(str(wf_path))
                    self.terminal_output.add(f"Reloaded workflow: {val}")
        else:
            self.terminal_output.add("Usage: config show | config set <key> <value>")

    def _cmd_workflow(self, args):
        if not args:
            self.terminal_output.add("Usage: workflow [start|stop|pause|resume|status]")
            return
        action = args[0].lower()
        if action == "start":
            if self.workflow_state == WorkflowState.IDLE or self.workflow_state == WorkflowState.STOPPED:
                if self.workflow:
                    self.workflow.reset()
                self.workflow_state = WorkflowState.RUNNING
                self.terminal_output.add("Workflow started.")
            else:
                self.terminal_output.add("Workflow already running or paused.")
        elif action == "stop":
            self.workflow_state = WorkflowState.STOPPED
            self.terminal_output.add("Workflow stopped.")
        elif action == "pause":
            if self.workflow_state == WorkflowState.RUNNING:
                self.workflow_state = WorkflowState.PAUSED
                self.terminal_output.add("Workflow paused.")
            else:
                self.terminal_output.add("Workflow not running.")
        elif action == "resume":
            if self.workflow_state == WorkflowState.PAUSED:
                self.workflow_state = WorkflowState.RUNNING
                self.terminal_output.add("Workflow resumed.")
            else:
                self.terminal_output.add("Workflow not paused.")
        elif action == "status":
            self.terminal_output.add(f"Workflow state: {self.workflow_state.value}")
        else:
            self.terminal_output.add("Unknown workflow action.")

    def _cmd_agent(self, args):
        if not args:
            self.terminal_output.add("Usage: agent [start|stop]")
            return
        action = args[0].lower()
        if action == "start":
            self.terminal_output.add("Agent started (simulated).")
            self.agent_log.add("Agent activated.")
        elif action == "stop":
            self.terminal_output.add("Agent stopped (simulated).")
            self.agent_log.add("Agent deactivated.")
        else:
            self.terminal_output.add("Unknown agent action.")

    def _cmd_paper(self, args):
        if not args:
            self.terminal_output.add("Usage: paper list | paper apply <name>")
            return
        action = args[0].lower()
        if action == "list":
            if PAPERS_AVAILABLE:
                papers = ["chain_of_draft", "elastic_reasoning", "fp16_stability"]
                self.terminal_output.add(f"Available papers: {', '.join(papers)}")
            else:
                self.terminal_output.add("Paper system not available (import failed).")
        elif action == "apply" and len(args) > 1:
            paper_name = args[1]
            try:
                if paper_name == "chain_of_draft" and callable(apply_chain_of_draft):
                    apply_chain_of_draft(variant=self.config.get("chain_of_draft_variant", "baseline"))
                    if "chain_of_draft" not in self.config["active_papers"]:
                        self.config["active_papers"].append("chain_of_draft")
                    self.terminal_output.add(f"Applied paper: {paper_name}")
                elif paper_name == "elastic_reasoning" and callable(apply_elastic_reasoning):
                    apply_elastic_reasoning(
                        think_budget=self.config.get("elastic_reasoning_budget", {}).get("think", 50),
                        solve_budget=self.config.get("elastic_reasoning_budget", {}).get("solve", 150)
                    )
                    if "elastic_reasoning" not in self.config["active_papers"]:
                        self.config["active_papers"].append("elastic_reasoning")
                    self.terminal_output.add(f"Applied paper: {paper_name}")
                elif paper_name == "fp16_stability" and callable(apply_fp16_stability):
                    apply_fp16_stability()
                    if "fp16_stability" not in self.config["active_papers"]:
                        self.config["active_papers"].append("fp16_stability")
                    self.terminal_output.add(f"Applied paper: {paper_name}")
                else:
                    self.terminal_output.add(f"Paper '{paper_name}' not found or function unavailable.")
            except Exception as e:
                self.terminal_output.add(f"Error applying paper {paper_name}: {e}")
        else:
            self.terminal_output.add("Unknown paper command.")

    def _cmd_git(self, args):
        """Handle git commands by executing them via subprocess."""
        if not args:
            self.terminal_output.add("Usage: git <command> [arguments] (e.g., git add ., git push)")
            return
        result = execute_git(args)
        if result.success:
            self.terminal_output.add(f"Git output: {result.message}")
        else:
            self.terminal_output.add(f"Git error: {result.message}")

# ── Main entry point ──────────────────────
def main():
    parser = argparse.ArgumentParser(description="TruthGPT Dynamic Terminal v7.0")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    args = parser.parse_args()

    cfg = load_config()
    if args.config:
        with open(args.config, 'r') as f:
            cfg.update(json.load(f))

    terminal = DynamicTerminal(cfg)
    terminal.run()

if __name__ == "__main__":
    main()
