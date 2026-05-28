class PipelineContext:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if not self.__initialized:
            self._embeddings = None
            self._forensic_snapshot = None
            self.__initialized = True

    async def get_embeddings(self):
        if self._embeddings is None:
            self._embeddings = await retrieve_cross_layer_embeddings()
        return self._embeddings

    async def get_forensic_snapshot(self):
        if self._forensic_snapshot is None:
            self._forensic_snapshot = await sync_forensic_persistent_state()
        return self._forensic_snapshot