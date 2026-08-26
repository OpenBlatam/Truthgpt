# Autonomous Agent Workflows & Swarm Guide

This guide walks through architecting multi-agent swarms, creating domain tools, managing episodic and vector memory, and deploying live messaging webhooks using the **OpenClaw SDK**.

---

## 🐝 1. Creating Custom Tools

Tools allow agents to interact with external APIs, execute code, or query databases. Register tools using the `@tool` decorator:

```python
from agents.tools.base import tool

@tool(
    name="query_arxiv_papers",
    description="Searches ArXiv for the latest research papers by keyword."
)
async def query_arxiv_papers(query: str, max_results: int = 5) -> str:
    # Tool execution logic
    return f"Retrieved {max_results} papers for query: '{query}'"
```

---

## 🤖 2. Building a Multi-Agent Swarm

A swarm dynamically routes user requests to the most specialized agent using semantic embeddings:

```python
import asyncio
from agents import AgentClient, AgentConfig
from agents.framework.architectures.base_agent import BaseAgent
from agents.framework.models import AgentResponse

# 1. Define specialized expert agent
class DatabaseOptimizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="DatabaseOptimizationAgent",
            role="Expert in PostgreSQL indexing and query optimization."
        )

    async def process(self, query: str, context: dict = None) -> AgentResponse:
        return AgentResponse(
            content=f"Database plan generated for: {query}",
            agent_name=self.name,
            action_type="final_answer"
        )

# 2. Initialize Swarm Client
async def run_swarm():
    config = AgentConfig(use_swarm=True, use_reflexion=True)
    client = AgentClient(config=config)
    client.register_agent(DatabaseOptimizationAgent())

    # The swarm recognizes this is a database query and routes it automatically
    res = await client.run(
        user_id="dev_user",
        prompt="How should I index a table with 50M rows queried by user_id and timestamp?"
    )
    print(res)

asyncio.run(run_swarm())
```

---

## 🧠 3. ChromaDB Long-Term Memory (RAG)

OpenClaw automatically stores learned facts, preferences, and episode summaries into ChromaDB:

```python
# Enable long-term vector memory
config = AgentConfig(use_vector_memory=True)
client = AgentClient(config=config)

# Store memory
await client.store_fact(
    user_id="user_42",
    fact="The user prefers Python solutions using Polars instead of Pandas."
)

# Subsequent queries automatically inject this preference into context
response = await client.run(
    user_id="user_42",
    prompt="Write code to aggregate sales by region."
)
# Output will use Polars automatically
```

---

## 🔒 4. Human-In-The-Loop (HITL) Safety Gates

For destructive or critical operations (e.g., database deletions, financial transactions, shell commands):

```python
from agents.framework.safety import SafetyGate

safety = SafetyGate(require_approval_for=["database_drop", "deploy_production"])

client = AgentClient(config=config, safety_gate=safety)
```

If an agent attempts a sensitive tool call, execution pauses and emits an approval request payload to the webhook or CLI before proceeding.

---

## 🌐 5. Deploying Production Webhooks

Deploy your swarm as a continuous chatbot service across Telegram, Discord, and Slack:

```bash
# Set credentials
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
export DISCORD_BOT_TOKEN="MTA..."

# Start daemon
openclaw serve --port 8080 --webhooks telegram,discord
```
