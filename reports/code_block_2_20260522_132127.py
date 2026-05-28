async def sync_forensic_delta(agent_output):
    new_hash = hash_state(agent_output)
    if new_hash != last_known_hash:
        delta = compute_delta(last_known_state, agent_output)
        await apply_forensic_delta(delta)
        last_known_hash = new_hash