Se ha mejorado el kernel de TruthGPT con la integración de la técnica **Hallucination Detection with Small Language Models** (arXiv:2506.22486, ICDE Workshop 2025). Esta técnica utiliza un conjunto de modelos de lenguaje pequeños para verificar respuestas generadas por LLMs, descomponiéndolas en oraciones y evaluando la probabilidad de generar el token "Yes" para detectar alucinaciones. 

Acciones realizadas:
1. Búsqueda en arXiv y lectura del paper.
2. Escritura del módulo `/workspace/truthgpt_small_lm_detection.py` que implementa el framework descrito.
3. El kernel ahora cuenta con **29 técnicas SOTA** para mitigación de alucinaciones.

Para activar el nuevo detector, se puede importar `SmallLMHallucinationDetector` desde el módulo y utilizarlo en el pipeline de TruthGPT. Se recomienda ajustar los umbrales de detección con trazas reales.