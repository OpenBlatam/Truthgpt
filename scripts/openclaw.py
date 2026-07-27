"""
OpenClaw Compatibility Layer for TruthGPT.
Allows users to 'import openclaw' and use the same high-level API.
Integrates directly with the OpenClaw Deep Refiner V2 Gateway (System 5.9).
"""

import aiohttp
import asyncio
import time
from typing import Optional

import truthgpt
from agents.framework.interfaces.client.client import AgentClient
from optimization_core.agents.framework.models import AgentConfig, AgentResponse

# Alias for the main API instance
api = truthgpt.api

# Re-export key methods for direct access if needed
ask = truthgpt.api.ask
list_papers = truthgpt.api.list_papers
get_paper_info = truthgpt.api.get_paper_info
apply_paper = truthgpt.api.apply_paper

# Gateway Client for OpenClaw Deep Refiner V2
OPENCLAW_GATEWAY_URL = "http://127.0.0.1:18789"

async def deep_refine(prompt: str, hours: float = 0.016, criteria: str = "Clarity, impact, and fidelity to the prompt", provider: str = "deepseek") -> Optional[str]:
    """
    Sends a refinement task to the local OpenClaw Deep Refiner Gateway (System 5.9).
    This function acts as an asynchronous client that polls for the result,
    and then displays TruthGPT's engine benchmarks.
    """
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        # 1. Submit the job
        payload = {
            "prompt": prompt,
            "hours": hours,
            "criteria": criteria,
            "provider": provider,
            "branches": 2,
            "top_k": 2
        }
        try:
            async with session.post(f"{OPENCLAW_GATEWAY_URL}/refine", json=payload) as response:
                if response.status != 202:
                    print(f"[OpenClaw] Gateway error: {response.status}")
                    return None
                
                data = await response.json()
                job_id = data.get("job_id")
                print(f"[OpenClaw] Task submitted to Deep Refiner. Job ID: {job_id}")
        except Exception as e:
            print(f"[OpenClaw] Connection to Gateway failed. Is 'claw --serve' running? Error: {e}")
            return None

        # 2. Poll for completion
        while True:
            await asyncio.sleep(5)
            try:
                async with session.get(f"{OPENCLAW_GATEWAY_URL}/jobs/{job_id}") as poll_res:
                    if poll_res.status == 200:
                        status_data = await poll_res.json()
                        if status_data["status"] == "completed":
                            elapsed = time.time() - start_time
                            output_text = status_data.get("output", "")
                            score = status_data.get("score", "N/A")
                            print(f"[OpenClaw] Refinement complete! Score: {score}")
                            
                            # Integrar Benchmark de TruthGPT
                            try:
                                from optimization_core.agents.framework.engines.engine_benchmark import _display_truthgpt_benchmark, _record_benchmark_run
                                tokens = len(output_text) // 4
                                _record_benchmark_run("openclaw", f"OpenClaw ({provider})", elapsed, tokens)
                                await _display_truthgpt_benchmark(elapsed, model_name=f"OpenClaw ({provider})", tokens=tokens, engine_key="openclaw")
                            except Exception as bench_err:
                                print(f"[OpenClaw] Could not render benchmark: {bench_err}")
                            
                            return output_text
                        elif status_data["status"] == "failed":
                            print("[OpenClaw] Refinement failed.")
                            return None
            except Exception as e:
                print(f"[OpenClaw] Polling error: {e}")
                return None

__all__ = ["api", "ask", "list_papers", "get_paper_info", "apply_paper", "AgentClient", "AgentConfig", "AgentResponse", "deep_refine"]

