import json
from pathlib import Path
from agents.models import AgentResponse
from agents.code_interpreter import CodeInterpreterAgent

class EvolutionArchitect(CodeInterpreterAgent):
    """
    Specialized agent that analyzes memory traces to self-improve the TruthGPT codebase.
    """
    async def process(self, task: str, context: dict = None) -> AgentResponse:
        trace_dir = Path("truthgpt_collected/logs/memory_traces")
        traces = []
        if trace_dir.exists():
            for f in sorted(trace_dir.glob("*.json"), reverse=True)[:5]:
                with open(f, 'r') as tf:
                    traces.append(json.load(tf))
        
        trace_summary = json.dumps(traces, indent=2)
        
        improvement_prompt = f"""
        Analyze the following execution traces from the TruthGPT System:
        {trace_summary}
        
        Identify recurring patterns, latencies, and rationales. 
        Propose specific code improvements for the optimization_core to make the system faster and more logical.
        Task: {task}
        """
        
        return await super().process(improvement_prompt, context)
