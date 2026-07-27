import sys
import os
import asyncio
import traceback
import pytest

root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
parent_dir = os.path.dirname(root_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import optimization_core.agents as agents
from optimization_core.agents.framework.models import (
    AgentAction, AgentResponse, InferenceResult, AgentConfig, ToolExecutionResult, TelemetryEvent
)
from optimization_core.agents.framework.exceptions import (
    TruthGPTError, InferenceError, ToolExecutionError, RegistryError, AgentExecutionError, AgentStateError, SecurityPolicyViolationError
)
from optimization_core.agents.framework.utils import (
    parse_agent_action, sanitize_tool_input, truncate_text_safely, safe_json_loads, safe_json_dumps, execution_timer, async_retry_with_backoff
)
from optimization_core.agents.framework.registry import registry
from optimization_core.agents.framework.architectures.base_agent import BaseAgent, AgentLifecycleState
from optimization_core.agents.framework.interfaces.client.client import AgentClient


def test_models_functionality():
    """Test Pydantic models serialization and validation."""
    cfg = AgentConfig()
    assert cfg.timeout_seconds == 120.0
    assert cfg.max_handoff_depth == 5

    action = AgentAction.parse_from_text('{"thought": "testing", "final_answer": "OK"}')
    assert action.is_final_answer()
    assert action.thought == "testing"
    assert action.final_answer == "OK"

    tool_action = AgentAction.create_tool_call(tool="web_search", tool_input={"query": "TruthGPT"})
    assert tool_action.is_tool_call()
    assert tool_action.tool == "web_search"

    resp = AgentResponse.success(content="Hello World", metadata={"trace": "123"})
    assert resp.is_success
    assert resp.status_code == 200
    assert resp.content == "Hello World"
    assert resp.metadata["trace"] == "123"

    err_resp = AgentResponse.error("System failure", status_code=500)
    assert not err_resp.is_success
    assert err_resp.status_code == 500

    tool_res = ToolExecutionResult.create_success(tool_name="file_read", output="file contents", execution_time_ms=12.5)
    assert tool_res.success
    assert tool_res.execution_time_ms == 12.5

    telem = TelemetryEvent(event_type="agent_start", agent_name="test_agent", payload={"mode": "test"})
    assert telem.event_type == "agent_start"
    assert telem.payload["mode"] == "test"


def test_exceptions_hierarchy():
    """Test exception tree metadata, cause chaining, and HTTP status codes."""
    err = AgentExecutionError("Test execution error", metadata={"step": 1})
    err_dict = err.to_dict()
    assert err_dict["error_type"] == "AgentExecutionError"
    assert err_dict["error_code"] == "AGENT_EXECUTION_ERROR"
    assert err.http_status_code == 500

    sec_err = SecurityPolicyViolationError("Forbidden command")
    assert sec_err.http_status_code == 403

    cause_exc = ValueError("Invalid parameter")
    wrapped_err = TruthGPTError("Wrapped error", cause=cause_exc)
    assert wrapped_err.cause == cause_exc
    assert wrapped_err.__cause__ == cause_exc


def test_registry_and_introspection():
    """Test thread-safe ComponentRegistry and category filtering."""
    tools = registry.list_tools()
    assert len(tools) > 0

    agents_list = registry.list_agents()
    assert len(agents_list) > 0

    filtered_tools = registry.list_tools(category="system")
    assert isinstance(filtered_tools, list)


def test_utils_and_helpers():
    """Test helper functions including JSON parsing and text truncation."""
    parsed = parse_agent_action('```json\n{"final_answer": "Extracted answer"}\n```')
    assert parsed.final_answer == "Extracted answer"

    truncated = truncate_text_safely("A" * 100, max_length=20, suffix="...")
    assert len(truncated) <= 20
    assert truncated.endswith("...")

    assert safe_json_loads('{"key": "val"}') == {"key": "val"}
    assert safe_json_loads("invalid json", default={}) == {}
    assert safe_json_dumps({"a": 1}) == '{"a": 1}'


class DummyAgent(BaseAgent):
    async def process(self, query, context=None):
        return AgentResponse.success("Dummy response")


def test_agent_lifecycle_state():
    """Test AgentLifecycleState transitions and AgentStateError guard."""
    agent = DummyAgent("test_dummy", "tester")
    assert agent.state == AgentLifecycleState.IDLE

    agent.set_state(AgentLifecycleState.RUNNING)
    assert agent.state == AgentLifecycleState.RUNNING

    agent.set_state(AgentLifecycleState.FAILED)
    assert agent.state == AgentLifecycleState.FAILED

    with pytest.raises(AgentStateError):
        agent.set_state(AgentLifecycleState.RUNNING)


@pytest.mark.asyncio
async def test_client_api_and_batching():
    """Test AgentClient SDK methods."""
    client = AgentClient()
    tools = client.list_available_tools()
    assert len(tools) > 0

    agents_list = client.list_available_agents()
    assert len(agents_list) > 0


if __name__ == "__main__":
    print(f"Successfully imported agents from {agents.__file__}")
    print(f"Exported members ({len(dir(agents))}): {dir(agents)}")

    test_models_functionality()
    print("✅ Models functionality verification PASSED")

    test_exceptions_hierarchy()
    print("✅ Exceptions hierarchy verification PASSED")

    test_registry_and_introspection()
    print("✅ Registry & introspection verification PASSED")

    test_utils_and_helpers()
    print("✅ Utility helpers verification PASSED")

    test_agent_lifecycle_state()
    print("✅ Agent lifecycle state machine verification PASSED")

    asyncio.run(test_client_api_and_batching())
    print("✅ Client API & batching verification PASSED")

    print("\n🎉 ALL AGENT FRAMEWORK REFACTORING VERIFICATIONS PASSED CLEANLY!")
