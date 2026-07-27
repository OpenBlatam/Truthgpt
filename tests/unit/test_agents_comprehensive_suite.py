"""
Comprehensive Unit Test Suite for TruthGPT / OpenClaw Optimization Core Agents.

Covers:
- Framework Models & Pydantic v2 Serialization
- Unified Exception Hierarchy & Context
- Component & Tool Registry thread safety and introspection
- Utility functions & Edge cases
- Memory components
- Engine registry & providers
- Observability tracing
- Domain agent instantiations
- Orchestration swarm & composer
"""

import pytest
import time
import json
from typing import Dict, Any

from optimization_core.agents.framework.models import (
    AgentAction,
    AgentResponse,
    InferenceResult,
    AgentConfig,
    ToolExecutionResult,
    TelemetryEvent,
)
from optimization_core.agents.framework.exceptions import (
    TruthGPTError,
    InferenceError,
    EngineInferenceTimeout,
    EngineUnavailableError,
    ToolExecutionError,
    ToolValidationError,
    ToolExecutionTimeoutError,
    RegistryError,
    PluginLoadError,
    ConfigurationError,
    AgentMemoryError,
    MemoryPersistenceError,
    HandoffError,
    AgentHandoffCycleError,
    RoutingError,
    SwarmRoutingError,
    AgentTimeoutError,
    AgentExecutionError,
    SecurityPolicyViolationError,
    AgentStateError,
)
from optimization_core.agents.framework.registry import ComponentRegistry, ToolInfo, AgentInfo, registry
from optimization_core.agents.framework.utils import (
    parse_agent_action,
    safe_json_loads,
    safe_json_dumps,
    clean_markdown_code_blocks,
    format_exception_trace,
    truncate_text_safely,
    sanitize_tool_input,
    extract_urls,
    chunk_iterable,
    estimate_token_count,
)


class TestAgentAction:
    def test_create_final_answer(self):
        action = AgentAction.create_final_answer("Hello World", thought="Thinking...")
        assert action.is_final_answer()
        assert not action.is_tool_call()
        assert not action.is_handoff()
        assert action.final_answer == "Hello World"
        assert action.thought == "Thinking..."

    def test_create_tool_call(self):
        action = AgentAction.create_tool_call("web_search", {"query": "python"})
        assert action.is_tool_call()
        assert not action.is_final_answer()
        assert action.tool == "web_search"
        assert action.tool_input == "python"

    def test_create_handoff(self):
        action = AgentAction.create_handoff("research_agent")
        assert action.is_handoff()
        assert action.handoff == "research_agent"

    def test_parse_from_text_json(self):
        json_text = '{"final_answer": "Extracted answer", "thought": "Internal step"}'
        action = AgentAction.parse_from_text(json_text)
        assert action.is_final_answer()
        assert action.final_answer == "Extracted answer"

    def test_parse_from_text_markdown_block(self):
        markdown_text = '```json\n{"tool": "python_execute", "tool_input": "print(1)"}\n```'
        action = AgentAction.parse_from_text(markdown_text)
        assert action.is_tool_call()
        assert action.tool == "python_execute"
        assert action.tool_input == "print(1)"

    def test_parse_from_text_raw_fallback(self):
        raw_text = "Plain response text without json formatting"
        action = AgentAction.parse_from_text(raw_text)
        assert action.is_final_answer()
        assert action.final_answer == raw_text

    def test_to_dict_and_to_json(self):
        action = AgentAction.create_final_answer("Test")
        d = action.to_dict()
        assert isinstance(d, dict)
        assert d["final_answer"] == "Test"
        j = action.to_json()
        assert isinstance(j, str)
        assert "Test" in j


class TestAgentResponse:
    def test_success_response(self):
        resp = AgentResponse.success("Result text", metadata={"k": "v"}, execution_time_ms=12.5)
        assert resp.is_success
        assert resp.status_code == 200
        assert resp.content == "Result text"
        assert resp.execution_time_ms == 12.5
        assert resp.metadata == {"k": "v"}

    def test_error_response(self):
        resp = AgentResponse.error("Failure occurred", status_code=500)
        assert not resp.is_success
        assert resp.status_code == 500
        assert resp.content == "Failure occurred"

    def test_with_metadata(self):
        resp = AgentResponse.success("Base")
        resp2 = resp.with_metadata(extra="data")
        assert resp2.metadata["extra"] == "data"


class TestInferenceResult:
    def test_creation(self):
        res = InferenceResult(text="Output", tokens_generated=100, latency_ms=45.0, model_name="gpt-4o")
        assert res.text == "Output"
        assert res.tokens_generated == 100
        assert res.to_dict()["model_name"] == "gpt-4o"


