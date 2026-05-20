Para mejorar TruthGPT, te recomiendo implementar las siguientes técnicas SOTA basadas en investigaciones recientes (2025-2026):

1. **Detección de alucinaciones basada en distancias probabilísticas** (arXiv:2506.09886): Este método mide la distancia entre las distribuciones de embeddings del prompt y de la respuesta del LLM para detectar alucinaciones de forma no supervisada y eficiente. Es especialmente útil en sistemas RAG.

2. **Mitigación conjunta de alucinaciones factuales y de fidelidad con SPACE** (arXiv:2506.11088): Un enfoque unificado que aborda tanto alucinaciones factuales (inconsistencias con el mundo real) como de fidelidad (desviaciones del contexto). Utiliza un marco de entrenamiento conjunto para reducir ambos tipos.

3. **REFIND: Detección de alucinaciones factuales con RAG** (arXiv:2502.13622): Un sistema de recuperación aumentada que verifica la factualidad de las respuestas comparándolas con documentos relevantes. Logra resultados SOTA en tareas de QA.

4. **Teaming LLMs para detectar y mitigar alucinaciones** (arXiv:2510.19507): Consiste en agregar múltiples respuestas de un mismo LLM (o de varios) y usar un clasificador de consistencia para identificar y corregir alucinaciones. Es simple y efectivo.

5. **Mitigación de alucinaciones mediante optimización de preferencias enfocada en alucinaciones** (arXiv:2501.17295): Adaptado para traducción automática, pero aplicable a otros dominios. Usa reinforcement learning con preferencias para penalizar respuestas alucinadas.

**Recomendación de implementación**: Integra un pipeline que combine (1) detección con distancias probabilísticas en tiempo real, (2) verificación RAG con REFIND para respuestas factuales, y (3) entrenamiento de fine-tuning con SPACE o preferencias para reducir alucinaciones de forma proactiva. Además, considera usar el enfoque de teaming para mejorar la robustez en producción.

Todas las técnicas están validadas con benchmarks y provienen de arXiv. Puedes profundizar en cada una a través de los enlaces proporcionados.