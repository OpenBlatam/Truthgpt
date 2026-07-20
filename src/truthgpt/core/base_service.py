"""Abstract base class for TruthGPT services."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseService(ABC):
    """Abstract base for all TruthGPT services."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config: Dict[str, Any] = config if config is not None else {}
        self._ready: bool = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service. Must set self._ready = True on success."""

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shut down the service."""

    def health_check(self) -> Dict[str, Any]:
        """Return basic health information."""
        return {"service": self.__class__.__name__, "ready": self._ready}

    def __enter__(self) -> "BaseService":
        self.initialize()
        return self

    def __exit__(self, *_: Any) -> None:
        self.shutdown()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} ready={self._ready}>"
