# Tutorial: Building Custom OpenClaw Agents

This tutorial demonstrates creating a custom autonomous agent from scratch with custom domain knowledge, system prompts, and tool execution capabilities.

---

## 🛠️ Step 1: Subclass `BaseAgent`

Create `agents/domains/database_admin.py`:

```python
from optimization_core.agents.framework.architectures.base_agent import BaseAgent
from optimization_core.agents.framework.models import AgentResponse

class DatabaseAdminAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="DatabaseAdminAgent",
            role="Specialist in SQL schema optimization and query indexing"
        )

    async def process(self, query: str, context: dict = None) -> AgentResponse:
        # Custom reasoning and SQL plan inspection
        analysis = f"Inspected SQL query for optimization: {query}\nRecommendation: Add composite B-Tree index on (user_id, created_at)."
        return AgentResponse(
            content=analysis,
            agent_name=self.name,
            action_type="final_answer"
        )
```

---

## 🐝 Step 2: Register Agent with Swarm

```python
from openclaw import AgentClient
from agents.domains.database_admin import DatabaseAdminAgent

client = AgentClient(use_swarm=True)
client.register_agent(DatabaseAdminAgent())

# Test query routing
response = await client.run(
    user_id="dev_1",
    prompt="My Postgres query on user transactions is taking 4 seconds. How can I optimize it?"
)

print(f"Handled by: {response.agent_name}")
print(response.content)
```
