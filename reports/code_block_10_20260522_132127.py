def skip_if_empty_input(func):
    def wrapper(agent_input, ctx):
        if not agent_input or agent_input == {}:
            return {"output": None, "skipped": True}
        return func(agent_input, ctx)
    return wrapper