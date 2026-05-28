class BatchOutputCollector:
    def __init__(self):
        self.outputs = {}

    def add(self, phase: str, output):
        self.outputs[phase] = output

    async def commit_all(self):
        await hybrid_fabric.batch_commit(self.outputs)