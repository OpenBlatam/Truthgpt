# OpenClaw Agents SDK API Reference

The OpenClaw Agents API (`agents/framework/client.py` and `agents/framework/architectures/base_agent.py`) provides the programmatic interface for multi-agent swarms, tool dispatch, and vector memory.

---

## 🏛️ `AgentClient` Class

```python
class AgentClient:
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        use_swarm: bool = False,
        use_vector_memory: bool = False,
        use_reflexion: bool = False,
    ) -> None: ...

    def add_tool(self, tool: Union[str, BaseTool]) -> None: ...

    async def run(
        self,
        user_id: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        return_response: bool = True
    ) -> AgentResponse: ...

    async def clear_memory(self, user_id: str) -> None: ...
```

---

## 🛠️ `BaseAgent` Custom Agent Interface

To implement a new specialized agent, inherit from `BaseAgent`:

```python
from agents.framework.architectures.base_agent import BaseAgent
from agents.framework.models import AgentResponse

class CustomSpecialistAgent(BaseAgent):
    def __init__(self, name: str = "SpecialistAgent"):
        super().__init__(name=name, role="Domain Expert")

    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        # Custom reasoning and tool execution
        return AgentResponse(
            content="Result of domain computation",
            agent_name=self.name,
            action_type="final_answer"
        )
```

---

## 📦 `AgentResponse` Schema

- `content: str` — Final text response from the agent.
- `agent_name: str` — Name of the agent that resolved the query.
- `action_type: str` — Action indicator (`"final_answer"`, `"delegation"`, `"tool_error"`).
- `tool_calls: List[Dict[str, Any]]` — List of tool executions executed during the ReAct loop.
- `trace_id: Optional[str]` — OpenTelemetry trace identifier.
