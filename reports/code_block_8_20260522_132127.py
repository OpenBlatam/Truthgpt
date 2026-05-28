class PipelineContext:
    _instance = None
    def __init__(self):
        self._embeddings = None
        self._forensic_snapshot = None

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = retrieve_cross_layer_embeddings()
        return self._embeddings

    @property
    def forensic_snapshot(self):
        if self._forensic_snapshot is None:
            self._forensic_snapshot = get_forensic_state_snapshot()
        return self._forensic_snapshot