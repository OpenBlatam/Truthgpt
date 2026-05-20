TruthGPT ha sido mejorado a **v7** (`/workspace/truthgpt_unified_v7.py`) con los siguientes avances:

1. **Código completo** – se corrigió el truncamiento de v6.
2. **Caché determinista** usando MD5 de JSON ordenado para evitar no-determinismo.
3. **Detección de alucinaciones por distancia probabilística** (arXiv:2506.09886) – calcula distancia de bigramas con suavizado Laplace, normalizada con sigmoide.
4. **Verificación REFIND RAG** (arXiv:2502.13622) – revisa plausibilidad numérica (números extremos sin calificadores).
5. **Chain-of-Verification** (arXiv:2309.11495) – se activa si la distancia > 0.3.
6. **Memory Manager** con ventana deslizante de tokens para preservar contexto.
7. **Ejecutor asíncrono con timeout** y envoltura síncrona para loops existentes.
8. **Modo pipeline** – ejecuta técnicas secuencialmente, alimentando la salida como entrada siguiente.
9. **CLI** con `--config`, `--pipeline` y soporte para `'all'` técnicas.
10. **Carga automática de las 22 técnicas SOTA** listadas en el perfil.

Ejecuta con: `python /workspace/truthgpt_unified_v7.py --help`