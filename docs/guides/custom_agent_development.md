# 🤖 Custom Agent & Tool Development Guide

Learn how to build domain-specialized autonomous agents, register custom tools, construct multi-step workflows, and integrate webhook endpoints into the OpenClaw ecosystem.

---

## 🛠️ 1. Building a Custom Specialized Agent

To create a new agent, inherit from `BaseAgent` and implement the asynchronous `process()` method:

```python
from optimization_core.agents.framework.architectures.base_agent import BaseAgent
from optimization_core.agents.framework.models import AgentResponse

class DatabaseOptimizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="DatabaseOptimizationAgent",
            role="SQL & Indexing Performance Specialist"
        )

    async def process(self, query: str, context: dict = None) -> AgentResponse:
        # Custom reasoning and tool invocation logic
        thought = f"Analyzing SQL query patterns in: {query}"
        
        # Execute tool or LLM synthesis
        result_plan = "Recommended Index: CREATE INDEX idx_users_created ON users(created_at);"
        
        return AgentResponse(
            content=result_plan,
            agent_name=self.name,
            action_type="final_answer",
            metadata={"thought": thought}
        )
```

---

## 🔧 2. Registering Custom Tools

Create tools by subclassing `BaseTool` or using the `@tool` decorator:

```python
from optimization_core.agents.tools.base import BaseTool

class QueryDatabaseTool(BaseTool):
    name = "query_database"
    description = "Executes read-only SQL queries against Postgres database and returns rows."

    def execute(self, sql_query: str) -> str:
        # Execute in sandboxed DB connection
        return f"Returned 12 rows for query: {sql_query}"
```

### Attaching Tools to the Agent Client:
```python
from optimization_core.agents import AgentClient

client = AgentClient()
client.add_tool(QueryDatabaseTool())
```

---

## 🐝 3. Adding Agents to the Swarm Router

Register your custom agent into the Swarm Orchestrator so queries are automatically routed based on semantic intent:

```python
from optimization_core.agents.multi_agent.swarm import SwarmOrchestrator

orchestrator = SwarmOrchestrator()
orchestrator.register_agent(
    agent=DatabaseOptimizationAgent(),
    semantic_description="Specialist in database query planning, indexing, and Postgres tuning."
)
```

---

## 🕸️ 4. Multi-Step Graph Pipelines

For complex sequential workflows that require multi-stage execution with validations:

```python
from optimization_core.agents.orchestration.graph_orchestrator import GraphOrchestrator

graph = GraphOrchestrator()
graph.add_node("Extractor", data_extractor_agent)
graph.add_node("Analyzer", data_analyzer_agent)
graph.add_node("Validator", validation_agent)

graph.add_edge("Extractor", "Analyzer")
graph.add_edge("Analyzer", "Validator")
graph.set_entry_point("Extractor")

result = await graph.run(user_id="user_42", initial_input="Extract and validate Q2 metrics.")
```

---

## 📡 5. Integrating Custom Webhooks

OpenClaw supports bidirectional webhook integrations for chat platforms:

```python
from optimization_core.agents.messaging.telegram import TelegramAdapter

adapter = TelegramAdapter(bot_token="YOUR_TELEGRAM_BOT_TOKEN")
# Start webhook listener
adapter.start_polling(agent_client=client)
```
