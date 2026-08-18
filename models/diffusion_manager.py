"""
Diffusion Models Management Module
==================================
Comprehensive pipeline management for Stable Diffusion (SD 1.5, SD 2.1, SDXL, SD 3),
Flux, and Latent Consistency Models with memory offloading, LoRA, and scheduler tuning.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

import torch
import torch.nn as nn

from .exceptions import DiffusionError, ModelLoadError
from .interfaces import BaseDiffusionManager
from .registry import register_model

logger = logging.getLogger(__name__)

# Module-level imports with graceful fallback for testing/mocking
try:
    import diffusers
    from diffusers import (
        DDIMScheduler,
        DPMSolverMultistepScheduler,
        EulerAncestralDiscreteScheduler,
        EulerDiscreteScheduler,
        LCMScheduler,
        StableDiffusionPipeline,
        StableDiffusionXLPipeline,
        UniPCMultistepScheduler,
    )
    _DIFFUSERS_AVAILABLE = True
except ImportError:
    _DIFFUSERS_AVAILABLE = False
    diffusers = None
    DDIMScheduler = None
    DPMSolverMultistepScheduler = None
    EulerAncestralDiscreteScheduler = None
    EulerDiscreteScheduler = None
    LCMScheduler = None
    StableDiffusionPipeline = None
    StableDiffusionXLPipeline = None
    UniPCMultistepScheduler = None


@register_model("diffusion", aliases=["diffusion_manager", "diffusion_model"])
class DiffusionModelManager(BaseDiffusionManager):
    """
    Manages diffusion pipelines (SD 1.5/2.1, SDXL, custom) with scheduler and memory optimizations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.pipeline: Optional[Any] = None
        self.device: Optional[torch.device] = None
        self.model_id: Optional[str] = None

        # Auto-load if config provided model_id
        if self.config.get("model_id"):
            self.load_pipeline(**self.config)

    def load_pipeline(
        self,
        model_id: str,
        pipeline_type: str = "stable-diffusion",
        variant: Optional[str] = None,
        torch_dtype: Optional[Union[str, torch.dtype]] = None,
        device: Optional[Union[str, torch.device]] = None,
        scheduler_type: Optional[str] = None,
        enable_attention_slicing: bool = True,
        enable_vae_slicing: bool = True,
        enable_vae_tiling: bool = False,
        enable_model_cpu_offload: bool = False,
        enable_sequential_cpu_offload: bool = False,
        lora_weights: Optional[str] = None,
        lora_scale: float = 1.0,
        **kwargs: Any,
    ) -> Any:
        """
        Load a diffusion pipeline with performance and memory options.
        """
        if not _DIFFUSERS_AVAILABLE:
            raise DiffusionError(
                "diffusers package is required to load diffusion pipelines",
                pipeline_type=pipeline_type,
            )

        try:
            self.model_id = model_id
            target_device = self._resolve_device(device)
            self.device = target_device

            # Resolve dtype
            resolved_dtype = self._resolve_dtype(torch_dtype)

            logger.info(f"Loading {pipeline_type} pipeline '{model_id}' on {target_device} (dtype={resolved_dtype})")

            # Choose pipeline class
            if pipeline_type in ("stable-diffusion-xl", "sdxl"):
                pipeline_cls = StableDiffusionXLPipeline
            else:
                pipeline_cls = StableDiffusionPipeline

            if pipeline_cls is None:
                raise DiffusionError(f"Pipeline class for '{pipeline_type}' is unavailable")

            # Build load arguments
            load_kwargs: Dict[str, Any] = {**kwargs}
            if resolved_dtype is not None:
                load_kwargs["torch_dtype"] = resolved_dtype
            if variant is not None:
                load_kwargs["variant"] = variant

            pipeline = pipeline_cls.from_pretrained(model_id, **load_kwargs)

            # Configure scheduler if requested
            if scheduler_type:
                pipeline = self._set_scheduler(pipeline, scheduler_type)

            # Move to device unless offload is enabled
            if enable_model_cpu_offload and hasattr(pipeline, "enable_model_cpu_offload"):
                pipeline.enable_model_cpu_offload()
                logger.debug("Model CPU offload enabled")
            elif enable_sequential_cpu_offload and hasattr(pipeline, "enable_sequential_cpu_offload"):
                pipeline.enable_sequential_cpu_offload()
                logger.debug("Sequential CPU offload enabled")
            else:
                if hasattr(pipeline, "to"):
                    pipeline = pipeline.to(target_device)

            # Memory optimizations
            if enable_attention_slicing and hasattr(pipeline, "enable_attention_slicing"):
                pipeline.enable_attention_slicing()
                logger.debug("Attention slicing enabled")

            if enable_vae_slicing and hasattr(pipeline, "enable_vae_slicing"):
                pipeline.enable_vae_slicing()
                logger.debug("VAE slicing enabled")

            if enable_vae_tiling and hasattr(pipeline, "enable_vae_tiling"):
                pipeline.enable_vae_tiling()
                logger.debug("VAE tiling enabled")

            # Load LoRA if provided
            if lora_weights and hasattr(pipeline, "load_lora_weights"):
                pipeline.load_lora_weights(lora_weights)
                if hasattr(pipeline, "fuse_lora") and lora_scale != 1.0:
                    pipeline.fuse_lora(lora_scale=lora_scale)
                logger.info(f"Loaded LoRA weights from '{lora_weights}'")

            self.pipeline = pipeline
            logger.info(f"Diffusion pipeline '{model_id}' loaded successfully")
            return pipeline

        except Exception as e:
            if isinstance(e, DiffusionError):
                raise
            logger.error(f"Failed to load diffusion pipeline '{model_id}': {e}", exc_info=True)
            raise DiffusionError(f"Error loading pipeline: {e}", pipeline_type=pipeline_type) from e

    def _set_scheduler(self, pipeline: Any, scheduler_type: str) -> Any:
        """Helper to switch noise scheduler on pipeline."""
        scheduler_map = {
            "ddim": DDIMScheduler,
            "dpm": DPMSolverMultistepScheduler,
            "euler": EulerDiscreteScheduler,
            "euler_a": EulerAncestralDiscreteScheduler,
            "euler_ancestral": EulerAncestralDiscreteScheduler,
            "lcm": LCMScheduler,
            "unipc": UniPCMultistepScheduler,
        }
        st = scheduler_type.lower()
        if st in scheduler_map and scheduler_map[st] is not None:
            try:
                sched_cls = scheduler_map[st]
                pipeline.scheduler = sched_cls.from_config(pipeline.scheduler.config)
                logger.info(f"Scheduler updated to '{st}'")
            except Exception as e:
                logger.warning(f"Could not apply scheduler '{st}': {e}")
        return pipeline

    def _configure_scheduler(self, pipeline: Any, scheduler_type: str, diff: Optional[Dict[str, Any]] = None) -> Any:
        return self._set_scheduler(pipeline, scheduler_type)

    def generate(
        self,
        prompt: Union[str, List[str]],
        negative_prompt: Optional[Union[str, List[str]]] = None,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        height: Optional[int] = None,
        width: Optional[int] = None,
        num_images_per_prompt: int = 1,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate images from prompt.
        """
        if self.pipeline is None:
            raise DiffusionError("Pipeline is not loaded. Call load_pipeline() first.")

        try:
            generator = None
            if seed is not None:
                gen_device = self.device if self.device is not None else torch.device("cpu")
                generator = torch.Generator(device=gen_device).manual_seed(seed)

            gen_kwargs: Dict[str, Any] = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "num_images_per_prompt": num_images_per_prompt,
                "generator": generator,
                **kwargs,
            }
            if height is not None:
                gen_kwargs["height"] = height
            if width is not None:
                gen_kwargs["width"] = width

            with torch.inference_mode():
                result = self.pipeline(**gen_kwargs)

            return getattr(result, "images", result)

        except Exception as e:
            if isinstance(e, DiffusionError):
                raise
            logger.error(f"Image generation failed: {e}", exc_info=True)
            raise DiffusionError(f"Generation failed: {e}") from e

    def enable_xformers(self) -> None:
        """Enable xFormers memory efficient attention if supported."""
        if self.pipeline is not None and hasattr(self.pipeline, "enable_xformers_memory_efficient_attention"):
            try:
                self.pipeline.enable_xformers_memory_efficient_attention()
                logger.info("xFormers attention activated on diffusion pipeline")
            except Exception as e:
                logger.warning(f"Could not enable xFormers: {e}")

    def enable_model_cpu_offload(self) -> None:
        """Offload sub-modules to CPU."""
        if self.pipeline is not None and hasattr(self.pipeline, "enable_model_cpu_offload"):
            self.pipeline.enable_model_cpu_offload()

    def enable_sequential_cpu_offload(self) -> None:
        """Sequential sub-module CPU offloading for extreme low VRAM environments."""
        if self.pipeline is not None and hasattr(self.pipeline, "enable_sequential_cpu_offload"):
            self.pipeline.enable_sequential_cpu_offload()

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _resolve_device(self, device: Optional[Union[str, torch.device]]) -> torch.device:
        if device is None:
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if isinstance(device, str):
            return torch.device(device)
        return device

    def _resolve_dtype(self, dtype: Optional[Union[str, torch.dtype]]) -> Optional[torch.dtype]:
        if dtype is None:
            return torch.float16 if torch.cuda.is_available() else torch.float32
        if isinstance(dtype, torch.dtype):
            return dtype
        d_str = str(dtype).lower()
        if d_str in ("fp16", "float16"):
            return torch.float16
        if d_str in ("bf16", "bfloat16"):
            return torch.bfloat16
        if d_str in ("fp32", "float32"):
            return torch.float32
        return None


class DiffusionTrainer:
    """
    Utility trainer for fine-tuning diffusion UNet, DiT, and LoRA adapters.
    """

    def __init__(
        self,
        pipeline: Any,
        learning_rate: float = 5e-6,
        use_8bit_adam: bool = False,
    ) -> None:
        self.pipeline = pipeline
        self.learning_rate = learning_rate
        self.use_8bit_adam = use_8bit_adam

    def prepare_for_training(self) -> None:
        """Freeze VAE and Text Encoder; put UNet in training mode."""
        if hasattr(self.pipeline, "unet") and self.pipeline.unet is not None:
            self.pipeline.unet.train()
        if hasattr(self.pipeline, "vae") and self.pipeline.vae is not None:
            self.pipeline.vae.requires_grad_(False)
        if hasattr(self.pipeline, "text_encoder") and self.pipeline.text_encoder is not None:
            self.pipeline.text_encoder.requires_grad_(False)
        logger.info("Pipeline components prepared for training")

    def get_unet(self) -> Any:
        """Extract UNet model."""
        return getattr(self.pipeline, "unet", None)


# Alias for backward compatibility
DiffusionManager = DiffusionModelManager


def create_diffusion_manager(config: Optional[Dict[str, Any]] = None) -> DiffusionModelManager:
    """Factory helper to instantiate a DiffusionModelManager."""
    return DiffusionModelManager(config=config)


__all__ = [
    "DiffusionModelManager",
    "DiffusionManager",
    "DiffusionTrainer",
    "create_diffusion_manager",
    "DDIMScheduler",
    "DPMSolverMultistepScheduler",
    "EulerDiscreteScheduler",
    "EulerAncestralDiscreteScheduler",
    "LCMScheduler",
    "UniPCMultistepScheduler",
    "StableDiffusionPipeline",
    "StableDiffusionXLPipeline",
    "_DIFFUSERS_AVAILABLE",
]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.models."):
        sys.modules["models." + __name__[len("optimization_core.models."):]] = _mod
    elif __name__.startswith("models."):
        sys.modules["optimization_core.models." + __name__[len("models."):]] = _mod
