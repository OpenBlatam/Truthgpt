async def run_pipeline(plan):
    independent_tasks = [
        run_phase('research_agent', plan),
        run_phase('arxiv_discovery_scout', plan),
        run_phase('sota_integrator', plan)
    ]
    results = await asyncio.gather(*independent_tasks)
    # Sequential after: code_architect depends on research
    code = await run_phase('code_architect', plan, research_results)
    # math_verifier and system_agent can run in parallel
    await asyncio.gather(
        run_phase('math_verifier', plan, code),
        run_phase('system_agent', plan, code)
    )
    # final sync
    await sync_state()