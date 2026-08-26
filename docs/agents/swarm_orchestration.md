# Swarm Orchestration & Multi-Agent Workflows

The **TruthGPT Swarm Subsystem** (`agents/orchestration/swarm.py`, `agents/orchestration/graph.py`) coordinates teams of specialized AI agents to solve complex, multi-step tasks through semantic routing, hierarchical task delegation, and DAG-based state machines.

---

## 🐝 Swarm Semantic Routing

Rather than sending all requests to a single monolithic prompt, the **Swarm Router** evaluates user intent using vector embeddings and semantic classifiers to dispatch the query to the most qualified agent.

```python
from openclaw import AgentClient

# Enable multi-agent swarm
client = AgentClient(use_swarm=True, max_handoff_depth=5)

# Queries are dynamically classified and routed:
# 1. Routes to ResearchAgent
await client.run("user_1", "What are the differences between MHA and GQA?")

# 2. Routes to CodeInterpreterAgent
await client.run("user_1", "Write and run a Python script to benchmark matrix multiplication.")

# 3. Routes to MarketingAgent
await client.run("user_1", "Generate a launch announcement for our new open-source model.")
```

---

## 🕸️ DAG Graph Orchestrator

For deterministic multi-stage pipelines where data must flow through specific stages:

```python
from optimization_core.agents.orchestration.graph import GraphOrchestrator
from optimization_core.agents.domains import ResearchAgent, CodeInterpreterAgent, DataAnalysisAgent

# 1. Initialize Graph Orchestrator
graph = GraphOrchestrator()

# 2. Add Agent Nodes
graph.add_node("Researcher", ResearchAgent())
graph.add_node("Coder", CodeInterpreterAgent())
graph.add_node("Analyst", DataAnalysisAgent())

# 3. Define Dependencies (Edges)
graph.add_edge("Researcher", "Coder")
graph.add_edge("Coder", "Analyst")
graph.set_entry_point("Researcher")

# 4. Execute Pipeline
result = await graph.run(
    user_id="user_1",
    initial_input="Find the fastest FlashAttention Triton implementation and run a benchmark."
)
```
