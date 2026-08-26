# Tutorial: Building Custom Autonomous Agents & Tools

In this tutorial, you will create a custom OpenClaw agent equipped with domain-specific Python tools, connect it to vector memory, and deploy it inside the OpenClaw Swarm.

---

## 🛠️ Step 1: Define a Custom Tool

Create a custom tool class inheriting from `BaseTool`:

```python
from agents.framework.tools.base_tool import BaseTool

class GPUStatTool(BaseTool):
    name: str = "gpu_stat"
    description: str = "Queries active GPU temperature, VRAM allocation, and utilization percentage."

    async def execute(self, device_id: int = 0) -> str:
        import torch
        if not torch.cuda.is_available():
            return "No CUDA GPU detected on current host."
        
        allocated = torch.cuda.memory_allocated(device_id) / (1024 ** 3)
        reserved = torch.cuda.memory_reserved(device_id) / (1024 ** 3)
        device_name = torch.cuda.get_device_name(device_id)
        
        return f"Device: {device_name} | VRAM Allocated: {allocated:.2f} GB | Reserved: {reserved:.2f} GB"
```

---

## 🤖 Step 2: Implement the Domain Agent

Inherit from `BaseAgent`:

```python
from agents.framework.architectures.base_agent import BaseAgent
from agents.framework.models import AgentResponse

class InfrastructureAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="InfrastructureAgent", role="DevOps & GPU Cluster Diagnostics")
        self.register_tool(GPUStatTool())

    async def process(self, query: str, context: dict = None) -> AgentResponse:
        # ReAct reasoning loop
        response_text = await self.reason_and_act(query, max_steps=4)
        return AgentResponse(
            content=response_text,
            agent_name=self.name,
            action_type="final_answer"
        )
```

---

## 🐝 Step 3: Register Agent with OpenClaw Swarm

```python
import asyncio
from agents.framework.client import AgentClient
from agents.domains.unified_agent_registry import UNIFIED_AGENT_REGISTRY

# Register custom agent
UNIFIED_AGENT_REGISTRY.register("infrastructure", InfrastructureAgent)

async def test_agent():
    client = AgentClient(use_swarm=True)
    
    # Query is automatically routed to InfrastructureAgent
    result = await client.run(
        user_id="sre_engineer_1",
        prompt="Check GPU memory allocation on device 0 and recommend batch size adjustments."
    )
    print(f"Agent [{result.agent_name}] output:\n{result.content}")

if __name__ == "__main__":
    asyncio.run(test_agent())
```
