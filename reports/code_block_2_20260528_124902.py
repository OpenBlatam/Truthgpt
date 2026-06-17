# Nuevo: core/resilient_inference.py
class ResilientInferenceEngine:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            timeout=30,
            expected_exception=APIError
        )
        self.model_router = ModelRouter()
    
    async def infer_with_fallback(self, prompt, agent_type):
        # 1. Intenta API externa con circuit breaker
        if self.circuit_breaker.is_closed():
            try:
                return await self.external_api_call(prompt)
            except Exception as e:
                self.circuit_breaker.record_failure()
        
        # 2. Fallback a modelo local optimizado
        return await self.local_inference(prompt, agent_type)