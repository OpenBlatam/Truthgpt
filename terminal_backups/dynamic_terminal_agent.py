# dynamic_terminal_agent.py
"""
Dynamic Continuous Agent with Live Terminal Viewer for TruthGPT.
Provides a customizable workflow, personalized configuration, and a sidecar
terminal panel that shows real‑time logs and agent activity.

Usage:
    python dynamic_terminal_agent.py [--config dynamic_config.json]

Requirements:
    pip install rich textual asyncio  (textual for advanced TUI, rich for basic live)
"""

import asyncio
import json
import logging
import queue
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Config:
    """Dynamic configuration loaded from a JSON file."""
    def __init__(self, config_path: Optional[str] = None):
        self.data = {
            "agent_name": "DynamicTruthGPT",
            "max_iterations": 100,
            "log_level": "INFO",
            "plugins": [],
            "workflow_order": ["think", "tools", "observation", "answer"],
            "custom_prompts": {},
            "terminal_enabled": True,
            "log_file": "agent_activity.log"
        }
        if config_path:
            self.load(config_path)

    def load(self, path: str):
        with open(path, 'r') as f:
            user = json.load(f)
            self.data.update(user)


class EventEmitter:
    """Thread‑safe emitter for structured log events."""
    def __init__(self):
        self.listeners: List[queue.Queue] = []

    def subscribe(self):
        q: queue.Queue = queue.Queue()
        self.listeners.append(q)
        return q

    def emit(self, event_type: str, data: Dict[str, Any]):
        event = {"type": event_type, "data": data, "timestamp": time.time()}
        for q in self.listeners:
            q.put(event)


class ActionPipeline:
    """Orchestrates the sequence of actions based on workflow order."""
    def __init__(self, workflow_order: List[str]):
        self.order = workflow_order

    def execute(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for action in self.order:
            handler = getattr(self, f"_handle_{action}", None)
            if handler:
                result = handler(context)
                results.append(result)
        return results

    def _handle_think(self, ctx):
        return {"step": "think", "thought": "Considering dynamic factors...", "timestamp": time.time()}

    def _handle_tools(self, ctx):
        return {"step": "tools", "tools_used": [], "output": "No tools called"}

    def _handle_observation(self, ctx):
        return {"step": "observation", "observation": "Waiting for input"}

    def _handle_answer(self, ctx):
        return {"step": "answer", "answer": "I understand your query."}


class DynamicAgent:
    """Main continuous agent with dynamic workflow."""
    def __init__(self, config: Config):
        self.config = config
        self.emitter = EventEmitter()
        self.pipeline = ActionPipeline(config.data.get("workflow_order", ["think", "tools", "observation", "answer"]))
        self.logger = logging.getLogger("dynamic_agent")
        self._setup_logging()

    def _setup_logging(self):
        log_file = self.config.data.get("log_file", "agent_activity.log")
        logging.basicConfig(
            filename=log_file,
            level=getattr(logging, self.config.data.get("log_level", "INFO")),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

    async def run(self):
        """Run the continuous loop."""
        self.emitter.emit("agent_start", {"name": self.config.data["agent_name"]})
        self.logger.info("Agent started.")
        counter = 0
        max_iter = self.config.data.get("max_iterations", 100)
        while counter < max_iter:
            counter += 1
            # Simulate processing a turn
            context = {"iteration": counter, "timestamp": time.time()}
            self.emitter.emit("iteration_begin", context)
            self.logger.info(f"Iteration {counter} started.")
            
            # Execute pipeline
            results = self.pipeline.execute(context)
            for r in results:
                self.emitter.emit("step_completed", r)
                await asyncio.sleep(0.1)  # simulate work
            
            # Await new input (simulated)
            await asyncio.sleep(1)  # placeholder for actual user interaction
            
            self.emitter.emit("iteration_end", {"iteration": counter})
        self.emitter.emit("agent_stop", {"reason": "max_iterations"})
        self.logger.info("Agent loop finished.")


def terminal_viewer(emitter: EventEmitter):
    """
    Live terminal sidecar that displays agent events in a rich Live panel.
    Runs in a separate thread.
    """
    if not RICH_AVAILABLE:
        print("Rich not installed. Run: pip install rich")
        while True:
            try:
                event = emitter.subscribe().get(timeout=1)
                print(f"[{event['type']}] {event['data']}")
            except queue.Empty:
                continue
        return

    console = Console()
    event_queue = emitter.subscribe()

    def generate_layout() -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
        )
        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1),
        )
        return layout

    with Live(generate_layout(), refresh_per_second=4, screen=True) as live:
        while True:
            try:
                event = event_queue.get(timeout=0.5)
            except queue.Empty:
                live.update(generate_layout())
                continue

            # Update layout
            layout = live.renderable
            # Right panel for latest events
            events_str = f"[bold green]{event['type']}[/]\n{json.dumps(event['data'], indent=2)}"
            layout["right"].update(Panel(events_str, title="Latest Event"))
            # Left panel for log summary
            left_content = layout["left"]
            if not hasattr(left_content, "renderable"):
                left_content.update(Table(title="Agent Log", expand=True))
            live.update(layout)

    print("Terminal viewer exited.")


async def main():
    # Load config
    config = Config("dynamic_config.json") if Path("dynamic_config.json").exists() else Config()
    agent = DynamicAgent(config)

    # Start terminal viewer in a separate thread
    if config.data.get("terminal_enabled", True):
        viewer_thread = threading.Thread(target=terminal_viewer, args=(agent.emitter,), daemon=True)
        viewer_thread.start()
    else:
        viewer_thread = None

    try:
        await agent.run()
    finally:
        if viewer_thread:
            viewer_thread.join(timeout=1)


if __name__ == "__main__":
    asyncio.run(main())
