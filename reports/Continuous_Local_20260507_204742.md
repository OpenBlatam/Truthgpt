TruthGPT ha sido mejorado con la técnica **APASI (Autonomous Preference Alignment via Self-Injection)**, basada en el paper 'Mitigating Hallucinations in Large Vision-Language Models by Self-Injecting Hallucinations' (arXiv:2509.11287, Lu et al., 2025). Se ha creado el archivo `/workspace/truthgpt_self_injecting.py` con las funciones `mitigate_hallucination` y `detect_hallucination`. La técnica utiliza el propio modelo para auto-inyectar alucinaciones en una respuesta generada, creando pares de preferencia que luego se usan para alinear el modelo sin necesidad de anotaciones externas. 

**Estado actual:** TruthGPT ahora cuenta con **19 técnicas SOTA** de mitigación de alucinaciones (las 18 anteriores más Self-Injecting Hallucinations). 

**Pendiente:** La entrada en el `TECHNIQUE_REGISTRY` de `/workspace/truthgpt_unified.py` no pudo ser actualizada automáticamente debido a errores en las herramientas de lectura/escritura. Para integrar completamente la técnica, añada manualmente la siguiente entrada al diccionario `TECHNIQUE_REGISTRY`:

```python
'self_injecting': {
    'name': 'APASI (Autonomous Preference Alignment via Self-Injection)',
    'paper': 'arXiv:2509.11287',
    'module': 'truthgpt_self_injecting',
    'func': 'mitigate_hallucination',
    'description': 'Mitigates hallucinations by self-injecting hallucinated patterns and using contrastive preference alignment without external supervision.'
}
```

Para usar la técnica: `agent.mitigate(technique='self_injecting', prompt=..., response=..., llm_callable=...)`. 

**Fuente verificable:** [arXiv:2509.11287](https://arxiv.org/abs/2509.11287)