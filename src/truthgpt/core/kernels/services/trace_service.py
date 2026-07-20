import logging
from typing import Any, Dict, List
import json
import os
from pathlib import Path
from datetime import datetime

from ...interfaces import BaseService
from truthgpt.core.kernel.truthgpt_kernel import TruthGPTKernel

class TraceService(BaseService):
    """
    Service responsible for keeping persistent traces of why specific architectural 
    or AI decisions were chosen during execution.
    """
    def __init__(self, kernel: TruthGPTKernel, config: Dict[str, Any]):
        self.kernel = kernel
        self.config = config
        self.logger = logging.getLogger("TruthGPT.Kernel.TraceService")
        self._is_running = False
        self.decision_traces: List[Dict[str, Any]] = []
        
        # Persistence path
        self.storage_path = Path(os.getcwd()) / "truthgpt_collected" / "traces"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.trace_file = self.storage_path / "decision_traces.json"

    async def start(self) -> None:
        self.logger.info("Starting TraceService...")
        self._is_running = True
        self._load_traces()

    async def stop(self) -> None:
        self.logger.info("Stopping TraceService...")
        self._save_traces()
        self._is_running = False

    def record_decision(self, component: str, decision: str, rationale: str) -> None:
        """Record the trace of why a decision was made and save it."""
        trace = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "decision": decision,
            "rationale": rationale
        }
        self.decision_traces.append(trace)
        self.logger.info(f"Decision Trace [{component}]: {decision} -> {rationale}")
        
        # Auto-save for robustness
        if len(self.decision_traces) % 5 == 0:
            self._save_traces()

    def _load_traces(self) -> None:
        if self.trace_file.exists():
            try:
                with open(self.trace_file, "r", encoding="utf-8") as f:
                    self.decision_traces = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load traces: {e}")

    def _save_traces(self) -> None:
        try:
            with open(self.trace_file, "w", encoding="utf-8") as f:
                json.dump(self.decision_traces, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save traces: {e}")
