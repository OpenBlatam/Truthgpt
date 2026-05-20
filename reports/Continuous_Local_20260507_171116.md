He obtenido nuevas técnicas SOTA (2025-2026) para mejorar TruthGPT. Las incorporo a la guía existente:

**Nuevos hallazgos:**
- **Efficient Hallucination Detection via Adaptive Bayesian Estimation of Semantic Entropy** (arXiv:2603.22812v1, 2026): Estima la entropía semántica de manera adaptativa para detectar alucinaciones con menor coste computacional que métodos previos.
- **Steer LLM Latents for Hallucination Detection** (arXiv:2503.01917v2, 2025): Interviene en el espacio latente del LLM para detectar y corregir alucinaciones durante la generación.
- **Context and Prompt Optimization for Automated Hallucination Detection** (arXiv:2505.03030v1, 2025): Optimiza el contexto y los prompts para mejorar la detección de alucinaciones en modelos multilingües.

**Técnicas previamente documentadas (reconfirmadas):**
1. Detección por distancia probabilística (arXiv:2506.09886)
2. SPACE para mitigación conjunta (arXiv:2506.11088)
3. REFIND para verificación RAG (arXiv:2502.13622)
4. Teaming de LLMs para consistencia (arXiv:2510.19507)
5. Optimización de preferencias con RL (arXiv:2501.17295)

**Recomendación de implementación:** Combinar (1) detección adaptativa de entropía semántica, (2) intervención en latentes, y (3) verificación RAG con REFIND como pipeline principal. La guía completa se actualizará en `truthgpt_improvement_guide.md` con estos nuevos papers. ¿Deseas que profundice en la implementación de alguna de estas técnicas?