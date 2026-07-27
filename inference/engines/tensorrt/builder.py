from __future__ import annotations
import logging
from typing import Optional, Any
from .engine import TensorRTLLMEngine
from ...schemas.engine_configs import TensorRTConfig, TensorRTBackend

logger = logging.getLogger(__name__)

try:
    from optimization_core.polyglot.kv_cache import KVCache
    POLYGLOT_AVAILABLE = True
except ImportError:
    POLYGLOT_AVAILABLE = False

class TensorRTEngineBuilder:
    """
    Builder pattern for constructing TensorRT-LLM engines.
    Ensures that complex initialization logic is completely decoupled from the Engine's runtime logic.
    """
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.config = TensorRTConfig()
        self.external_cache: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.model_config: Optional[Any] = None
        self.sampling_config: Optional[Any] = None

    def with_config(self, config: TensorRTConfig) -> TensorRTEngineBuilder:
        self.config = config
        return self

    def setup_backend(self) -> TensorRTEngineBuilder:
        if self.config.backend_mode == TensorRTBackend.AUTO:
            if POLYGLOT_AVAILABLE:
                try:
                    from optimization_core.polyglot import get_available_backends
                    backends = get_available_backends()
                    if backends.get("cpp"):
                        self.config.backend_mode = TensorRTBackend.TENSORRT_CPP
                    elif backends.get("rust"):
                        self.config.backend_mode = TensorRTBackend.TENSORRT_RUST
                    else:
                        self.config.backend_mode = TensorRTBackend.TENSORRT_ONLY
                except Exception:
                    self.config.backend_mode = TensorRTBackend.TENSORRT_ONLY
            else:
                self.config.backend_mode = TensorRTBackend.TENSORRT_ONLY
        logger.info(f"TensorRT backend configured as: {self.config.backend_mode}")
        return self

    def setup_kv_cache(self) -> TensorRTEngineBuilder:
        if self.config.use_rust_kv_cache and POLYGLOT_AVAILABLE:
            try:
                self.external_cache = KVCache(
                    max_size=16384,
                    eviction_strategy="adaptive",
                    enable_compression=True,
                )
                logger.info("External Rust KV cache initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize external cache: {e}")
        return self

    def setup_tensorrt_configs(self) -> TensorRTEngineBuilder:
        try:
            from tensorrt_llm.runtime import ModelConfig, SamplingConfig
            self.model_config = ModelConfig(
                max_batch_size=self.config.max_batch_size,
                max_beam_width=1,
                vocab_size=50257,
                num_layers=12,
                num_heads=12,
                hidden_size=768,
                gpt_attention_plugin=True,
                remove_input_padding=True,
            )
            self.sampling_config = SamplingConfig(
                end_id=50256,
                pad_id=50256,
                output_sequence_lengths=True,
                return_dict=True,
            )
        except ImportError:
            logger.warning("TensorRT-LLM not installed. Using mock configs for builder.")
            self.model_config = {"mock": True}
            self.sampling_config = {"mock": True}
        return self

    def setup_tokenizer(self) -> TensorRTEngineBuilder:
        try:
            from optimization_core.polyglot import Tokenizer
            self.tokenizer = Tokenizer(model_name="gpt2", use_rust=True)
        except ImportError:
            self.tokenizer = None
            logger.warning("Failed to initialize polyglot tokenizer. Will use fallback in engine.")
        return self

    def build(self) -> TensorRTLLMEngine:
        """
        Constructs the final immutable TensorRTLLMEngine instance.
        """
        logger.info(f"Building TensorRTLLMEngine for {self.model_path}")
        return TensorRTLLMEngine(
            model_path=self.model_path,
            config=self.config,
            external_cache=self.external_cache,
            model_config=self.model_config,
            sampling_config=self.sampling_config,
            tokenizer=self.tokenizer
        )
