# En factories/agent_backends.py
AGENT_BACKENDS = Registry("agent_backends")

@AGENT_BACKENDS.register("hybrid")
class HybridAgentBackend:
    def __init__(self, config):
        self.primary = APIBackend(config.api)
        self.fallback = LocalModelBackend(config.local)
        self.circuit_breaker = CircuitBreaker()