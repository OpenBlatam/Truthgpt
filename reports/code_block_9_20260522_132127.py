import asyncio

class OptimizationCore:
    async def run_pipeline(self, task_input):
        ctx = PipelineContext()

        # Fase 1: Trabajo independiente
        research_task = asyncio.create_task(run_agent("research_agent", task_input, ctx))
        sota_task = asyncio.create_task(run_agent("sota_integrator", task_input, ctx))
        await asyncio.gather(research_task, sota_task)

        # Fase 2: Planificación (depende de fase 1)
        plan_output = await run_agent("planning_agent", task_input, ctx)

        # Fase 3: Evolución y verificación en paralelo
        evo_task = asyncio.create_task(run_agent("evolution_architect", plan_output, ctx))
        math_task = asyncio.create_task(run_agent("math_verifier", plan_output, ctx))
        await asyncio.gather(evo_task, math_task)

        # Fase 4: Commit unificado
        await batch_commit_hybrid_fabric(ctx.outputs)