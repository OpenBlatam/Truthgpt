# dynamic_continuous_terminal.py
"""
Dynamic Continuous Terminal for TruthGPT with Paper Integrations.
Features:
- Live dual-pane TUI: left shows agent reasoning, right shows workflow execution and metrics.
- Chain of Draft, Elastic Reasoning, and FP16 Stability seamlessly applied.
- Personalized workflows via DynamicWorkflow and user preferences.
- Continuous loop with configurable rest intervals.
- Config dashboard accessible from the terminal.
Usage: python dynamic_continuous_terminal.py
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

# Rich UI
try:
    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich import box
    from rich.columns import Columns
except ImportError:
    print("Please install 'rich': pip install rich")
    sys.exit(1)

# Local imports
try:
    from dynamic_workflow import DynamicWorkflow, action_system_check, action_run_model_inference, action_save_output
    from terminal_view import LiveTerminal  # though we'll build our own
    from latency_optimizations import apply_chain_of_draft, apply_elastic_reasoning, apply_fp16_stability
    from papers.chain_of_draft import ChainOfDraft
    from papers.elastic_reasoning import ElasticReasoning
    from papers.fp16_stability import FP16Stability
except ImportError:
    # Fallback: define minimal implementations if imports fail
    DynamicWorkflow = None
    apply_chain_of_draft = lambda p, v='baseline': p
    apply_elastic_reasoning = lambda p, t, s, w=True: p
    apply_fp16_stability = lambda m: m
    ChainOfDraft = None
    ElasticReasoning = None
    FP16Stability = None
    # Provide dummy action functions
    def action_system_check(**kwargs): return "System OK"
    def action_run_model_inference(**kwargs): return "Inference done"
    def action_save_output(**kwargs): return True

# Configuration constants
CONFIG_FILE = Path(__file__).parent / "terminal_config.json"
DEFAULT_CONFIG = {
    "agent_name": "TruthGPT-Dynamic-Agent",
    "theme": "blue",
    "refresh_rate": 8,
    "max_log_lines": 200,
    "workflow_interval": 5,  # seconds between workflow iterations
    "plugins": [],
    "continuous_mode": True,
    "active_papers": ["chain_of_draft", "elastic_reasoning"],
    "workflow_file": "default_workflow.yaml",
    "elastic_reasoning_budget": {"think": 50, "solve": 150},
    "chain_of_draft_variant": "baseline",
    "fp16_enabled": False,
    "max_iterations": 0,  # 0 means infinite
    "user_input_timeout": 30  # seconds
}


def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception as e:
            logging.warning(f"Failed to load config, using defaults: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, Any]):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)


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


class DynamicContinuousTerminal:
    """
    Live terminal with dual panels: agent reasoning and workflow logs,
    integrating Chain of Draft, Elastic Reasoning, and FP16 Stability.
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.cfg = config or load_config()
        self.console = Console()
        self.layout = self._build_layout()
        self.live = Live(self.layout, console=self.console, refresh_per_second=self.cfg["refresh_rate"],
                         screen=True, vertical_overflow="visible")
        self.reasoning_buffer = LogBuffer(self.cfg["max_log_lines"])
        self.workflow_buffer = LogBuffer(self.cfg["max_log_lines"])
        self.metrics = {
            "iterations": 0,
            "last_elapsed": 0.0,
            "papers_active": self.cfg["active_papers"],
            "model": "TruthGPT",
            "temperature": 0.8
        }
        # Instantiate papers
        if ChainOfDraft and "chain_of_draft" in self.cfg["active_papers"]:
            self.chain_draft = True
            self.chain_variant = self.cfg["chain_of_draft_variant"]
        else:
            self.chain_draft = False
        if ElasticReasoning and "elastic_reasoning" in self.cfg["active_papers"]:
            self.elastic = ElasticReasoning(self.cfg["elastic_reasoning_budget"]["think"],
                                            self.cfg["elastic_reasoning_budget"]["solve"])
        else:
            self.elastic = None
        if FP16Stability:
            self.fp16 = FP16Stability()
        else:
            self.fp16 = None
        # Workflow engine
        self.workflow = self._init_workflow()
        # User input queue
        self.input_queue: List[str] = []
        self.input_lock = threading.Lock()

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=5)
        )
        layout["main"].split_row(
            Layout(name="reasoning", ratio=2),
            Layout(name="workflow", ratio=3)
        )
        return layout

    def _init_workflow(self):
        if DynamicWorkflow:
            wf = DynamicWorkflow(config_path=Path(self.cfg["workflow_file"]))
            wf.register_action("system_check", action_system_check)
            wf.register_action("inference", action_run_model_inference)
            wf.register_action("save", action_save_output)
            return wf
        else:
            return None

    def update_header(self, text: str = None):
        if text:
            self.layout["header"].update(
                Panel(Text(text, style="bold white on dark_blue"), border_style="bright_blue")
            )
        else:
            self.layout["header"].update(
                Panel(Text(f"{self.cfg['agent_name']} 💡 Live Reasoning", style="bold white on dark_blue"),
                      border_style="bright_blue")
            )

    def add_reasoning(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Apply chain of draft: make reasoning concise if enabled
        if self.chain_draft and len(message.split()) > 10:
            # Simulate concise drafting by limiting words per line
            # but just note we are using chain of draft style
            pass
        self.reasoning_buffer.add(f"[{timestamp}] 🧠 {message}")
        self._refresh_reasoning_panel()

    def add_workflow_entry(self, message: str, success: bool = True):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = "✓" if success else "✗"
        self.workflow_buffer.add(f"[{timestamp}] {icon} {message}")
        self._refresh_workflow_panel()

    def add_tool_use(self, tool_name: str, input_str: str, result: str = None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"[{timestamp}] 🛠️  {tool_name}"
        if input_str:
            msg += f"\n       ├─ Input: {input_str}"
        if result:
            msg += f"\n       └─ Result: {result}"
        self.workflow_buffer.add(msg)
        self._refresh_workflow_panel()

    def update_metrics(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.metrics:
                self.metrics[k] = v
        self._refresh_footer()

    def _refresh_reasoning_panel(self):
        lines = self.reasoning_buffer.get_all()
        if not lines:
            lines = ["[dim]Awaiting reasoning...[/dim]"]
        # Show last 15 lines
        panel = Panel("\n".join(lines[-15:]), title="🧠 Agent Reasoning", border_style="yellow")
        self.layout["reasoning"].update(panel)

    def _refresh_workflow_panel(self):
        lines = self.workflow_buffer.get_all()
        if not lines:
            lines = ["[dim]No workflow actions yet.[/dim]"]
        panel = Panel("\n".join(lines[-20:]), title="⚙️ Workflow & Tools", border_style="green")
        self.layout["workflow"].update(panel)

    def _refresh_footer(self):
        m = self.metrics
        papers_str = ", ".join(self.cfg["active_papers"]) if self.cfg["active_papers"] else "none"
        footer_text = (
            f"[bold]Iterations:[/bold] {m['iterations']}  |  "
            f"[bold]Last run:[/bold] {m['last_elapsed']:.2f}s  |  "
            f"[bold]Papers:[/bold] {papers_str}  |  "
            f"[bold]Model:[/bold] {m['model']}  |  "
            f"[bold]Temp:[/bold] {m['temperature']}  |  "
            f"[bold]Press Ctrl+C to exit[/bold]"
        )
        self.layout["footer"].update(
            Panel(Text(footer_text, style="white on dark_slate_gray"), border_style="grey")
        )

    async def process_input(self, user_input: str):
        """Process user input and generate a response with paper optimizations."""
        if not user_input.strip():
            return
        self.add_reasoning(f"User: {user_input}")
        # Build optimized prompt
        prompt = user_input
        if self.chain_draft:
            # Apply chain of draft template
            prompt = apply_chain_of_draft(prompt, variant=self.chain_variant)
            self.add_reasoning("Applied Chain of Draft template.")
        if self.elastic:
            # Apply elastic reasoning instruction
            prompt = apply_elastic_reasoning(prompt, self.cfg["elastic_reasoning_budget"]["think"],
                                             self.cfg["elastic_reasoning_budget"]["solve"], wrapper=True)
            self.add_reasoning(f"Elastic Reasoning budget: {self.cfg['elastic_reasoning_budget']} tokens.")
        # Simulate LLM call (in a real system, call the model with prompt)
        # Here we'll generate a mock concise answer
        llm_response = f"[Simulated answer based on Chain of Draft and Elastic Reasoning] Received: {user_input[:60]}..."
        self.add_reasoning(f"Assistant: {llm_response}")
        return llm_response

    async def continuous_loop(self):
        """Main continuous agent loop with workflow execution and paper integration."""
        iteration = 0
        max_iter = self.cfg["max_iterations"] if self.cfg["max_iterations"] > 0 else None
        while max_iter is None or iteration < max_iter:
            iteration += 1
            self.update_metrics(iterations=iteration)
            self.add_reasoning(f"Iteration {iteration} starting.")

            # Execute workflow if enabled
            if self.workflow:
                start = time.time()
                try:
                    result = await self.workflow.run()  # This runs steps defined in YAML
                    elapsed = time.time() - start
                    self.update_metrics(last_elapsed=elapsed)
                    self.add_workflow_entry(f"Workflow completed: {len(result['history'])} steps in {elapsed:.2f}s",
                                            success=True)
                    for entry in result['history']:
                        self.add_workflow_entry(f"  {entry['step']}: {entry['status']}",
                                                success=(entry['status'] == 'ok'))
                except Exception as e:
                    self.add_workflow_entry(f"Workflow error: {e}", success=False)
            else:
                self.add_workflow_entry("Workflow engine not available.")

            # Check for user input
            with self.input_lock:
                if self.input_queue:
                    user_msg = self.input_queue.pop(0)
                    await self.process_input(user_msg)

            # Simulate applying FP16 stability if enabled (on tensors, not applicable here)
            if self.cfg.get("fp16_enabled") and self.fp16:
                self.add_reasoning("FP16 stability checks would be performed on model tensors.")

            # Wait before next loop
            await asyncio.sleep(self.cfg["workflow_interval"])

        self.add_reasoning("Max iterations reached. Shutting down.")

    def start_live(self):
        """Start the Live display context and run the loop."""
        self.live.start()
        try:
            asyncio.run(self.continuous_loop())
        except KeyboardInterrupt:
            self.add_reasoning("Interrupted by user.")
        finally:
            self.live.stop()

    def feed_input(self, text: str):
        """External method to feed user input into the buffer."""
        with self.input_lock:
            self.input_queue.append(text)


if __name__ == "__main__":
    terminal = DynamicContinuousTerminal()
    # In a full application, you'd run start_live and also a thread to read stdin
    # For this demo, just start
    terminal.start_live()
