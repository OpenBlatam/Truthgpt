# continuous_agent_tui.py
# Path: optimization_core/continuous_agent_tui.py
"""
Dynamic Continuous Agent TUI with side-by-side Agent view and Terminal.
Uses Rich Layout to display:
  - Left panel: Agent thoughts / responses
  - Right panel: Real-time command execution (or log)
Integrated optimization pipeline runs on prompts.
"""

import sys
import json
from pathlib import Path
from typing import Any

from rich.live import Live
from rich.panel import Panel
from rich.console import Group
from rich.layout import Layout
from rich.text import Text
from rich import print as rprint

# Add parent to path for imports
_current_dir = Path(__file__).resolve().parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from optimization_pipeline import OptimizationPipeline
from papers.chain_of_draft import ChainOfDraft
from papers.elastic_reasoning import ElasticReasoning
from papers.fp16_stability import FP16Stability

# Simulated terminal / command execution (could wrap subprocess)
import subprocess
import queue
import threading


class ContinuousAgentTUI:
    """
    Renders a live dual-pane interface:
      - Pane 1: Agent output (last messages from the continuous agent)
      - Pane 2: Live terminal output (commands run via subprocess)
    """
    
    def __init__(self, prefs_path: Path = None):
        self.pipeline = OptimizationPipeline.from_config_file(prefs_path)
        self.agent_output_lines = []  # list of str
        self.terminal_output_lines = []
        self._stop_event = threading.Event()
        self._command_queue = queue.Queue()  # commands to execute
        self._process = None
        self._terminal_thread = None
        
        # Layout definition
        self.layout = Layout()
        self.layout.split_row(
            Layout(name="agent", ratio=1),
            Layout(name="terminal", ratio=1),
        )
    
    def add_agent_line(self, line: str):
        self.agent_output_lines.append(line)
        if len(self.agent_output_lines) > 20:  # keep only recent
            self.agent_output_lines.pop(0)
    
    def add_terminal_line(self, line: str):
        self.terminal_output_lines.append(line)
        if len(self.terminal_output_lines) > 20:
            self.terminal_output_lines.pop(0)
    
    def start_terminal_process(self, cmd: str = "cmd.exe"):
        """Launch a persistent shell process and capture its stdout."""
        self._stop_event.clear()
        self._process = subprocess.Popen(
            cmd, shell=True, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )
        
        def reader():
            try:
                for line in iter(self._process.stdout.readline, ''):
                    if self._stop_event.is_set():
                        break
                    if line:
                        self.add_terminal_line(line.rstrip())
            except Exception:
                pass
                
        self._terminal_thread = threading.Thread(target=reader, daemon=True)
        self._terminal_thread.start()
    
    def send_command(self, cmd: str):
        """Send a command to the terminal process and capture output."""
        if self._process and self._process.stdin:
            try:
                self._process.stdin.write(cmd + '\n')
                self._process.stdin.flush()
            except Exception as e:
                self.add_terminal_line(f"[red]Error sending command: {e}[/red]")
    
    def stop(self):
        self._stop_event.set()
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()
        if self._terminal_thread:
            self._terminal_thread.join(timeout=2)
    
    def run(self):
        """Start the live TUI loop."""
        self.start_terminal_process()
        
        with Live(self.layout, refresh_per_second=10, screen=True) as live:
            while True:
                # Update the layout
                agent_panel = Panel(
                    Text("\n".join(self.agent_output_lines[-15:]) or "[italic]Agent waiting...[/italic]"),
                    title="🤖 Agent",
                    border_style="blue"
                )
                terminal_panel = Panel(
                    Text("\n".join(self.terminal_output_lines[-15:]) or "[italic]Terminal idle...[/italic]"),
                    title="💻 Terminal",
                    border_style="green"
                )
                
                self.layout["agent"].update(agent_panel)
                self.layout["terminal"].update(terminal_panel)
                
                # Check for incoming commands from a file/socket? For now just show static.
                # In a real implementation, you'd integrate the agent loop here.
                # For demonstration, we'll just sleep briefly.
                import time
                time.sleep(0.1)
                
                # Normally, we'd break on user input, but since this is a demonstration
                # we'll stop after a few seconds to show the concept.
                # In production, you'd have an event loop.
                # For now, we'll exit if a stop file exists (e.g., stop_tui.txt)
                if Path("stop_tui.txt").exists():
                    Path("stop_tui.txt").unlink()
                    break
        
        self.stop()


# ---- Integration helper for system_menu ----
def launch_continuous_agent_tui():
    """Entry point called from the menu."""
    # Load prefs
    prefs = {}
    prefs_path = Path(__file__).resolve().parent / "user_preferences.json"
    if prefs_path.exists():
        try:
            prefs = json.loads(prefs_path.read_bytes())
        except:
            pass
    tui = ContinuousAgentTUI(prefs_path)
    # Show a start message
    tui.add_agent_line("[bold yellow]Starting Continuous Agent with Optimization Pipeline[/bold yellow]")
    tui.add_agent_line(f"Enabled techniques: Chain of Draft ({tui.pipeline.chain_draft_variant}), Elastic Reasoning, FP16: {tui.pipeline.use_fp16}")
    tui.add_terminal_line("[cyan]Terminal ready[/cyan]")
    tui.run()
