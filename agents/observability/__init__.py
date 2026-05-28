"""
OpenClaw -- Agent Observability & Tracing.

Provides a lightweight tracing system that records every agent action
(tool calls, LLM decisions, routing events) with timing and metadata.
Designed for debugging, auditing, and performance optimisation.
"""

import logging
import threading
import time
import uuid
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict, computed_field

logger = logging.getLogger(__name__)

_INPUT_TRUNCATE = 500
_OUTPUT_TRUNCATE = 500


class Span(BaseModel):
    """A single traced event in an agent execution (Pydantic-validated)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    span_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    trace_id: str = ""
    parent_id: Optional[str] = None
    name: str = ""
    agent_name: str = ""
    kind: str = Field(default="internal", description="llm_call | tool_call | routing | internal")
    input_data: str = ""
    output_data: str = ""
    status: str = Field(default="ok", description="ok | error")
    start_time: float = Field(default_factory=time.time)
    end_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @computed_field  # type: ignore[misc]
    @property
    def duration_ms(self) -> float:
        if self.end_time == 0.0:
            return 0.0
        return round((self.end_time - self.start_time) * 1000, 2)

    def finish(self, output: str = "", status: str = "ok", metadata: Optional[Dict[str, Any]] = None) -> None:
        # Guard against double-finish (a leaked span may already have a real end_time)
        if self.end_time == 0.0:
            self.end_time = time.time()
        if output:
            self.output_data = output[:_OUTPUT_TRUNCATE]
        self.status = status
        if metadata:
            self.metadata.update(metadata)

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "agent": self.agent_name,
            "kind": self.kind,
            "input": self.input_data[:200],
            "output": self.output_data[:200],
            "status": self.status,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


class Tracer:
    """
    Lightweight in-memory tracer for agent executions.

    Usage::

        tracer = Tracer()

        # Start a trace for a user request
        trace_id = tracer.start_trace("user_request", agent_name="ReActAgent")

        # Record a tool call
        span = tracer.start_span(trace_id, "web_search", kind="tool_call",
                                 input_data="search query")
        # ... tool executes ...
        span.finish(output="search results")

        # Get the full trace
        print(tracer.get_trace(trace_id))
    """

    def __init__(self, max_traces: int = 1000, persistence_path: str = "traces_history.json") -> None:
        self.max_traces = max_traces
        self.persistence_path = Path(persistence_path)
        self._traces: Dict[str, List[Span]] = {}
        self._trace_order: List[str] = []
        self._persistence_loaded = False
        self._lock = threading.Lock()
        # Only the finish of a trace forces a disk write. start_trace / start_span
        # update the in-memory store and rely on the eventual finish_trace flush,
        # which avoids the O(n²) full-history rewrite per span.

    def _ensure_loaded(self) -> None:
        """Lazy-load persisted traces on first access."""
        if not self._persistence_loaded:
            self._load_traces()
            self._persistence_loaded = True

    def start_trace(
        self,
        name: str,
        agent_name: str = "",
        input_data: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new trace and return its ID."""
        self._ensure_loaded()
        trace_id = str(uuid.uuid4())[:12]

        root_span = Span(
            trace_id=trace_id,
            name=name,
            agent_name=agent_name,
            kind="internal",
            input_data=(input_data or "")[:_INPUT_TRUNCATE],
            metadata=dict(metadata or {}),
        )
        with self._lock:
            self._traces[trace_id] = [root_span]
            self._trace_order.append(trace_id)
            # Evict old traces
            while len(self._trace_order) > self.max_traces:
                old_id = self._trace_order.pop(0)
                self._traces.pop(old_id, None)
        return trace_id

    def start_span(
        self,
        trace_id: str,
        name: str,
        kind: str = "internal",
        input_data: str = "",
        parent_id: Optional[str] = None,
        agent_name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Add a new span to an existing trace."""
        self._ensure_loaded()
        span = Span(
            trace_id=trace_id,
            parent_id=parent_id,
            name=name,
            agent_name=agent_name,
            kind=kind,
            input_data=(input_data or "")[:_INPUT_TRUNCATE],
            metadata=dict(metadata or {}),
        )
        with self._lock:
            spans = self._traces.get(trace_id)
            if spans is not None:
                spans.append(span)
        return span

    def finish_trace(
        self,
        trace_id: str,
        output: str = "",
        status: str = "ok",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Mark the root span of the trace as finished and persist."""
        with self._lock:
            spans = self._traces.get(trace_id)
            if not spans:
                return
            root = spans[0]
            if root.end_time != 0.0:
                # Already finished — idempotent, skip persist.
                return
            root.finish(output=output, status=status, metadata=metadata)
        self._save_traces()

    def get_trace(self, trace_id: str) -> List[dict]:
        """Return all spans for a trace as dicts."""
        self._ensure_loaded()
        spans = self._traces.get(trace_id, [])
        return [s.to_dict() for s in spans]

    def get_recent_traces(self, limit: int = 20) -> List[dict]:
        """Return a summary of the most recent traces."""
        self._ensure_loaded()
        results = []
        for tid in reversed(self._trace_order[-limit:]):
            spans = self._traces.get(tid, [])
            if spans:
                root = spans[0]
                results.append({
                    "trace_id": tid,
                    "name": root.name,
                    "agent": root.agent_name,
                    "span_count": len(spans),
                    "duration_ms": root.duration_ms,
                    "status": root.status,
                })
        return results

    def get_stats(self) -> dict:
        """Return aggregate stats across all stored traces."""
        self._ensure_loaded()
        total_spans = sum(len(s) for s in self._traces.values())
        errors = sum(
            1
            for spans in self._traces.values()
            for s in spans
            if s.status == "error"
        )
        return {
            "total_traces": len(self._traces),
            "total_spans": total_spans,
            "error_spans": errors,
            "error_rate": round(errors / max(total_spans, 1), 4),
        }

    # ------------------------------------------------------------------
    # Persistence (uses Pydantic model_dump for serialization)
    # ------------------------------------------------------------------

    def _save_traces(self) -> None:
        """Serialize current traces to a JSON file via Pydantic model_dump.

        Writes atomically via a sibling tmp file + os.replace so a crash mid-write
        cannot corrupt traces_history.json.
        """
        import os
        try:
            with self._lock:
                data = {
                    tid: [s.model_dump() for s in spans]
                    for tid, spans in self._traces.items()
                }
            tmp_path = self.persistence_path.with_suffix(self.persistence_path.suffix + ".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.persistence_path)
        except Exception as e:
            logger.error("Failed to save trace history: %s", e)

    def _load_traces(self) -> None:
        """Load traces from the history file."""
        if not self.persistence_path.exists():
            return

        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for tid, spans_data in data.items():
                    spans = [Span.model_validate(s_data) for s_data in spans_data]
                    self._traces[tid] = spans
                    self._trace_order.append(tid)
            logger.info("Restored %d traces from persistence.", len(self._traces))
        except Exception as e:
            logger.error("Failed to load trace history: %s", e)


# Singleton tracer instance for the entire application
global_tracer = Tracer()

