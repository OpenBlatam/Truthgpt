async def run_system_agent(checks_needed=False):
    if not checks_needed:
        quick_report = await health_light()  # <5s
        if quick_report.outlier_ratio > 0.1:
            await health_deep()
    else:
        await health_deep()
    # ... resto de la lógica