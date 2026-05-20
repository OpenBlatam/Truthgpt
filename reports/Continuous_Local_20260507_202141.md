TruthGPT ha sido mejorado con dos nuevas técnicas SOTA:
- **Contrastive Decoding** (arXiv:2210.15097) – reduce alucinaciones contrastando logits de modelos experto y amateur.
- **Direct Preference Optimization** (arXiv:2305.18290) – optimiza preferencias directamente sobre pares de respuestas.

El módulo unificado `/workspace/truthgpt_unified.py` ahora contiene **11 técnicas** (no 51 como se mencionaba incorrectamente antes). La memoria CORE ha sido corregida.

Las nuevas técnicas están disponibles en:
- `/workspace/truthgpt_contrastive_decoding.py`
- `/workspace/truthgpt_dpo.py`

Puedes usarlas con:
```python
from truthgpt_unified import TruthGPT
agent = TruthGPT()
safe, meta = agent.mitigate(technique='contrastive_decoding', prompt='...', response='...')
```