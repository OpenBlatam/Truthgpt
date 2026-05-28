async def execute_pipeline(inputs):
    # Fase 1: research y sota pueden ejecutarse en paralelo
    research_task = asyncio.create_task(run_agent("research_agent", inputs))
    sota_task = asyncio.create_task(run_agent("sota_integrator", inputs))
    research_out, sota_out = await asyncio.gather(research_task, sota_task)

    # Fase 2: planning depende de ellos
    plan_out = await run_agent("planning_agent", {"research": research_out, "sota": sota_out})

    # Fase 3: evolución, verificación, arxiv, código en paralelo
    evo_task = asyncio.create_task(run_agent("evolution_architect", plan_out))
    math_task = asyncio.create_task(run_agent("math_verifier", plan_out))
    arxiv_task = asyncio.create_task(run_agent("arxiv_discovery_scout", plan_out))
    code_task = asyncio.create_task(run_agent("code_architect", plan_out))
    evo, math, arxiv, code = await asyncio.gather(evo_task, math_task, arxiv_task, code_task)

    # Fase final: system_agent consolida todo
    final_out = await run_agent("system_agent", {...})
    return final_out