Basado en investigaciones de 2025-2026, las técnicas SOTA para mejorar la veracidad y reducir alucinaciones en TruthGPT son:

1. **Detección de alucinaciones por distancia probabilística** (arXiv:2506.09886): Mide la distancia entre distribuciones de embeddings del prompt y la respuesta para detectar alucinaciones en tiempo real, sin supervisión.

2. **SPACE** (arXiv:2506.11088): Mitigación conjunta de alucinaciones factuales y de fidelidad mediante entrenamiento unificado.

3. **REFIND** (arXiv:2502.13622): Sistema RAG que verifica la factualidad de respuestas comparándolas con documentos relevantes; logra SOTA en QA.

4. **Teaming de LLMs** (arXiv:2510.19507): Agregar múltiples respuestas del mismo LLM y usar un clasificador de consistencia para detectar y corregir alucinaciones.

5. **Optimización de preferencias enfocada en alucinaciones** (arXiv:2501.17295): Uso de RL con preferencias para penalizar respuestas no factuales, adaptable a diversos dominios.

Además, se recomienda combinar estos enfoques: pipeline de detección probabilística + verificación RAG con REFIND + fine-tuning con SPACE/RL para reducción proactiva. Las fuentes están verificadas en arXiv.