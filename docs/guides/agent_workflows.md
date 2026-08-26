# Practical Guide: Building Complex Agent Workflows

This guide walks through constructing multi-agent research and development workflows using the **OpenClaw Agent SDK**.

---

## 🏗️ Building an Automated Code Review & Refactoring Swarm

We will create a multi-agent team consisting of:
1. **LinterAgent**: Inspects Python code for PEP-8 and typing errors.
2. **RefactorAgent**: Re-writes functions with type hints and optimized docstrings.
3. **TesterAgent**: Executes unit tests in a sandbox to verify correctness.

```python
import asyncio
from openclaw import AgentClient, AgentConfig
from optimization_core.agents.orchestration.graph import GraphOrchestrator

async def run_swarm_pipeline():
    config = AgentConfig(use_swarm=True, use_vector_memory=True)
    client = AgentClient(config=config)
    
    # 1. Run prompt through orchestrated pipeline
    prompt = """
    Here is an unoptimized Python function:
    def slow_dot(a, b):
        s = 0
        for i in range(len(a)):
            s += a[i] * b[i]
        return s

    Refactor this using NumPy/PyTorch SIMD vectorization and write a test case.
    """
    
    response = await client.run(user_id="lead_engineer", prompt=prompt)
    print("=== Refactored Solution ===")
    print(response.content)

if __name__ == "__main__":
    asyncio.run(run_swarm_pipeline())
```
