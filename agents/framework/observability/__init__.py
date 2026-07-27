"""
OpenClaw -- Agent Observability & Tracing.

Provides a lightweight tracing system that records every agent action
(tool calls, LLM decisions, routing events) with timing and metadata.
Designed for debugging, auditing, and performance optimisation.
"""

from __future__ import annotations

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

    # ------------------------------------------------------------------
    # Intelligent Health Analysis
    # ------------------------------------------------------------------

    def analyze_health(self, last_n: int = 50) -> dict:
        """Compute a health score and detailed metrics from recent traces.

        Returns a dict with:
        - health_score (0-100): overall system health
        - latency_avg_ms, latency_p95_ms, latency_p99_ms
        - error_rate, dummy_rate, json_retry_rate
        - total_traces_analyzed
        - top_errors: list of (error_type, count)
        """
        self._ensure_loaded()
        recent_ids = self._trace_order[-last_n:]
        if not recent_ids:
            return {"health_score": 0, "total_traces_analyzed": 0, "message": "No traces available"}

        durations = []
        error_count = 0
        dummy_count = 0
        no_engine_count = 0
        json_retry_count = 0
        tool_call_total = 0
        error_types: Dict[str, int] = {}

        for tid in recent_ids:
            spans = self._traces.get(tid, [])
            if not spans:
                continue
            root = spans[0]
            if root.duration_ms > 0:
                durations.append(root.duration_ms)

            # Check root metadata for action_type errors
            action_type = root.metadata.get("action_type", "")
            if action_type in ("json_retry_exhausted", "mock_echo_detected", "mock_in_json_retry", "no_engine_configured", "iteration_limit", "unhandled_exception"):
                error_count += 1
                error_types[action_type] = error_types.get(action_type, 0) + 1

            if root.status in ("error", "no_engine"):
                if root.status not in error_types:
                    error_types[root.status] = error_types.get(root.status, 0) + 1

            tool_call_total += root.metadata.get("tool_calls", 0)
            json_retry_count += root.metadata.get("json_retries", 0)

            # Check child spans for dummy/no_engine
            for span in spans:
                if span.status in ("dummy_fallback", "no_engine"):
                    dummy_count += 1
                    break

        n = len(recent_ids)
        sorted_durations = sorted(durations) if durations else [0]

        def _percentile(data: list, pct: float) -> float:
            if not data:
                return 0.0
            idx = int(len(data) * pct / 100)
            return data[min(idx, len(data) - 1)]

        error_rate = error_count / max(n, 1)
        dummy_rate = dummy_count / max(n, 1)

        # Health score: start at 100, deduct for issues
        score = 100
        score -= min(50, int(error_rate * 100))  # Up to -50 for errors
        score -= min(30, int(dummy_rate * 60))    # Up to -30 for dummy fallbacks
        score -= min(10, json_retry_count // max(n, 1) * 5)  # Up to -10 for retries
        if tool_call_total == 0 and n > 5:
            score -= 10  # No tools used at all
        score = max(0, min(100, score))

        top_errors = sorted(error_types.items(), key=lambda x: -x[1])[:5]

        return {
            "health_score": score,
            "total_traces_analyzed": n,
            "latency_avg_ms": round(sum(durations) / max(len(durations), 1), 1),
            "latency_p95_ms": round(_percentile(sorted_durations, 95), 1),
            "latency_p99_ms": round(_percentile(sorted_durations, 99), 1),
            "error_rate": round(error_rate, 4),
            "dummy_rate": round(dummy_rate, 4),
            "json_retry_total": json_retry_count,
            "tool_calls_total": tool_call_total,
            "top_errors": top_errors,
        }

    def detect_anomalies(self, last_n: int = 20) -> List[dict]:
        """Detect anomalies in recent traces and return actionable alerts.

        Each alert has: severity (critical/warning/info), type, message, suggestion.
        """
        health = self.analyze_health(last_n)
        alerts: List[dict] = []

        if health.get("total_traces_analyzed", 0) == 0:
            return [{"severity": "info", "type": "no_data", "message": "No traces to analyze.", "suggestion": "Run the agent to generate traces."}]

        # CRITICAL: All traces use dummy engine
        if health.get("dummy_rate", 0) > 0.5:
            alerts.append({
                "severity": "critical",
                "type": "no_real_engine",
                "message": f"{health['dummy_rate']*100:.0f}% of traces used DummyAsyncLLM (no real engine).",
                "suggestion": "Configure at least one API key: DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, or OPENROUTER_API_KEY in Settings > Engines.",
            })

        # CRITICAL: High error rate
        if health.get("error_rate", 0) > 0.3:
            alerts.append({
                "severity": "critical",
                "type": "high_error_rate",
                "message": f"Error rate is {health['error_rate']*100:.0f}% across last {last_n} traces.",
                "suggestion": "Check API keys, network connectivity, and model availability.",
            })

        # WARNING: JSON retry storms
        avg_retries = health.get("json_retry_total", 0) / max(health.get("total_traces_analyzed", 1), 1)
        if avg_retries > 1.0:
            alerts.append({
                "severity": "warning",
                "type": "json_retry_storm",
                "message": f"Average {avg_retries:.1f} JSON retries per trace. LLM is not producing valid JSON.",
                "suggestion": "Check if the LLM engine supports structured output. Consider switching to a more capable model.",
            })

        # WARNING: High latency
        if health.get("latency_p95_ms", 0) > 30000:
            alerts.append({
                "severity": "warning",
                "type": "high_latency",
                "message": f"P95 latency is {health['latency_p95_ms']/1000:.1f}s (threshold: 30s).",
                "suggestion": "Check if the LLM is timing out. Consider using a faster model or increasing timeout.",
            })

        # INFO: Zero tool calls
        if health.get("tool_calls_total", 0) == 0 and health.get("total_traces_analyzed", 0) > 5:
            alerts.append({
                "severity": "info",
                "type": "no_tools_used",
                "message": "No tool calls were made in any recent trace.",
                "suggestion": "The agent may not be using its tools effectively, or all queries are simple Q&A.",
            })

        # Top errors breakdown
        for err_type, count in health.get("top_errors", []):
            if count >= 3:
                alerts.append({
                    "severity": "warning",
                    "type": f"recurring_error:{err_type}",
                    "message": f"Error '{err_type}' occurred {count} times in last {last_n} traces.",
                    "suggestion": f"Investigate root cause of '{err_type}' errors.",
                })

        return alerts or [{"severity": "info", "type": "healthy", "message": "System appears healthy.", "suggestion": "No action needed."}]

    def get_trace_summary_for_improvement(self) -> str:
        """Generate a human-readable summary of trace health for system improvement."""
        health = self.analyze_health(last_n=100)
        anomalies = self.detect_anomalies(last_n=50)

        lines = ["═══ TruthGPT Trace Health Report ═══", ""]

        score = health.get("health_score", 0)
        if score >= 80:
            grade = "🟢 HEALTHY"
        elif score >= 50:
            grade = "🟡 DEGRADED"
        else:
            grade = "🔴 CRITICAL"

        lines.append(f"Health Score: {score}/100 ({grade})")
        lines.append(f"Traces Analyzed: {health.get('total_traces_analyzed', 0)}")
        lines.append(f"Error Rate: {health.get('error_rate', 0)*100:.1f}%")
        lines.append(f"Dummy Fallback Rate: {health.get('dummy_rate', 0)*100:.1f}%")
        lines.append(f"Avg Latency: {health.get('latency_avg_ms', 0):.0f}ms")
        lines.append(f"P95 Latency: {health.get('latency_p95_ms', 0):.0f}ms")
        lines.append(f"JSON Retries: {health.get('json_retry_total', 0)}")
        lines.append(f"Tool Calls: {health.get('tool_calls_total', 0)}")
        lines.append("")

        if anomalies:
            lines.append("── Alerts ──")
            for alert in anomalies:
                icon = {"critical": "🔴", "warning": "🟡", "info": "ℹ️"}.get(alert["severity"], "•")
                lines.append(f"  {icon} [{alert['type']}] {alert['message']}")
                lines.append(f"    → {alert['suggestion']}")
            lines.append("")

        if health.get("top_errors"):
            lines.append("── Top Errors ──")
            for err_type, count in health["top_errors"]:
                lines.append(f"  • {err_type}: {count}x")

        lines.append("═" * 38)
        return "\n".join(lines)


# Singleton tracer instance for the entire application
global_tracer = Tracer()

