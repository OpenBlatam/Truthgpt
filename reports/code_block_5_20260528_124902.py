# Nuevo: core/auto_healing.py
class AutoHealingSystem:
    def __init__(self):
        self.health_monitor = HealthMonitor()
        self.recovery_strategies = {
            'api_failure': self.activate_local_mode,
            'memory_pressure': self.optimize_memory,
            'inference_timeout': self.reduce_context_window
        }
    
    async def self_diagnose_and_heal(self):
        issues = await self.health_monitor.detect_issues()
        for issue in issues:
            strategy = self.recovery_strategies.get(issue.type)
            if strategy:
                await strategy(issue)