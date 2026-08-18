"""
HuggingFace Diffusers Integration
=================================
Wrapper for Diffusers image generation pipelines with automatic memory optimizations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

import torch
import torch.nn as nn

from .exceptions import DiffusionError, ModelLoadError
from .interfaces import BaseModel
from .registry import register_model
from .types import DiffusionConfig, DiffusionOutput

logger = logging.getLogger(__name__)


@register_model("hf_diffusers", aliases=["hf-diffusers", "hf_diffusion", "diffusion_model_hf", "diffusers"])
class HFDiffusersModel(BaseModel):
    """
    Wrapper for HuggingFace Diffusers pipelines with memory management.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config=config)
        self.pipe: Optional[Any] = None
        self.device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if self.config.get("model", {}).get("name_or_path") or self.config.get("name") or self.config.get("name_or_path"):
            self.load(self.config)

    def load(self, cfg: Dict[str, Any]) -> None:
        """
        Load diffusion pipeline from configuration.
        """
        try:
            from diffusers import StableDiffusionPipeline
        except ImportError as e:
            raise ModelLoadError("diffusers package is required for HFDiffusersModel") from e

        try:
            if "model" in cfg and isinstance(cfg["model"], dict):
                name = cfg["model"].get("name_or_path") or cfg["model"].get("name")
            else:
                name = cfg.get("name_or_path") or cfg.get("name") or cfg.get("model_name")

            if not name:
                raise ModelLoadError("No diffusion model name or path specified")

            dtype = torch.float16 if torch.cuda.is_available() else None
            logger.info(f"Loading HFDiffusersModel: '{name}' (dtype={dtype})")

            self.pipe = StableDiffusionPipeline.from_pretrained(name, torch_dtype=dtype)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.pipe.to(self.device)

            try:
                self.pipe.enable_attention_slicing()
            except Exception:
                pass

            if not torch.cuda.is_available():
                try:
                    self.pipe.enable_model_cpu_offload()
                except Exception:
                    pass

            logger.info(f"HFDiffusersModel '{name}' loaded successfully")

        except Exception as e:
            if isinstance(e, (ModelLoadError, DiffusionError)):
                raise
            logger.error(f"Failed to load HFDiffusersModel: {e}", exc_info=True)
            raise ModelLoadError(f"Failed to load diffusion pipeline: {e}", original_exception=e) from e

    def to(self, device: Union[str, torch.device]) -> "HFDiffusersModel":
        if isinstance(device, str):
            self.device = torch.device(device)
        else:
            self.device = device

        if self.pipe is not None and hasattr(self.pipe, "to"):
            self.pipe.to(self.device)
        return self

    @torch.inference_mode()
    def infer(self, inputs: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate image given prompt inputs.
        """
        if self.pipe is None:
            raise DiffusionError("Pipeline is not loaded. Call load() first.")

        if isinstance(inputs, str):
            prompt = inputs
            gen_params = {}
        elif isinstance(inputs, dict):
            prompt = inputs.get("prompt") or inputs.get("text") or ""
            gen_params = inputs
        else:
            prompt = str(inputs)
            gen_params = {}

        try:
            steps = int(gen_params.get("steps", gen_params.get("num_inference_steps", 25)))
            guidance_scale = float(gen_params.get("guidance_scale", 7.5))
            negative_prompt = gen_params.get("negative_prompt")

            kwargs: Dict[str, Any] = {
                "num_inference_steps": steps,
                "guidance_scale": guidance_scale,
            }
            if negative_prompt:
                kwargs["negative_prompt"] = negative_prompt
            if "height" in gen_params:
                kwargs["height"] = int(gen_params["height"])
            if "width" in gen_params:
                kwargs["width"] = int(gen_params["width"])

            result = self.pipe(prompt, **kwargs)
            images = getattr(result, "images", result) if not isinstance(result, list) else result
            return {
                "image": images[0] if images else None,
                "images": images,
                "prompt": prompt,
            }

        except Exception as e:
            if isinstance(e, DiffusionError):
                raise
            logger.error(f"Inference error in HFDiffusersModel: {e}", exc_info=True)
            raise DiffusionError(f"Diffusion generation failed: {e}", original_exception=e) from e

    def generate(
        self,
        prompt: Union[str, List[str]],
        config: Optional[Union[DiffusionConfig, Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> DiffusionOutput:
        """
        Structured generation returning DiffusionOutput.
        """
        gen_dict = config.to_dict() if hasattr(config, "to_dict") else dict(config or {})
        gen_dict.update(kwargs)
        gen_dict["prompt"] = prompt

        res = self.infer(gen_dict)
        images = res.get("images") or ([res.get("image")] if res.get("image") is not None else [])
        return DiffusionOutput(
            images=images,
            seed=res.get("seed"),
            metadata={"prompt": prompt},
        )

    def get_info(self) -> Dict[str, Any]:
        return {
            "model_class": self.__class__.__name__,
            "is_loaded": self.pipe is not None,
            "device": str(getattr(self.pipe, "device", self.device)),
        }


# Alias for backward compatibility
HFDiffusion = HFDiffusersModel


def create_hf_diffusers_model(config: Optional[Dict[str, Any]] = None) -> HFDiffusersModel:
    """Factory function for HFDiffusersModel."""
    return HFDiffusersModel(config=config)


__all__ = [
    "HFDiffusersModel",
    "HFDiffusion",
    "create_hf_diffusers_model",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
