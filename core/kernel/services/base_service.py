import abc
import asyncio
from typing import Optional
from loguru import logger

class BaseService(abc.ABC):
    """
    Contrato base para los servicios del SO del Kernel (AIOS-style).
    Define el ciclo de vida: inicialización, ejecución y terminación.
    """
    def __init__(self, name: str):
        self.name = name
        self.is_running = False

    async def start(self):
        """Inicializa recursos del servicio."""
        logger.info(f"[{self.name}] Booting service...")
        self.is_running = True
        await self._on_start()
        logger.info(f"[{self.name}] Service is online.")

    async def stop(self):
        """Apaga el servicio de forma segura (graceful shutdown)."""
        logger.info(f"[{self.name}] Shutting down service...")
        self.is_running = False
        await self._on_stop()
        logger.info(f"[{self.name}] Service terminated.")

    @abc.abstractmethod
    async def _on_start(self):
        pass

    @abc.abstractmethod
    async def _on_stop(self):
        pass

    def check_health(self) -> bool:
        """Verifica si el servicio interno está operativo."""
        return self.is_running
