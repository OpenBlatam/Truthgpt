from dataclasses import dataclass, field
from typing import Optional, List, Union, Dict, Any
import numpy as np
from .backend import Backend, get_best_backend, is_backend_available



# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Default tokenizer parameters
DEFAULT_MODEL_NAME = "gpt2"

DEFAULT_MAX_LENGTH = 512


# Tensor types
TENSOR_TYPE_NUMPY = "np"

TENSOR_TYPE_PYTORCH = "pt"

TENSOR_TYPE_TENSORFLOW = "tf"

