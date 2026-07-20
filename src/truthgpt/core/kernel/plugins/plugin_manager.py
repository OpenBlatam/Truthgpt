import os
import importlib
import asyncio
from pathlib import Path
from typing import Dict, Any
from loguru import logger

class PluginManager:
    """
    Sistema de Plugins (Hot-Reloadable).
    Permite cargar, descargar y recargar módulos en caliente sin reiniciar el Kernel 2.0.
    """
    def __init__(self, plugins_dir: str = "plugins"):
        # El directorio estará en la raíz de optimization_core/plugins
        self.plugins_dir = Path(__file__).resolve().parent.parent.parent.parent / plugins_dir
        self.active_plugins: Dict[str, Any] = {}
        
        # Crear directorio si no existe
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)

    async def load_plugins(self):
        """Escanea el directorio de plugins y carga los disponibles."""
        logger.info(f"[PluginManager] Scanning for plugins in {self.plugins_dir}...")
        
        if not self.plugins_dir.exists():
            return
            
        for item in self.plugins_dir.glob("*.py"):
            if item.name.startswith("__"):
                continue
            
            plugin_name = item.stem
            await self.load_plugin(plugin_name)

    async def load_plugin(self, plugin_name: str) -> bool:
        """Carga un plugin dinámicamente."""
        try:
            # Importar de manera dinámica
            module_path = f"plugins.{plugin_name}"
            
            if plugin_name in self.active_plugins:
                logger.info(f"[PluginManager] Hot-Reloading plugin: {plugin_name}")
                # Si ya está cargado, lo recargamos (Hot-Reload)
                module = importlib.reload(self.active_plugins[plugin_name])
            else:
                logger.info(f"[PluginManager] Loading plugin: {plugin_name}")
                module = importlib.import_module(module_path)
                
            self.active_plugins[plugin_name] = module
            
            # Si el plugin tiene una función setup() asíncrona, ejecutarla
            if hasattr(module, 'setup'):
                if asyncio.iscoroutinefunction(module.setup):
                    await module.setup()
                else:
                    module.setup()
                    
            logger.info(f"[PluginManager] ✅ Plugin '{plugin_name}' activated.")
            return True
        except Exception as e:
            logger.error(f"[PluginManager] ❌ Failed to load plugin '{plugin_name}': {e}")
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """Descarga un plugin y libera sus recursos."""
        if plugin_name in self.active_plugins:
            module = self.active_plugins[plugin_name]
            
            # Ejecutar teardown() si existe
            if hasattr(module, 'teardown'):
                try:
                    if asyncio.iscoroutinefunction(module.teardown):
                        await module.teardown()
                    else:
                        module.teardown()
                except Exception as e:
                    logger.error(f"[PluginManager] Error during teardown of '{plugin_name}': {e}")
                    
            del self.active_plugins[plugin_name]
            logger.info(f"[PluginManager] Plugin '{plugin_name}' unloaded.")
            return True
        return False
