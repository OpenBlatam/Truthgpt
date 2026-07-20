from loguru import logger
import asyncio

async def setup():
    """Llamado automáticamente cuando el Kernel 2.0 carga el plugin."""
    logger.info("DemoPlugin: Inicialización asíncrona completada.")
    logger.info("DemoPlugin: Integrado con el Event Bus y listo para recibir tareas.")

async def teardown():
    """Llamado cuando el plugin es descargado (Hot-Reloading/Apagado)."""
    logger.info("DemoPlugin: Liberando recursos asíncronamente...")

def execute_custom_logic():
    """Lógica expuesta por el plugin."""
    return "Hello from Demo Plugin V1!"
