from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, Tuple
import numpy as np
import math
import time
from .backend import Backend, get_best_backend, is_backend_available



# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Default attention parameters
DEFAULT_D_MODEL = 768

DEFAULT_N_HEADS = 12

DEFAULT_MAX_SEQ_LEN = 8192

DEFAULT_DROPOUT = 0.0

DEFAULT_WINDOW_SIZE = 512

DEFAULT_BLOCK_SIZE = 64

DEFAULT_ROPE_THETA = 10000.0


# Numerical stability
EPSILON = 1e-9

LARGE_NEGATIVE_VALUE = -1e9


# Time conversion
MILLISECONDS_PER_SECOND = 1000

