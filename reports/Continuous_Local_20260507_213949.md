## Mejoras recomendadas para TruthGPT basadas en trazas empíricas

### 1. Ajuste de hiperparámetros (basado en arXiv:2309.03883, arXiv:2203.11171, arXiv:2403.07691, arXiv:2508.03553)
- **DoLA (arXiv:2309.03883):** Reducir el umbral de detección de 0.5 a **0.35** (trace #12 con DoLA solo tuvo score 0.25, lo que indica necesidad de activación más temprana).
- **Self-Consistency (arXiv:2203.11171):** Aumentar k de 5 a **7** (trace #13 con SelfConsistency solo tuvo score 0.18; con k más alto se espera menor varianza).
- **ORPO (arXiv:2403.07691):** Incrementar β de 0.1 a **0.15** para mayor penalización de respuestas alucinadas.
- **MultiRAG (arXiv:2508.03553):** Ponderar fuentes como **0.4/0.3/0.2/0.1** (fuentes principales con más peso).

### 2. Selección dinámica de técnicas según tipo de prompt
- **Consultas factuales simples** (ej. capitales, fechas): Usar **ContrastiveDecoding + SemanticEntropy** (trace #14 score 0.01).
- **Explicaciones complejas** (ej. relatividad, agujeros negros): Usar **SelfRAG + Chain-of-Verification** (trace #15 score 0.09).
- **Preguntas abiertas** (ej. beneficios meditación): Usar **DoLA + SelfConsistency** (trace #6 score 0.05).

### 3. Integrar detector ligero de alucinaciones (arXiv:2506.22486 – Hallucination Detection with Small Language Models)
Añadir un módulo `/workspace/truthgpt_small_lm_detection.py` que preclasifique respuestas como probables alucinaciones antes de aplicar técnicas correctivas, reduciendo costo computacional. Este detector puede activarse solo cuando el hallucination_score supere 0.1.

### 4. Automatizar análisis periódico
Ejecutar `python /workspace/analyze_traces.py` cada 100 trazas para recalibrar umbrales dinámicamente.

**Próximo paso:** Proceder con la implementación del detector ligero (arXiv:2506.22486) y la actualización de hiperparámetros en el kernel. ¿Deseas que genere el nuevo módulo ahora?