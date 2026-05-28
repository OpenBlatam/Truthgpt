# Before: sequential, redundant embedding fetch
# After: cached embeddings + parallel async DAG

from functools import lru_cache
import asyncio

@lru_cache(maxsize=1)
def get_embeddings():
    return load_cross_layer_embeddings()  # heavy I/O done once

async def run_pipeline(task):
    emb = get_embeddings()
    # independent phases
    research, arxiv, sota = await asyncio.gather(
        research_agent(emb, task),
        arxiv_scout(emb, task),
        sota_integrator(emb, task)
    )
    # code generation depends on research
    code = await code_architect(emb, task, research)
    # verification and system checks in parallel
    math_rep, sys_rep = await asyncio.gather(
        math_verifier(emb, code),
        system_agent(emb, code)
    )
    # single atomic forensic sync at end
    flush_final_state()
    return assemble_final_output(research, code, math_rep, sys_rep)