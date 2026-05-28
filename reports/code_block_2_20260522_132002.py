async def run_pipeline(task_input):
    ctx = PipelineContext()
    # Fase 1: investigación y SOTA pueden ejecutarse juntos
    research_fut = asyncio.create_task(run_agent("research_agent", task_input, ctx))
    sota_fut = asyncio.create_task(run_agent("sota_integrator", task_input, ctx))
    research, sota = await asyncio.gather(research_fut, sota_fut)

    # Fase 2: planning depende de ellos
    plan = await run_agent("planning_agent", {"research": research, "sota": sota}, ctx)

    # Fase 3: tareas paralelas
    evo_fut = asyncio.create_task(run_agent("evolution_architect", plan, ctx))
    math_fut = asyncio.create_task(run_agent("math_verifier", plan, ctx))
    code_fut = asyncio.create_task(run_agent("code_architect", plan, ctx))
    arxiv_fut = asyncio.create_task(run_agent("arxiv_discovery_scout", plan, ctx))
    rl_fut = asyncio.create_task(run_agent("rl_agent", plan, ctx))
    evo, math, code, arxiv, rl = await asyncio.gather(evo_fut, math_fut, code_fut, arxiv_fut, rl_fut)

    # Fase 4: system agent consolida
    final = await run_agent("system_agent", {"all_outputs": ...}, ctx)
    return final