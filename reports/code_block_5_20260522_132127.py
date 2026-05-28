def should_skip(agent_name):
    stats = get_agent_stats(agent_name)
    if stats['consecutive_nops'] > 2:
        return True
    return False