class AgentCircuitBreaker:
    def __init__(self, timeout=120.0):
        self.timeout = timeout
        self.failure_count = defaultdict(int)

    async def run_with_breaker(self, agent_name, coro):
        if self.failure_count[agent_name] >= 3:
            print(f"Saltando {agent_name} (fallos repetidos)")
            return None
        try:
            result = await asyncio.wait_for(coro, timeout=self.timeout)
            self.failure_count[agent_name] = 0
            return result
        except asyncio.TimeoutError:
            self.failure_count[agent_name] += 1
            print(f"Timeout en {agent_name}")
            return None