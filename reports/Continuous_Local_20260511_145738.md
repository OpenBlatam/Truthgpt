He mejorado TruthGPT a la versión 12 (v12) en `/workspace/truthgpt_unified_v12.py`. Las mejoras incluyen:

1. **Funciones completas** – Todas las implementaciones truncadas fueron completadas (probabilistic distance, refind, chain-of-verification, small LM detection, self-rag, dpo rerank, self-consistency, semantic entropy, THaMES).
2. **Nueva técnica: Adaptive Bayesian Semantic Entropy** (arXiv:2603.22812) – Ajusta dinámicamente las muestras según la incertidumbre, reduciendo coste computacional y mejorando el AUROC.
3. **Caché determinista MD5** – Evita resultados no deterministas.
4. **Memory Manager con ventana deslizante** – Gestión eficiente del contexto.
5. **Manejo robusto de errores** – Degradación gradual y registro.
6. **CLI interactiva mejorada** – Soporta `--interactive`, `--techniques`, y `--config`.
7. **Pipeline completo** – Ejecuta todas las técnicas en secuencia con verificación final de distancia probabilística.

Ejecuta con: `python /workspace/truthgpt_unified_v12.py "tu prompt" --techniques probdist adaptive_bayesian refind conv small_lm selfrag dpo self_consistency semantic_entropy thames`

¿Deseas que añada alguna mejora adicional?