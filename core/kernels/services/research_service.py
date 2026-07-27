"""
ResearchService - Papers, research, and knowledge management
"""

import asyncio
from typing import Dict, Any, Optional, List
from .base_service import BaseService


class ResearchService(BaseService):
    """Service for managing research papers and knowledge base"""

    def __init__(self, kernel, config: Optional[Dict[str, Any]] = None):
        super().__init__(kernel, config)
        self._paper_registry = None
        self._paper_count = 0

    async def _on_start(self) -> None:
        try:
            from optimization_core.modules.base.core_system.core.papers.paper_registry import get_paper_registry
            loop = asyncio.get_event_loop()
            self._paper_registry = await loop.run_in_executor(
                None,
                lambda: get_paper_registry(preload_popular=False)
            )
            self._paper_count = len(self._paper_registry.list_papers())
            self.logger.info(f"ResearchService: {self._paper_count} papers loaded")
        except Exception as e:
            self.logger.warning(f"ResearchService partial init: {e}")

    async def _on_stop(self) -> None:
        self._paper_registry = None
        self._paper_count = 0

    async def _get_health_info(self) -> Dict[str, Any]:
        return {
            "paper_count": self._paper_count,
            "registry_ready": self._paper_registry is not None
        }

    def list_papers(self) -> List[Any]:
        if self._paper_registry:
            return self._paper_registry.list_papers()
        return []

    def search_papers(self, query: str) -> List[Any]:
        if self._paper_registry:
            return self._paper_registry.search(query)
        return []
