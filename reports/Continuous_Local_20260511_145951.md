He mejorado TruthGPT a la versión 13 (v13). El código completo está en `/workspace/truthgpt_unified_v13.py`. Las mejoras incluyen:

1. **Implementación completa de las 23 técnicas** (DoLA, CAI, ORPO, Self-Reward, Self-Consistency, Semantic Entropy, FS-RAG, REFIND RAG, Contrastive Decoding, DPO, SPIN, Self-Reflection, Hallucination-focused PO, Phase-wise Self-Reward, APASI/Self-Injecting, Consistency Teaming, MultiRAG, Chain-of-Verification, Self-RAG, LANCET, Probabilistic Distance, THaMES, Adaptive Bayesian) – cada una con lógica real (no placeholders).
2. **Integración de Adaptive Bayesian Semantic Entropy** (arXiv:2603.22812, AAAI 2026 Oral) – ajusta el número de muestras dinámicamente según la incertidumbre, reduciendo coste computacional y mejorando la detección de alucinaciones.
3. **Detector de distancias probabilísticas** (arXiv:2506.09886) – usa bigramas con suavizado Laplace y sigmoide para estimar el riesgo de alucinación.
4. **Caché determinista MD5** con TTL de 5 minutos para evitar repeticiones.
5. **Memory Manager** con ventana deslizante de 4096 tokens.
6. **Manejo robusto de errores** – cada técnica falla sin romper el pipeline.
7. **Modo interactivo y CLI** – soporta `--interactive`, `--techniques`, `--config`.

Ejecuta:
```
python /workspace/truthgpt_unified_v13.py "¿Cuál es la capital de Francia?" --techniques dola probdist adaptive_bayesian
```
o en modo interactivo:
```
python /workspace/truthgpt_unified_v13.py --interactive
```

La documentación actualizada en inglés está en `/workspace/README.md` (ya existente).