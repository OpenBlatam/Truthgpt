# Autonomous Agents & OpenClaw Overview

The **OpenClaw Agent Framework** inside TruthGPT is an enterprise-ready autonomous agent system featuring **ReAct reasoning**, **Self-Reflexion**, **Hierarchical Swarms**, **ChromaDB Vector Memory**, and **Multi-Channel Webhooks**.

---

## 🏗️ Agent System Architecture

```
optimization_core/agents/
├── framework/              # Core Agent abstraction layers
│   ├── architectures/      # ReAct, Reflexion, Embodied RL agent base classes
│   └── models/             # AgentRequest, AgentResponse, ToolCall schemas
├── orchestration/          # Swarm routing & graph state machines
│   ├── swarm.py            # Semantic router & handoff orchestrator
│   ├── graph.py            # DAG workflow state-machine executor
│   └── scheduler/          # Cron task scheduler & queue
├── domains/                # Domain-specialized agent implementations
│   ├── code_interpreter.py # Sandboxed Python execution & iterative debugging
│   ├── research.py         # SOTA paper discovery & analysis
│   ├── marketing.py        # SEO, content strategy, & ad funnels
│   └── data_analysis.py    # Pandas, NumPy, and Matplotlib data pipelines
├── unified_agent_registry.py # Dynamic agent discovery registry
└── messaging/              # Multi-channel webhook adapters (Telegram, WhatsApp, Slack, etc.)
```

---

## 🔄 The ReAct + Reflexion Loop

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Router as Swarm Router
    participant Agent as Specialized Agent (e.g. CodeInterpreter)
    participant Tool as Tool Executor (Python/Web)
    participant Memory as ChromaDB / SQLite

    User->>Router: Prompt: "Analyze dataset and plot loss curve"
    Router->>Memory: Query episodic context & user history
    Memory-->>Router: Inject relevant past context
    Router->>Agent: Route task to CodeInterpreterAgent
    
    loop ReAct Loop
        Agent->>Agent: Thought: "I need to load the CSV first"
        Agent->>Tool: Action: python_execute("import pandas as pd; df = ...")
        Tool-->>Agent: Observation: "Columns: step, loss, lr (1000 rows)"
    end

    opt Reflexion Phase (if enabled)
        Agent->>Agent: Critique output quality & verify image artifact existence
    end

    Agent->>Memory: Persist interaction episode
    Agent->>User: Final Answer + Generated Plot
```

---

## 🚀 Quick Usage Example

```python
import asyncio
from openclaw import AgentClient, AgentConfig

async def main():
    # 1. Configure OpenClaw Client
    config = AgentConfig(
        use_swarm=True,
        use_vector_memory=True,
        use_reflexion=True
    )
    
    client = AgentClient(config=config)
    
    # 2. Run query (automatically routed to best agent)
    response = await client.run(
        user_id="researcher_42",
        prompt="Search for recent developments in KV-cache compression and write a summary."
    )
    
    print(f"[{response.agent_name}]: {response.content}")

if __name__ == "__main__":
    asyncio.run(main())
```
