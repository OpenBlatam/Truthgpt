# Mejora: core/shared_memory.py
class AdvancedSharedMemory:
    def __init__(self):
        self.vector_store = ChromaDB()  # Para embeddings semánticos
        self.graph_memory = Neo4j()     # Para relaciones causales
        self.kv_cache = RedisCluster()  # Para cache distribuido
        
    def store_agent_result(self, agent_id, result, context):
        # Almacena con embeddings para búsqueda semántica
        embedding = self.embed(result)
        self.vector_store.add(embedding, metadata={"agent": agent_id})
        
        # Actualiza grafo de dependencias
        self.graph_memory.create_relation(context.previous_agent, agent_id, result)