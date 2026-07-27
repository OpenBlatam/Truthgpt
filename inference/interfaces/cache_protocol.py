from typing import Protocol, Optional
from abc import abstractmethod

class KVCacheInterface(Protocol):
    """
    Protocol defining the contract for any KV Cache layer (Memory, Rust, Redis).
    """

    @abstractmethod
    def get(self, layer_idx: int, position: int, key: str) -> Optional[bytes]:
        """
        Retrieves cached data.
        """
        ...

    @abstractmethod
    def put(self, layer_idx: int, position: int, data: bytes, key: str) -> None:
        """
        Stores data into the cache.
        """
        ...

    @abstractmethod
    def evict(self, key: str) -> None:
        """
        Evicts a specific key from the cache.
        """
        ...

    @abstractmethod
    def stats(self) -> dict:
        """
        Retrieves cache telemetry (hit rates, memory usage).
        """
        ...
