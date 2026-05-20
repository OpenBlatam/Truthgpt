TruthGPT ha sido mejorado con una nueva técnica SOTA:

- **Attention-guided Self-reflection (AGSER)** (arXiv:2501.09997, 2025) – Detección y mitigación de alucinaciones en zero-shot mediante guía de atención y autorreflexión. Archivo creado: `/workspace/truthgpt_agser.py`.

Para integrarlo completamente, debes añadir la entrada `'agser'` al TECHNIQUE_REGISTRY en `/workspace/truthgpt_unified.py` apuntando al módulo `truthgpt_agser` y a la función `mitigate_hallucination`. Luego podrás usarlo con: `agent.mitigate(technique='agser', prompt=..., response=...)`.