He mejorado TruthGPT a v8 (guardado en `/workspace/truthgpt_unified_v8.py`). Las mejoras incluyen:

1. **Corrección de errores sintácticos** – La función `compute_probabilistic_distance` ahora tiene la sintaxis correcta (falta un `:` en v7).
2. **Implementación completa de detección de alucinaciones** – Distancia probabilística con bigramas y suavizado Laplace (arXiv:2506.09886).
3. **Verificación REFIND RAG** – Revisión de plausibilidad numérica (arXiv:2502.13622).
4. **Pipeline funcional** – Ejecuta técnicas secuencialmente con paso de contexto y memoria opcional.
5. **Caché determinista** – Usa MD5 de JSON ordenado (sort_keys=True) para evitar no-determinismo.
6. **Memory Manager** – Ventana deslizante de tokens para preservar contexto.
7. **CLI robusta** – Soporta `--interactive`, `--config`, `--pipeline`, y selección de técnicas.
8. **Manejo de errores** – Captura timeouts, fallos de módulos, y registra logs.

Ejecuta con: `python /workspace/truthgpt_unified_v8.py --help`