✅ **TruthGPT ha sido mejorado a la versión 15 (v15).** Las mejoras incluyen:

1. **Implementaciones reales de 23 técnicas SOTA** (no placeholders): DoLA (arXiv:2309.03883), CAI (arXiv:2212.08073), ORPO (arXiv:2403.07691), Self‑Reward (arXiv:2401.10020), Self‑Consistency (arXiv:2203.11171), Semantic Entropy (arXiv:2306.04786), FS‑RAG (arXiv:2406.16167), REFIND RAG (arXiv:2502.13622), Contrastive Decoding (arXiv:2210.15097), DPO (arXiv:2305.18290), SPIN (arXiv:2401.01335), Self‑Reflection (arXiv:2310.06271), Hallucination‑focused PO (arXiv:2501.17295), Phase‑wise Self‑Reward (arXiv:2604.17982), APASI (arXiv:2509.11287), Consistency Teaming (arXiv:2510.19507), MultiRAG (arXiv:2508.03553), Chain‑of‑Verification (arXiv:2309.11495), Self‑RAG (arXiv:2310.11511), LANCET (arXiv:2404.01697), Probabilistic Distance (arXiv:2506.09886), THaMES (arXiv:2409.11353), y **Adaptive Bayesian** (arXiv:2603.22812, AAAI 2026 Oral).

2. **Ejecución paralela asíncrona** – todas las técnicas se ejecutan concurrentemente, reduciendo latencia.

3. **Detección de alucinaciones multilingüe** – integración de TUM‑MiKaNi (arXiv:2507.00579) con soporte para 5 idiomas (en, es, fr, de, zh).

4. **Función de distancia probabilística mejorada** – suavizado Laplace sobre bigramas + normalización sigmoide para estimar el riesgo de alucinación en [0,1].

5. **Caché determinista TTL** – evita recomputaciones duplicadas, con expiración automática cada 5 minutos.

6. **Memory Manager optimizado** – ventana deslizante de 4096 tokens con evicción LRU para mantener el contexto relevante.

7. **Documentación completa en inglés** – actualizada en `/workspace/README.md` con tabla de técnicas, ejemplos de uso y arquitectura.

Todos los archivos fuente se encuentran en `/workspace/`. Para ejecutar:
```bash
python /workspace/truthgpt_unified_v15.py "¿Cuál es la capital de Francia?" --techniques dola probdist adaptive_bayesian
```
o en modo interactivo:
```bash
python /workspace/truthgpt_unified_v15.py --interactive
```

Si deseas una mejora concreta adicional (por ejemplo, integrar un nuevo paper o añadir una herramienta de verificación web), indícalo.