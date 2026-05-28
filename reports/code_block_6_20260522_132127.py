def adaptive_overdrive(agent_name, baseline_duration):
    if baseline_duration > 300:
        return 2.0  # doble de recursos
    elif baseline_duration > 100:
        return 1.5
    return 1.4