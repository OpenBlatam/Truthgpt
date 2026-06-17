# optimization_core/embedding_cache.py
class EmbeddingCache:
    def __init__(self):
        self.cache = LRUCache(maxsize=10000)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def get_or_compute_embeddings(self, text_input):
        cache_key = hashlib.md5(text_input.encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        embeddings = self.embedding_model.encode(text_input)
        self.cache[cache_key] = embeddings
        return embeddings