import tensorflow as tf
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class TensorFlowSubOptimizer(ABC):
    """Abstract base class for TensorFlow sub-optimizers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
    @abstractmethod
    def optimize(self, model: tf.keras.Model) -> tf.keras.Model:
        """Apply optimization to the model."""
        pass
