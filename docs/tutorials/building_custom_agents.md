# Building Custom Agents & Tool Augmentation

This tutorial guides you through building a specialized domain agent with custom tools and integrating it into the OpenClaw Agent Swarm.

---

## 🛠️ Step 1: Define Custom Python Tools

Tools in OpenClaw can be defined using callable functions or by subclassing `BaseTool`:

```python
from agents.framework.tools.tool_base import BaseTool

def profile_cuda_kernel(kernel_name: str) -> dict:
    """Profiles active CUDA kernel execution time in microseconds."""
    return {
        "kernel": kernel_name,
        "average_duration_us": 142.6,
        "occupancy_pct": 94.2,
        "sm_efficiency_pct": 88.7
    }
```

---

## 🐝 Step 2: Implement the Specialist Agent

```python
from agents.framework.architectures.base_agent import BaseAgent
from agents.framework.models import AgentResponse
from agents.unified_agent_registry import agent_registry

@agent_registry.register("gpu_kernel_profiler_agent")
class GPUKernelProfilerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="gpu_kernel_profiler_agent",
            name="GPUKernelProfilerAgent",
            role="Specialist in GPU profiling, occupancy analysis, and SM efficiency optimization"
        )

    async def process(self, query: str, context: dict = None) -> AgentResponse:
        # 1. Execute profiling logic
        profiling_data = profile_cuda_kernel("triton_fused_rmsnorm")
        
        # 2. Synthesize recommendations
        analysis = (
            f"Profiled {profiling_data['kernel']}:\n"
            f"- Latency: {profiling_data['average_duration_us']} µs\n"
            f"- SM Efficiency: {profiling_data['sm_efficiency_pct']}%\n"
            f"Recommendation: Increase block size to 256 for 100% SM saturation."
        )
        
        return AgentResponse(
            content=analysis,
            agent_name=self.name,
            action_type="final_answer"
        )
```

---

## 🚀 Step 3: Test Agent via Swarm Client

```python
import asyncio
from agents import AgentClient, AgentConfig

async def main():
    config = AgentConfig(use_swarm=True, default_agent_name="gpu_kernel_profiler_agent")
    client = AgentClient(config=config)
    
    response = await client.run(
        user_id="dev_01",
        prompt="Analyze why our fused RMSNorm kernel is dropping GPU occupancy."
    )
    print(response.content)

if __name__ == "__main__":
    asyncio.run(main())
```
