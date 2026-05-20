He mejorado el código de TruthGPT. Los cambios principales son:

1. **Eliminación de patrones wrapper**: Se reemplazó la clase `TimedLRUCache` por `functools.lru_cache` con un diccionario separado para control de TTL (time-to-live). La clase `MemoryManager` se simplificó usando `collections.deque`, lo que evita errores de evicción y es más eficiente.
2. **Corrección de bug en evicción de memoria**: En la versión original, `total_tokens` no se actualizaba correctamente al eliminar entradas; ahora se decrementa apropiadamente.
3. **Descubrimiento automático de módulos**: El código ahora escanea el directorio en busca de módulos `truthgpt_*.py`, eliminando el mapeo manual y facilitando la adición de nuevas técnicas.
4. **Carga directa de módulos**: Se eliminó la carga diferida (lazy loading) para mayor claridad y rendimiento.
5. **Pipeline asíncrono**: Se agregó una función `truthgpt_pipeline` que ejecuta técnicas en paralelo usando `asyncio.create_task`.
6. **Caché con TTL**: Se implementó un mecanismo de expiración por tiempo usando timestamps, manteniendo la simplicidad del LRU cache.

El archivo mejorado se ha guardado como `/workspace/truthgpt_unified_v2.py`. Puedes revisarlo y ejecutarlo. Si deseas más ajustes, indícalo.