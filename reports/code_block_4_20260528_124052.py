# Nuevo: optimization_core/temporal_coordination.py
class TemporalCoordinator:
    def __init__(self):
        self.agent_graph = nx.DiGraph()  # Grafo de dependencias
        self.execution_planner = AsyncExecutionPlanner()
        
    def optimize_execution_order(self, agents, context):
        # Análisis de dependencias para paralelización
        independent_agents = self.find_independent_agents(agents)
        
        # Ejecuta agentes independientes en paralelo
        return self.execution_planner.parallel_execute(
            independent_agents,
            max_concurrency=4
        )