Se ha refactorizado TruthGPT creando un módulo unificado en `/workspace/truthgpt_unified.py` que proporciona una interfaz consistente para las 50 técnicas de mitigación de alucinaciones. El archivo importa dinámicamente cada técnica y expone las funciones `list_techniques()` y `detect_hallucination(technique, **kwargs)`. El código del módulo es:

```python
""" TruthGPT Unified Module
Provides a single interface to all 50 hallucination mitigation techniques.
Each technique can be called via `detect_hallucination(technique_name, **kwargs)`.
"""
import importlib
import inspect
import os
import sys

sys.path.insert(0, '/workspace')

TECHNIQUE_REGISTRY = {
    'prob_dist': {'module': 'truthgpt_prob_dist', 'func': 'detect_hallucination'},
    'consistency_teaming': {'module': 'truthgpt_consistency_teaming', 'func': 'detect_hallucination'},
    'refind_rag': {'module': 'truthgpt_refind_rag', 'func': 'detect_hallucination'},
    'fs_rag': {'module': 'truthgpt_fs_rag', 'func': 'detect_hallucination'},
    'selfcheckgpt': {'module': 'truthgpt_selfcheck', 'func': 'detect_hallucination'},
    'nli': {'module': 'truthgpt_nli', 'func': 'detect_hallucination'},
    'ensemble': {'module': 'truthgpt_ensemble', 'func': 'detect_hallucination'},
    'slm_ensemble': {'module': 'truthgpt_slm_ensemble', 'func': 'detect_hallucination'},
    'abese': {'module': 'truthgpt_abese', 'func': 'detect_hallucination'},
    'ucsc_semeval': {'module': 'truthgpt_ucsc_semeval', 'func': 'detect_hallucination'},
    'simpletext': {'module': 'truthgpt_simpletext_ensemble', 'func': 'detect_hallucination'},
    'grapheval': {'module': 'truthgpt_grapheval', 'func': 'detect_hallucination'},
    'tum_mikani': {'module': 'truthgpt_tum_mikani', 'func': 'detect_hallucination'},
    'confactcheck': {'module': 'truthgpt_confactcheck', 'func': 'detect_hallucination'},
    'atlantis': {'module': 'truthgpt_atlantis', 'func': 'detect_hallucination'},
    'mdok_kinit': {'module': 'truthgpt_mdok_kinit', 'func': 'detect_hallucination'},
    'tpa': {'module': 'truthgpt_tpa', 'func': 'detect_hallucination'},
    'thames': {'module': 'truthgpt_thames', 'func': 'detect_hallucination'},
    'eclipse': {'module': 'truthgpt_eclipse', 'func': 'detect_hallucination'},
    'selfrag': {'module': 'truthgpt_selfrag', 'func': 'detect_hallucination'},
    'factscore': {'module': 'truthgpt_factscore', 'func': 'detect_hallucination'},
    'dola': {'module': 'truthgpt_dola', 'func': 'dola_decode'},
    'cove': {'module': 'truthgpt_cove', 'func': 'detect_hallucination'},
    'alignscore': {'module': 'truthgpt_alignscore', 'func': 'detect_hallucination'},
    'rarr': {'module': 'truthgpt_rarr', 'func': 'detect_hallucination'},
    'dehallucinator': {'module': 'truthgpt_dehallucinator', 'func': 'detect_hallucination'},
    'self_refine': {'module': 'truthgpt_self_refine', 'func': 'detect_hallucination'},
    'contrastive_decoding': {'module': 'truthgpt_contrastive_decoding', 'func': 'detect_hallucination'},
    'rtuning': {'module': 'truthgpt_rtuning', 'func': 'detect_hallucination'},
    'iti': {'module': 'truthgpt_iti', 'func': 'detect_hallucination'},
    'dpo': {'module': 'truthgpt_dpo', 'func': 'detect_hallucination'},
    'repe': {'module': 'truthgpt_repe', 'func': 'detect_hallucination'},
    'cai': {'module': 'truthgpt_cai', 'func': 'detect_hallucination'},
    'simpo': {'module': 'truthgpt_simpo', 'func': 'detect_hallucination'},
    'orpo': {'module': 'truthgpt_orpo', 'func': 'detect_hallucination'},
    'spin': {'module': 'truthgpt_spin', 'func': 'detect_hallucination'},
    'kto': {'module': 'truthgpt_kto', 'func': 'detect_hallucination'},
    'ppo': {'module': 'truthgpt_ppo', 'func': 'detect_hallucination'},
    'grpo': {'module': 'truthgpt_grpo', 'func': 'detect_hallucination'},
    'cad': {'module': 'truthgpt_cad', 'func': 'detect_hallucination'},
    'self_consistency': {'module': 'truthgpt_self_consistency', 'func': 'detect_hallucination'},
    'reflexion': {'module': 'truthgpt_reflexion', 'func': 'detect_hallucination'},
    'flare': {'module': 'truthgpt_flare', 'func': 'detect_hallucination'},
    'conformal': {'module': 'truthgpt_conformal', 'func': 'detect_hallucination'},
    'crag': {'module': 'truthgpt_crag', 'func': 'detect_hallucination'},
    'factoid': {'module': 'truthgpt_factoid', 'func': 'detect_hallucination'},
    'sppo': {'module': 'truthgpt_sppo', 'func': 'detect_hallucination'},
    'rest': {'module': 'truthgpt_rest', 'func': 'detect_hallucination'},
    'mad': {'module': 'truthgpt_mad', 'func': 'detect_hallucination'},
    'tot': {'module': 'truthgpt_tot', 'func': 'detect_hallucination'},
}

def list_techniques():
    return list(TECHNIQUE_REGISTRY.keys())

def detect_hallucination(technique: str, **kwargs):
    if technique not in TECHNIQUE_REGISTRY:
        raise ValueError(f"Unknown technique: {technique}. Available: {list_techniques()}")
    entry = TECHNIQUE_REGISTRY[technique]
    try:
        module = importlib.import_module(entry['module'])
    except ModuleNotFoundError:
        raise ImportError(f"Module {entry['module']} not found.")
    func = getattr(module, entry['func'], None)
    if func is None:
        raise AttributeError(f"Function {entry['func']} not found.")
    if technique == 'dola':
        return dola_detect_wrapper(module, **kwargs)
    sig = inspect.signature(func)
    if 'self' in sig.parameters:
        class_name = entry['func'].replace('detect_hallucination', '').strip('_')
        if class_name:
            cls = getattr(module, class_name, None)
            if cls:
                instance = cls(**{k: v for k,v in kwargs.items() if k in sig.parameters})
                return instance.detect_hallucination(**kwargs)
    return func(**kwargs)

def dola_detect_wrapper(module, **kwargs):
    import torch
    model = kwargs.get('model')
    input_ids = kwargs.get('input_ids')
    if model is None or input_ids is None:
        raise ValueError("DOLA requires 'model' and 'input_ids'.")
    max_new_tokens = kwargs.get('max_new_tokens', 50)
    return module.dola_decode(model, input_ids, max_new_tokens=max_new_tokens)

if __name__ == '__main__':
    print("TruthGPT Unified Module loaded.")
    print(f"Available techniques: {len(list_techniques())}")
```

El archivo se ha guardado en `/workspace/truthgpt_unified.py`. Ahora todas las técnicas se pueden invocar con un solo punto de entrada, manteniendo la compatibilidad hacia atrás con los archivos individuales.