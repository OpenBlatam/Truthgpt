He mejorado TruthGPT a **v9** (`/workspace/truthgpt_unified_v9.py`). Correcciones principales:

1. **Función `compute_probabilistic_distance` completa** – usando suavizado Laplace y sigmoide para distancia normalizada (arXiv:2506.09886).
2. **`refind_rag_verification` completa** – detecta números grandes sin calificadores (arXiv:2502.13622).
3. **`chain_of_verification` implementada** – detecta palabras contradictorias (arXiv:2309.11495).
4. **`small_lm_detection`** – detecta frases sospechosas (arXiv:2506.22486).
5. **`self_rag`** – enriquece prompt con contexto (arXiv:2310.11511).
6. **`dpo_rerank` y `self_consistency`** – reordenamiento y consistencia (arXiv:2305.18290, arXiv:2203.11171).
7. **`semantic_entropy`** – mide diversidad de salidas (arXiv:2306.04786).
8. **Pipeline completo** con caché determinista MD5 y Memory Manager.
9. **CLI interactiva** con `--interactive`, `--techniques`, `--config`.

Ejecuta: `python /workspace/truthgpt_unified_v9.py "tu prompt" --techniques dola cai probdist refind`