# optimization_core/adaptive_timeouts.py
class AdaptiveTimeoutManager:
    def __init__(self):
        self.agent_performance_history = {}
        self.base_timeouts = {
            'research_agent': 15,
            'code_architect': 120, 
            'system_agent': 150,
            'evolution_architect': 100
        }
    
    def get_dynamic_timeout(self, agent_type, complexity_score=1.0):
        base = self.base_timeouts.get(agent_type, 60)
        historical_avg = self.get_avg_duration(agent_type)
        
        # Ajuste dinámico basado en historial
        if historical_avg > base * 1.5:
            return int(base * 1.8 * complexity_score)
        elif historical_avg < base * 0.7:
            return int(base * 0.9 * complexity_score)
        
        return int(base * complexity_score)