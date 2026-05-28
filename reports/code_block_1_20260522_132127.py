class SharedPhaseContext:
    def __init__(self):
        self._embeddings = None
        self._forensic_state = None
        self._forensic_version = 0

    async def get_embeddings(self):
        if self._embeddings is None:
            self._embeddings = await retrieve_cross_layer_embeddings()
        return self._embeddings

    async def get_forensic_state(self):
        if self._forensic_state is None:
            self._forensic_state = await sync_forensic_persistent_state()
        return self._forensic_state