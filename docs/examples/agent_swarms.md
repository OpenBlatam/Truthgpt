# 💡 Example: Autonomous Research Swarm

This example demonstrates orchestrating a multi-agent swarm that decomposes complex research questions, executes sandboxed code, and writes a synthesized report.

---

## 🐍 Complete Python Script

```python
import asyncio
from optimization_core.agents import AgentClient, AgentConfig

async def run_research_swarm():
    # 1. Configure the swarm client
    config = AgentConfig(
        use_swarm=True,
        max_handoff_depth=8,
        use_vector_memory=True,       # Persistent semantic memory
        use_reflexion=True            # Self-critique & error correction
    )
    client = AgentClient(config=config)

    # 2. Add sandboxed tools
    client.add_tool("web_search")
    client.add_tool("python_execute")
    client.add_tool("file_write")

    # 3. Define multi-step research inquiry
    query = (
        "Investigate the differences between FlashAttention-2 and FlashAttention-3. "
        "Write a Python script that benchmarks memory consumption for both formulas "
        "and save the report to research_report.md."
    )

    print("Submitting query to OpenClaw Swarm...")
    response = await client.run(user_id="research_scientist", prompt=query, return_response=True)

    print(f"\n--- Swarm Execution Completed by [{response.agent_name}] ---")
    print(response.content)

if __name__ == "__main__":
    asyncio.run(run_research_swarm())
```
