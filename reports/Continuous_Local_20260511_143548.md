He mejorado TruthGPT. El nuevo archivo es `/workspace/truthgpt_unified_v3.py`. Las mejoras incluyen:

1. **TTL Cache robusto**: Reemplacé el `lru_cache` con TTL manual por una clase `TTLCache` usando `OrderedDict`, con expiración por tiempo (300s) y evicción LRU verdadera.
2. **Ejecución asíncrona**: `run_technique_async` verifica si el módulo expone `run_async` o `run`. Si es síncrono, lo ejecuta en un thread pool para no bloquear el event loop.
3. **Caching correcto**: Se calcula un hash de la configuración para claves únicas, evitando colisiones. Se usa un caché global compartido.
4. **Memory Manager**: Usa `deque` para ventana deslizante, con evicción correcta de tokens.
5. **Manejo de errores**: Las técnicas que fallen no interrumpen el pipeline; se registran y retornan `None`.
6. **Auto-descubrimiento**: Se escanea el workspace en busca de módulos `truthgpt_*.py` y se importan directamente.

Puedes probar el pipeline con `python truthgpt_unified_v3.py`.