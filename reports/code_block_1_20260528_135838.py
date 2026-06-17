# optimization_core/resilient_inference.py
class ResilientInferenceEngine:
    def __init__(self):
        self.engines = {
            'primary': ExternalAPIEngine(),
            'secondary': LocalModelEngine(), 
            'emergency': RuleBasedEngine()
        }
        self.circuit_breaker = CircuitBreaker(failure_threshold=3)
    
    async def infer_with_cascade(self, prompt, agent_type):
        for engine_name, engine in self.engines.items():
            try:
                if engine.is_available():
                    result = await engine.process(prompt)
                    if self.validate_output(result):
                        return result
            except Exception as e:
                logging.warning(f"{engine_name} failed: {e}")
                continue
        
        # Emergency fallback
        return self.generate_structured_response(agent_type)