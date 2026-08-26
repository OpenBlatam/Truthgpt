# 🤖 Quickstart: OpenClaw Agent Swarms

OpenClaw is TruthGPT's autonomous agent framework featuring ReAct reasoning loops, dynamic tool calling, multi-agent swarm orchestration, long-term vector memory (ChromaDB), and multi-platform webhook integrations.

---

## ⚡ 1. Command Line Swarm

Use the `openclaw` CLI for zero-code agent queries and multi-agent coordination:

```bash
# Single agent question
openclaw swarm ask "What are the latest breakthroughs in FlashAttention-3?"

# Persistent session with user memory
openclaw swarm ask "Analyze our latency logs and suggest batch size improvements." --user engineer_1
```

---

## 🐍 2. Python SDK: Single ReAct Agent

Instantiate an autonomous agent equipped with sandboxed tools:

```python
import asyncio
from optimization_core.agents import AgentClient

async def main():
    # Initialize single ReAct agent client
    client = AgentClient(use_swarm=False)

    # Register built-in sandboxed tools
    client.add_tool("web_search")
    client.add_tool("python_execute")
    client.add_tool("file_read")
    client.add_tool("file_write")

    # Execute complex multi-step reasoning prompt
    prompt = (
        "Search for the top 3 KV cache optimization techniques, "
        "write a summary script in Python, and save it to kv_cache_summary.py."
    )

    response = await client.run(user_id="researcher_1", prompt=prompt)
    print("Agent Response:\n", response)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🐝 3. Multi-Agent Swarm Mode

Swarm mode uses an intelligent semantic router to dispatch user requests to specialized domain experts:

```python
import asyncio
from optimization_core.agents import AgentClient, AgentConfig

async def swarm_example():
    config = AgentConfig(
        use_swarm=True,
        max_handoff_depth=6,
        use_vector_memory=True,       # ChromaDB episodic retrieval
        use_reflexion=True            # Self-critique & error correction
    )
    client = AgentClient(config=config)

    # Marketing query -> routed to ContentMarketingAgent
    res1 = await client.run("user_101", "Design an SEO campaign for our LLM compiler.")
    print(f"[{res1.agent_name}]: {res1.content}")

    # Code optimization query -> routed to CodeInterpreterAgent
    res2 = await client.run("user_101", "Profile the attention kernel in polyglot_core/core/attention/engine.py.")
    print(f"[{res2.agent_name}]: {res2.content}")

if __name__ == "__main__":
    asyncio.run(swarm_example())
```

---

## 🌐 4. Launching the Agent REST API Server

Run the production FastAPI agent server for microservice architectures:

```bash
# Start server on port 8080 with 4 workers
python cli.py serve --port 8080 --workers 4
```

### Key Endpoints:
- `POST /v1/agent/run` - Execute ReAct agent query
- `POST /v1/swarm/ask` - Execute routed swarm query
- `DELETE /v1/agent/memory/{user_id}` - Clear episodic user memory
- `GET /v1/traces/recent` - Inspect agent execution traces & spans

---

## ⏭️ Next Steps

- Learn how to build custom tools and agent architectures in [Custom Agent Development](../guides/custom_agent_development.md).
- Read the full [Agents API Reference](../api/agents.md).
