# 🤖 OpenClaw Agents API Reference

The `agents` module provides the SDK for autonomous ReAct agents, multi-agent swarms, DAG graph orchestration, persistent episodic memory, and webhook integrations.

---

## 🏛️ `AgentClient`

```python
from optimization_core.agents import AgentClient, AgentConfig
```

### Initialization
```python
client = AgentClient(
    config=AgentConfig(
        use_swarm=True,
        max_handoff_depth=8,
        use_vector_memory=True,
        use_reflexion=True,
        llm_model="gpt-4o"
    )
)
```

### Core Methods

#### `run(user_id: str, prompt: str, return_response: bool = False)`
Executes an agent task. If `use_swarm=True`, the prompt is semantically classified and delegated to the optimal specialist agent.
- **Parameters**:
  - `user_id` (`str`): Unique identifier for loading/saving episodic context.
  - `prompt` (`str`): Instruction or query for the agent.
  - `return_response` (`bool`): If `True`, returns structured `AgentResponse` object; if `False`, returns output text.
- **Returns**: `str` or `AgentResponse`.

#### `add_tool(tool_name_or_instance: Union[str, BaseTool])`
Registers a new tool into the agent's active reasoning execution environment.

#### `clear_memory(user_id: str)`
Purges episodic conversation history and cached vector embeddings for the specified user.

---

## 🐝 `SwarmOrchestrator`

```python
from optimization_core.agents.multi_agent.swarm import SwarmOrchestrator
```
Manages dynamic handoffs between specialized agents:
- `ResearchAgent`: Deep literature and web intelligence.
- `CodeInterpreterAgent`: Sandboxed code authoring, execution, and debugging.
- `DataAnalysisAgent`: Tabular, statistical, and plotting operations.
- `MarketingAgent`: SEO optimization and copy generation.

---

## 🕸️ `GraphOrchestrator`

```python
from optimization_core.agents.multi_agent.graph_orchestrator import GraphOrchestrator

graph = GraphOrchestrator()
graph.add_node("Scraper", scraper_agent)
graph.add_node("Analyzer", analyzer_agent)
graph.add_node("Reporter", reporter_agent)
graph.add_edge("Scraper", "Analyzer")
graph.add_edge("Analyzer", "Reporter")
graph.set_entry_point("Scraper")

result = await graph.run(user_id="analyst_1", input_data="Analyze Q3 cloud spend.")
```

---

## ⏰ `AgentScheduler`

```python
from optimization_core.agents.orchestration.scheduler.scheduler_api import AgentScheduler

scheduler = AgentScheduler(client)
scheduler.add_recurring(
    task_id="daily_gpu_audit",
    user_id="devops_admin",
    prompt="Run GPU cluster health check and summarize memory leaks",
    interval_seconds=86400
)
await scheduler.start()
```

---

## 📡 REST API & Webhook Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/v1/agent/run` | POST | Execute ReAct agent query with tools |
| `/v1/swarm/ask` | POST | Route query via semantic swarm router |
| `/v1/agent/memory/{user_id}` | DELETE | Wipe user memory session |
| `/v1/traces/recent` | GET | List recent execution spans and latency |
| `/v1/webhooks/telegram` | POST | Inbound webhook handler for Telegram bots |
| `/v1/webhooks/discord` | POST | Inbound webhook handler for Discord bots |
| `/v1/webhooks/slack` | POST | Inbound webhook handler for Slack events |
