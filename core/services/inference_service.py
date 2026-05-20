"""
Inference service for model inference operations.
"""
import logging
from typing import Dict, Any, Optional, List, Union
import torch

from .base_service import BaseService
from ..event_system import EventType
from ...inference.text_generator import TextGenerator
from ...inference.inference_engine import InferenceEngine

logger = logging.getLogger(__name__)


class InferenceService(BaseService):
    """
    Service for inference operations.
    Handles text generation, batch processing, and caching.
    """
    
    def __init__(self, **kwargs):
        """Initialize inference service."""
        super().__init__(name="InferenceService", **kwargs)
        self.text_generator: Optional[TextGenerator] = None
        self.inference_engine: Optional[InferenceEngine] = None
    
    def _do_initialize(self) -> None:
        """Initialize inference components."""
        pass
    
    def configure(
        self,
        model: torch.nn.Module,
        tokenizer: Any,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Configure inference service.
        
        Args:
            model: Model for inference
            tokenizer: Tokenizer
            config: Optional inference configuration
        """
        config = config or {}
        
        # Create text generator with caching
        self.text_generator = TextGenerator(
            model=model,
            tokenizer=tokenizer,
            device=config.get("device"),
            use_cache=config.get("use_cache", True),
            cache_dir=config.get("cache_dir"),
            max_batch_size=config.get("max_batch_size", 8),
            max_seq_length=config.get("max_seq_length", 512),
        )
        
        # Store inference engine reference
        self.inference_engine = self.text_generator.engine
        
        logger.info("Inference service configured")
    
    def generate(
        self,
        prompt: Union[str, List[str]],
        config: Optional[Dict[str, Any]] = None,
        use_cache: Optional[bool] = None,
    ) -> Union[str, List[str]]:
        """
        Generate text from prompt(s).
        
        Args:
            prompt: Input prompt(s)
            config: Optional generation configuration
            use_cache: Override cache setting
        
        Returns:
            Generated text(s)
        """
        if not self.text_generator:
            raise RuntimeError("Inference service not configured")
        
        config = config or {}
        generation_kwargs = {
            "max_new_tokens": config.get("max_new_tokens", 64),
            "temperature": config.get("temperature", 0.8),
            "top_p": config.get("top_p", 0.95),
            "top_k": config.get("top_k", 50),
            "repetition_penalty": config.get("repetition_penalty", 1.1),
            "do_sample": config.get("do_sample", True),
        }
        
        try:
            # Handle single vs batch
            if isinstance(prompt, str):
                result = self.text_generator.generate(
                    prompt,
                    use_cache=use_cache,
                    **generation_kwargs
                )
            else:
                result = self.text_generator.generate_batch(
                    prompt,
                    **generation_kwargs
                )
            
            # Emit event
            self.emit(EventType.METRIC_LOGGED, {
                "operation": "generate",
                "prompt_count": 1 if isinstance(prompt, str) else len(prompt),
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error during generation: {e}", exc_info=True)
            self.emit(EventType.ERROR_OCCURRED, {
                "error": str(e),
                "operation": "generate",
            })
            raise
    
    def profile(
        self,
        prompt: str,
        config: Optional[Dict[str, Any]] = None,
        num_runs: int = 10,
    ) -> Dict[str, float]:
        """
        Profile inference performance.
        
        Args:
            prompt: Test prompt
            config: Optional generation configuration
            num_runs: Number of profiling runs
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.inference_engine:
            raise RuntimeError("Inference service not configured")
        
        config = config or {}
        generation_kwargs = {
            "max_new_tokens": config.get("max_new_tokens", 64),
            "temperature": config.get("temperature", 0.8),
        }
        
        metrics = self.inference_engine.profile_inference(
            prompt=prompt,
            num_runs=num_runs,
            **generation_kwargs
        )
        
        return metrics
    
    def clear_cache(self) -> None:
        """Clear inference cache."""
        if self.text_generator:
            self.text_generator.clear_cache()
            logger.info("Inference cache cleared")
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics."""
        if self.text_generator:
            return self.text_generator.get_cache_stats()
        return None


