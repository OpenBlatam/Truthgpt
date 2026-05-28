class EmbeddingCache:
    _cache = None
    @classmethod
    def get_embeddings(cls):
        if cls._cache is None:
            cls._cache = load_cross_layer_embeddings()  # heavy op
        return cls._cache

# In each phase:
embeddings = EmbeddingCache.get_embeddings()