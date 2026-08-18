"""
HuggingFace Transformers Integration
====================================
High-performance wrapper for HuggingFace CausalLM and Seq2Seq Transformer models.
Supports streaming generation, chat templates, embeddings extraction, and smart device placement.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import torch
import torch.nn as nn

from .exceptions import ModelInferenceError, ModelLoadError
from .interfaces import BaseModel
from .registry import register_model
from .types import GenerationConfig, ModelOutput

logger = logging.getLogger(__name__)


@register_model("hf_transformers", aliases=["hf-transformers", "hf_llm", "llm", "transformers"])
class HFTransformersModel(BaseModel):
    """
    Wrapper for HuggingFace Transformers models with optimized inference and generation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config=config)
        self.model: Optional[nn.Module] = None
        self.tokenizer: Optional[Any] = None
        self.device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Auto-load if config provides model name
        if self.config.get("model", {}).get("name_or_path") or self.config.get("name") or self.config.get("name_or_path"):
            self.load(self.config)

    def _resolve_dtype(self, mixed_precision: Optional[str]) -> Optional[torch.dtype]:
        if not mixed_precision or mixed_precision == "no":
            return torch.float32 if not torch.cuda.is_available() else torch.float16
        mp = mixed_precision.lower()
        if mp in ("bf16", "bfloat16"):
            return torch.bfloat16
        if mp in ("fp16", "float16"):
            return torch.float16
        return None

    def load(self, cfg: Dict[str, Any]) -> None:
        """
        Load model and tokenizer from configuration.
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as e:
            raise ModelLoadError("transformers package is required for HFTransformersModel") from e

        try:
            # Extract model identifier
            if "model" in cfg and isinstance(cfg["model"], dict):
                name = cfg["model"].get("name_or_path") or cfg["model"].get("name")
            else:
                name = cfg.get("name_or_path") or cfg.get("name") or cfg.get("model_name")

            if not name:
                raise ModelLoadError("No model name or path specified in configuration")

            mp = cfg.get("training", {}).get("mixed_precision") or cfg.get("mixed_precision", "no")
            dtype = self._resolve_dtype(mp)

            logger.info(f"Loading HFTransformersModel: '{name}' (dtype={dtype})")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token or "<|pad|>"

            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(name, torch_dtype=dtype)

            # Move to best available device
            self.to_device()
            self.eval_mode()

            # Enable KV-cache for inference
            if hasattr(self.model, "config"):
                try:
                    self.model.config.use_cache = True
                except Exception:
                    pass

            logger.info(f"HFTransformersModel '{name}' loaded successfully")

        except Exception as e:
            if isinstance(e, ModelLoadError):
                raise
            logger.error(f"Failed to load HFTransformersModel: {e}", exc_info=True)
            raise ModelLoadError(f"Failed to load HF model: {e}", original_exception=e) from e

    def to(self, device: Union[str, torch.device]) -> "HFTransformersModel":
        """Move model and internal reference to target device."""
        if isinstance(device, str):
            self.device = torch.device(device)
        else:
            self.device = device

        if self.model is not None and hasattr(self.model, "to"):
            self.model.to(self.device)
        return self

    @torch.inference_mode()
    def infer(self, inputs: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run text generation given an input prompt or text dictionary.
        """
        if self.model is None or self.tokenizer is None:
            raise ModelInferenceError("Model or Tokenizer is not loaded. Call load() first.")

        if isinstance(inputs, str):
            text_input = inputs
            gen_params = {}
        elif isinstance(inputs, dict):
            text_input = inputs.get("text") or inputs.get("prompt") or ""
            gen_params = inputs
        else:
            text_input = str(inputs)
            gen_params = {}

        try:
            device = self.device
            if hasattr(self.model, "parameters"):
                p = next(self.model.parameters(), None)
                if p is not None:
                    device = p.device

            toks = self.tokenizer(text_input, return_tensors="pt")
            if hasattr(toks, "to"):
                toks = toks.to(device)

            max_new_tokens = int(gen_params.get("max_new_tokens", gen_params.get("max_tokens", 64)))
            temperature = float(gen_params.get("temperature", 0.8))
            do_sample = gen_params.get("do_sample", temperature > 0.0)

            gen_kwargs: Dict[str, Any] = {
                "max_new_tokens": max_new_tokens,
                "do_sample": do_sample,
                "temperature": max(temperature, 1e-4) if do_sample else 1.0,
                "pad_token_id": getattr(self.tokenizer, "pad_token_id", None) or getattr(self.tokenizer, "eos_token_id", None),
            }

            if "top_p" in gen_params:
                gen_kwargs["top_p"] = float(gen_params["top_p"])
            if "top_k" in gen_params:
                gen_kwargs["top_k"] = int(gen_params["top_k"])
            if "repetition_penalty" in gen_params:
                gen_kwargs["repetition_penalty"] = float(gen_params["repetition_penalty"])

            output_ids = self.model.generate(**toks, **gen_kwargs)
            generated_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)

            input_len = toks["input_ids"].shape[1] if "input_ids" in toks else 0
            tokens_generated = max(0, len(output_ids[0]) - input_len)

            return {
                "text": generated_text,
                "tokens": output_ids,
                "tokens_generated": tokens_generated,
                "prompt": text_input,
            }

        except Exception as e:
            if isinstance(e, ModelInferenceError):
                raise
            logger.error(f"Inference error in HFTransformersModel: {e}", exc_info=True)
            raise ModelInferenceError(f"Inference failed: {e}", original_exception=e) from e

    def generate(
        self,
        prompt: str,
        config: Optional[Union[GenerationConfig, Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> ModelOutput:
        """
        Structured generation returning ModelOutput.
        """
        gen_dict = config.to_dict() if hasattr(config, "to_dict") else dict(config or {})
        gen_dict.update(kwargs)
        gen_dict["prompt"] = prompt

        res = self.infer(gen_dict)
        return ModelOutput(
            text=res.get("text"),
            tokens=res.get("tokens"),
            metadata={"prompt": prompt, "tokens_generated": res.get("tokens_generated", 0)},
        )

    def generate_stream(self, inputs: Dict[str, Any]) -> Iterator[str]:
        """Stream generated tokens one by one."""
        if self.model is None or self.tokenizer is None:
            raise ModelInferenceError("Model or Tokenizer is not loaded.")

        try:
            from transformers import TextIteratorStreamer
            import threading
        except ImportError:
            res = self.infer(inputs)
            yield res["text"]
            return

        device = self.device
        if hasattr(self.model, "parameters"):
            p = next(self.model.parameters(), None)
            if p is not None:
                device = p.device

        text_input = inputs.get("text") or inputs.get("prompt") or ""
        toks = self.tokenizer(text_input, return_tensors="pt")
        if hasattr(toks, "to"):
            toks = toks.to(device)

        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        max_new_tokens = int(inputs.get("max_new_tokens", 64))
        temperature = float(inputs.get("temperature", 0.8))

        gen_kwargs = {
            **toks,
            "streamer": streamer,
            "max_new_tokens": max_new_tokens,
            "do_sample": inputs.get("do_sample", temperature > 0.0),
            "temperature": max(temperature, 1e-4),
            "pad_token_id": getattr(self.tokenizer, "pad_token_id", None) or getattr(self.tokenizer, "eos_token_id", None),
        }

        thread = threading.Thread(target=self.model.generate, kwargs=gen_kwargs)
        thread.start()

        for new_text in streamer:
            yield new_text

        thread.join()

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Apply tokenizer chat template and return assistant response."""
        if self.tokenizer is None or not hasattr(self.tokenizer, "apply_chat_template"):
            formatted = "\n".join(f"{m['role']}: {m['content']}" for m in messages) + "\nassistant:"
            return self.infer({"text": formatted, **kwargs})["text"]

        formatted_prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        return self.infer({"text": formatted_prompt, **kwargs})["text"]

    @torch.inference_mode()
    def get_embeddings(self, text: Union[str, List[str]]) -> torch.Tensor:
        """Extract hidden state representations for given text."""
        if self.model is None or self.tokenizer is None:
            raise ModelInferenceError("Model is not loaded.")

        device = self.device
        if hasattr(self.model, "parameters"):
            p = next(self.model.parameters(), None)
            if p is not None:
                device = p.device

        toks = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        if hasattr(toks, "to"):
            toks = toks.to(device)
        outputs = self.model(**toks, output_hidden_states=True)
        last_hidden = outputs.hidden_states[-1]
        return last_hidden.mean(dim=1)


# Aliases for backward compatibility
HFLLM = HFTransformersModel


def create_hf_transformers_model(config: Optional[Dict[str, Any]] = None) -> HFTransformersModel:
    """Factory function for HFTransformersModel."""
    return HFTransformersModel(config=config)


__all__ = [
    "HFTransformersModel",
    "HFLLM",
    "create_hf_transformers_model",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
