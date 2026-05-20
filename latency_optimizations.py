# latency_optimizations.py
# Path: optimization_core/latency_optimizations.py

from papers.chain_of_draft import ChainOfDraft
from papers.elastic_reasoning import ElasticReasoning
from papers.fp16_stability import FP16Stability
import torch

def apply_chain_of_draft(prompt: str, variant: str = "baseline") -> str:
    """Prepend Chain of Draft template to prompt."""
    template = ChainOfDraft.get_template(variant)
    return template + "\n" + prompt

def apply_elastic_reasoning(prompt: str, t_budget: int, s_budget: int, wrapper: bool = True) -> str:
    """Wrap prompt with think tags if desired, otherwise just pass budgets to model? For API we can't directly enforce budget, but we can prefix instructions."""
    elastic = ElasticReasoning(t_budget, s_budget)
    if wrapper:
        # We'll prepend an instruction to think within budget, but the actual enforcement would need LLM cooperation.
        # We'll rely on the paper's algorithm to be implemented in generation loop if possible.
        # For now, just add instruction.
        return f"Please think within {t_budget} tokens using <think></think> tags, then answer within {s_budget} tokens:\n\n" + prompt
    return prompt

def apply_fp16_stability(model):
    """Configure model for FP16 stability (if applicable). Returns wrapper or hooks."""
    # For transformers models, we can convert to half and then run inference. But we need to be careful.
    # This function checks if model is compatible, converts to half, and returns a function to run with stability.
    # Simple approach: model.half() and then call model.infer.
    try:
        if hasattr(model, 'half'):
            model.half()
            print("Model converted to FP16.")
            # Schedule memory stabilization hooks if needed.
        else:
            print("Model does not support half(), skipping FP16 conversion.")
    except Exception as e:
        print(f"FP16 conversion failed: {e}")
    return model

def check_tensor_stability(tensor):
    """Run FP16 stability check on tensor if using FP16."""
    return FP16Stability.check_stability_metrics(tensor)
