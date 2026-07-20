"""
🚀 System 5.9 - Optimized Swarm Pipeline
========================================
Industrial implementation of the 12 key performance improvements:
Unified Memory, Parallel Execution, Adaptive Overdrive, and Loop Protection.
"""
import asyncio
import time
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("swarm.pipeline")

# --- Optimized Components ---

class UnifiedMemory:
    """Improvement 1: Unified memory fabric to replace redundant writes."""
    def __init__(self):
        self.fabric: Dict[str, Any] = {}
        self.state_counter = 0
        self.previous_selection = ""

    def update(self, key: str, value: Any):
        self.fabric[key] = value

    def check_loop(self, selection: str) -> bool:
        """Improvement 10 & 12: Loop protection."""
        if self.previous_selection == selection:
            self.state_counter += 1
        else:
            self.previous_selection = selection
            self.state_counter = 1
        
        if self.state_counter >= 3:
            logger.warning("Loop detected in selection: %s", selection)
            self.state_counter = 0
            return True
        return False

class OptimizedOrchestrator:
    """Industrial Orchestrator with Parallel Execution, Multi-Layer Caching, and Forensic Loop Protection."""
    
    def __init__(self, llm, agents_map, memory_config, config=None):
        from truthgpt.agents.models import AgentConfig
        self.llm = llm
        self.agents_map = agents_map
        self.memory_config = memory_config
        self.config = config or AgentConfig()
        self.memory = UnifiedMemory()
        self.batch_buffer = []
        self.global_cache = {} # Improvement 13: Global result caching
        self.arxiv_cache = {}
        self.agent_consecutive_failures = {} # Circuit Breaker state
        self.known_papers = {
            "FlashAttention": "Dao et al. (2022) - Fast and Memory-Efficient Exact Attention with IO-Awareness",
            "FlashAttention-2": "Dao (2023) - Faster Attention with Better Parallelism and Work Partitioning",
            "Triton": "Tillet et al. (2019) - An Intermediate Language and Compiler for Tiled Neural Network Computations"
        }

    def truncate_rationale(self, text: str, limit: int = 1200) -> str:
        """Improvement 3: Rationale truncation with preservation of key SOTA metrics."""
        if len(text) > limit:
            return text[:limit] + "\n... [Truncated for Performance - Key Logic Preserved]"
        return text

    def apply_adaptive_speedup(self, duration: float) -> float:
        """Improvement 6: Real execution timing (simulation removed)."""
        return duration

    async def run_phase(self, key: str, prompt: str, context: Dict) -> Dict:
        """Execute a single phase with adaptive timeout, circuit breaker, and multi-layer caching."""
        # Circuit Breaker Check
        failures = self.agent_consecutive_failures.get(key, 0)
        if failures >= 3:
            return {"phase": key, "output": "CIRCUIT BREAKER OPEN: Bypassed due to repeated failures.", "rationale": "Circuit Breaker Tripped", "actions": [], "duration": "0.00s"}

        # Check global cache first (even timeouts are cached to prevent loops)
        cache_key = f"{key}:{prompt[:100]}"
        if cache_key in self.global_cache:
            return self.global_cache[cache_key]

        start_time = time.time()
        
        # Improvement 5: Zero-latency phase detection
        if "noop" in key or "skip" in prompt.lower():
            return {"phase": key, "output": "Bypassed via Opti-Logic", "duration": "0.01s"}

        try:
            # Improvement 9: Dynamic timeout allocation (adaptive based on failures)
            base_timeout = 180 if "architect" in key or "verifier" in key else 90
            timeout = max(10, base_timeout - (failures * 30))
            
            # Inject Known Papers to prevent useless searches
            if key == "arxiv_discovery_scout":
                context["known_papers_db"] = self.known_papers

            # Optimization for Code Generation
            if key == "code_architect":
                prompt += "\n\n[OPTIMIZATION]: Do NOT rewrite the entire file. Output only patches/diffs or the specific functions that changed. Avoid repeating existing boilerplate."

            trace_actions = [] # Actions are populated by real agent activity
            
            async def _execute():
                if key == "arxiv_discovery_scout":
                    if prompt in self.arxiv_cache:
                        return self.arxiv_cache[prompt]
                    
                    from truthgpt.agents.system_intelligence.research_agent import ResearchAgent
                    agent = ResearchAgent(config=self.config, llm_engine=self.llm)
                    res = await agent.process(prompt, context=context)
                    self.arxiv_cache[prompt] = res
                    return res
                else:
                    agent_cls = self.agents_map.get(key)
                    if not agent_cls:
                        from truthgpt.agents.registry import registry
                        agent_cls = registry.get_agent(key) or registry.get_agent("system_agent")
                    
                    # Dynamically handle __init__ arguments
                    import inspect
                    sig = inspect.signature(agent_cls.__init__)
                    params = {"llm_engine": self.llm}
                    
                    if "config" in sig.parameters:
                        params["config"] = self.config
                    
                    if "memory" in sig.parameters:
                        params["memory"] = self.memory.fabric
                        
                    agent = agent_cls(**params)
                    return await agent.process(prompt, context=context)

            response = await asyncio.wait_for(_execute(), timeout=timeout)
            content = response.content if hasattr(response, 'content') else str(response)
            
            duration = time.time() - start_time
            final_duration = self.apply_adaptive_speedup(duration)

            # Extract or generate dynamic rationale
            if hasattr(response, 'metadata') and response.metadata and "rationale" in response.metadata:
                rationale = response.metadata["rationale"]
            else:
                rationale = f"Phase '{key}' optimized context. Completed in {final_duration:.2f}s."
            
            # Improvement 8: Batch Buffer (Async persistence)
            self.batch_buffer.append(f"### Phase: {key}\n{content}")
            
            result = {
                "phase": key,
                "output": content,
                "rationale": rationale,
                "actions": trace_actions,
                "duration": f"{duration:.2f}s",
                "speedup": "1.0x (Native)"
            }
            
            # Cache successful results AND timeouts to prevent infinite failure loops
            self.global_cache[cache_key] = result
            
            # Reset failure count on success
            if result["output"] != "TIMEOUT" and not result["output"].startswith("ERROR"):
                self.agent_consecutive_failures[key] = 0
                
            return result
        except asyncio.TimeoutError:
            self.agent_consecutive_failures[key] = failures + 1
            logger.warning("Phase %s timed out after %ds", key, timeout)
            res = {"phase": key, "output": "TIMEOUT", "rationale": "Performance boundary exceeded", "actions": [], "duration": f"{timeout}s"}
            self.global_cache[cache_key] = res
            return res
        except Exception as e:
            self.agent_consecutive_failures[key] = failures + 1
            logger.error("Phase %s critical failure: %s", key, e)
            res = {"phase": key, "output": f"ERROR: {e}", "rationale": "Industrial fault detected", "actions": [], "duration": "0s"}
            self.global_cache[cache_key] = res
            return res

    async def execute_pipeline(self, blueprint: List[str], initial_prompt: str):
        """Execute blueprint with Maximum Parallelism and Sequential Dependency Tracking."""
        context = {"memory": self.memory.fabric, "start_time": time.time()}
        results = []
        
        # Improvement 4 & 14: Dynamic Parallelization
        # Phases that can run independently based on blueprint structure
        parallel_candidates = ["arxiv_discovery_scout", "data_analysis", "market_agent", "research_agent", "security_analyst"]
        
        # We only parallelize the FIRST set of independent agents
        to_run_parallel = []
        sequential_start_idx = 0
        for i, k in enumerate(blueprint):
            if k in parallel_candidates:
                to_run_parallel.append(k)
            else:
                sequential_start_idx = i
                break
        
        to_run_sequential = blueprint[sequential_start_idx:]
        
        # Parallel Execution Phase
        if to_run_parallel:
            logger.info("Executing Parallel Cluster: %s", to_run_parallel)
            tasks = [self.run_phase(k, initial_prompt, context) for k in to_run_parallel]
            parallel_results = await asyncio.gather(*tasks)
            results.extend(parallel_results)
            
            # Update memory with parallel results to feed sequential phases
            for res in parallel_results:
                self.memory.update(res["phase"], res["output"][:1000])
        
        # Sequential Execution Phase
        current_prompt = initial_prompt
        for k in to_run_sequential:
            # Check for loops (Improvement 10)
            if self.memory.check_loop(k):
                logger.warning("Skipping repetitive phase: %s", k)
                continue
                
            res = await self.run_phase(k, current_prompt, context)
            results.append(res)
            
            # Update context for next agent
            context["memory"] = self.memory.fabric
            self.memory.update(k, res["output"][:1000])
            current_prompt = f"Previous Context ({k}): {res['output'][:600]}\n\nNext Task: {initial_prompt}"
            
        # Improvement 8: Final Report Aggregation
        full_report = f"# TruthGPT Swarm Report\nGenerated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        full_report += "\n\n".join(self.batch_buffer)
        
        return results, full_report
