He implementado dos técnicas SOTA de detección de alucinaciones:

1. **Distancias probabilísticas** (arXiv:2506.09886) — analiza la distribución de probabilidades del modelo para identificar posibles alucinaciones. Archivo: `/workspace/truthgpt_prob_dist.py`.
2. **Consistency Teaming** (arXiv:2510.19507) — utiliza múltiples muestras con variación de temperatura para medir la consistencia de las respuestas. Archivo: `/workspace/truthgpt_consistency_teaming.py`.

Ambos detectores están listos para ser integrados en TruthGPT. ¿Deseas implementar alguna otra técnica (de las 12 disponibles) o prefieres explorar un dominio concreto (medicina, derecho, finanzas, etc.) para buscar adaptaciones especializadas?