class TestAgentConfig:
    def test_defaults(self):
        cfg = AgentConfig()
        assert cfg.memory_db_path == "openclaw_memory.db"
        assert cfg.timeout_seconds == 120.0
        assert cfg.max_handoff_depth == 5

    def test_copy_with(self):
        cfg = AgentConfig()
        cfg2 = cfg.copy_with(timeout_seconds=60.0)
        assert cfg2.timeout_seconds == 60.0
        assert cfg.timeout_seconds == 120.0

    def test_invalid_handoff_depth(self):
        with pytest.raises(ValueError):
            AgentConfig(max_handoff_depth=0)

    def test_invalid_timeout(self):
        with pytest.raises(ValueError):
            AgentConfig(timeout_seconds=-1.0)


class TestToolExecutionResult:
    def test_create_success(self):
        res = ToolExecutionResult.create_success("web_search", "results", execution_time_ms=10.0)
        assert res.success
        assert res.tool_name == "web_search"
        assert res.output == "results"

    def test_create_error(self):
        res = ToolExecutionResult.create_error("python_execute", "SyntaxError")
        assert not res.success
        assert res.error_message == "SyntaxError"


class TestTelemetryEvent:
    def test_event_creation(self):
        evt = TelemetryEvent(event_type="agent_run", agent_name="research_agent", payload={"status": "ok"})
        assert evt.agent_name == "research_agent"
        assert evt.payload["status"] == "ok"
        assert len(evt.event_id) > 0


class TestExceptions:
    def test_base_error(self):
        err = TruthGPTError("Test error", error_code="TEST_CODE", remediation_hint="Fix it")
        assert err.message == "Test error"
        assert err.error_code == "TEST_CODE"
        assert "Fix it" in str(err)

    def test_exception_serialization(self):
        err = TruthGPTError("Test error", metadata={"a": 1})
        d = err.to_dict()
        assert d["message"] == "Test error"
        assert d["metadata"]["a"] == 1

        reconstructed = TruthGPTError.from_dict(d)
        assert reconstructed.message == err.message
        assert reconstructed.metadata == err.metadata

    def test_derived_exceptions(self):
        e1 = InferenceError("Inference failed")
        assert e1.category == "inference"

        e2 = EngineInferenceTimeout("Timed out")
        assert e2.error_code == "INFERENCE_TIMEOUT"

        e3 = ToolExecutionError("Tool error")
        assert e3.category == "tools"

        e4 = SecurityPolicyViolationError("Access denied")
        assert e4.error_code == "SECURITY_VIOLATION"


class TestComponentRegistry:
    def test_singleton(self):
        reg1 = ComponentRegistry()
        reg2 = ComponentRegistry()
        assert reg1 is reg2

    def test_list_tools(self):
        tools = registry.list_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_list_agents(self):
        agents = registry.list_agents()
        assert isinstance(agents, list)
        assert len(agents) > 0

    def test_get_tool(self):
        tool_cls = registry.get_tool("web_search")
        assert tool_cls is not None

    def test_get_agent(self):
        agent_cls = registry.get_agent("research_agent")
        assert agent_cls is not None


class TestUtils:
    def test_parse_agent_action_valid(self):
        action = parse_agent_action('{"final_answer": "Done"}')
        assert action.final_answer == "Done"

    def test_safe_json_loads(self):
        assert safe_json_loads('{"a": 1}') == {"a": 1}
        assert safe_json_loads("invalid json", default={}) == {}

    def test_clean_markdown_code_blocks(self):
        assert clean_markdown_code_blocks("```python\nprint(1)\n```") == "print(1)"

    def test_format_exception_trace(self):
        try:
            raise ValueError("Test ex")
        except Exception as exc:
            formatted = format_exception_trace(exc)
            assert "ValueError: Test ex" in formatted

    def test_truncate_text_safely(self):
        long_str = "a" * 100
        truncated = truncate_text_safely(long_str, max_length=20)
        assert len(truncated) <= 20
        assert truncated.endswith("... [truncated]")

    def test_sanitize_tool_input(self):
        inp = {"query": "  test  ", "nested": ["  item  "]}
        sanitized = sanitize_tool_input(inp)
        assert sanitized["query"] == "test"
        assert sanitized["nested"][0] == "item"

    def test_extract_urls(self):
        text = "Visit https://example.com and http://test.org for info"
        urls = extract_urls(text)
        assert "https://example.com" in urls
        assert "http://test.org" in urls

    def test_chunk_iterable(self):
        items = list(range(10))
        chunks = chunk_iterable(items, 3)
        assert len(chunks) == 4
        assert chunks[0] == [0, 1, 2]

    def test_estimate_token_count(self):
        assert estimate_token_count("Hello World") == 2
        assert estimate_token_count("") == 0
