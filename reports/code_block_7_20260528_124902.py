# Modificar: core/generic_trainer.py → core/agent_orchestrator.py
class AgentOrchestrator(GenericTrainer):
    def __init__(self, config):
        super().__init__(config)
        self.agent_coordinator = TemporalCoordinator()
        self.resilient_engine = ResilientInferenceEngine()
        self.shared_memory = AdvancedSharedMemory()