"""
ModelService - Handles model inference and management
"""

import asyncio
from typing import Dict, Any, Optional, List
from .base_service import BaseService


class ModelService(BaseService):
    """Service for model lifecycle management and inference routing"""

    def __init__(self, kernel, config: Optional[Dict[str, Any]] = None):
        super().__init__(kernel, config)
        self._loaded_models: Dict[str, Any] = {}
        self._engine_registry = None

    async def _on_start(self) -> None:
        try:
            import agents.engines as ae
            self._engine_registry = ae.engine_registry
            self.logger.info("ModelService: engine registry loaded")
        except Exception as e:
            self.logger.warning(f"ModelService partial init: {e}")

    async def _on_stop(self) -> None:
        self._loaded_models.clear()
        self._engine_registry = None

    async def _get_health_info(self) -> Dict[str, Any]:
        return {
            "loaded_models": list(self._loaded_models.keys()),
            "engine_registry_ready": self._engine_registry is not None
        }

    def get_engine(self, name: str):
        if self._engine_registry:
            return self._engine_registry.get_engine(name)
        return None

    def list_engines(self) -> List[str]:
        if self._engine_registry:
            return list(self._engine_registry.list_engines())
        return []
