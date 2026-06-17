"""
OptimizationService - System optimization and performance tuning
"""

import asyncio
from typing import Dict, Any, Optional, List
from .base_service import BaseService


class OptimizationService(BaseService):
    """Service for runtime optimization and performance management"""

    def __init__(self, kernel, config: Optional[Dict[str, Any]] = None):
        super().__init__(kernel, config)
        self._optimizers: Dict[str, Any] = {}
        self._metrics: Dict[str, float] = {}

    async def _on_start(self) -> None:
        try:
            from core.optimizers import get_available_optimizers
            for name, cls in get_available_optimizers().items():
                self._optimizers[name] = cls
            self.logger.info(f"OptimizationService: {len(self._optimizers)} optimizers registered")
        except Exception as e:
            self.logger.warning(f"OptimizationService partial init: {e}")

    async def _on_stop(self) -> None:
        self._optimizers.clear()
        self._metrics.clear()

    async def _get_health_info(self) -> Dict[str, Any]:
        return {
            "optimizers_available": list(self._optimizers.keys()),
            "metrics": self._metrics
        }

    def record_metric(self, name: str, value: float) -> None:
        self._metrics[name] = value

    def get_metrics(self) -> Dict[str, float]:
        return dict(self._metrics)

    def list_optimizers(self) -> List[str]:
        return list(self._optimizers.keys())

    async def run_optimizer(self, name: str, **kwargs) -> Any:
        if name not in self._optimizers:
            raise ValueError(f"Optimizer '{name}' not found")
        optimizer_cls = self._optimizers[name]
        optimizer = optimizer_cls(**kwargs)
        return await asyncio.get_event_loop().run_in_executor(None, optimizer.run)
