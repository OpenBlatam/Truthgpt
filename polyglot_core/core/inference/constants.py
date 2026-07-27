from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict, Any
import numpy as np
import time
from polyglot_core.core.backend import Backend, get_best_backend, is_backend_available



# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Default generation parameters
DEFAULT_MAX_NEW_TOKENS = 100

DEFAULT_TEMPERATURE = 1.0

DEFAULT_TOP_K = 50

DEFAULT_TOP_P = 0.9

DEFAULT_REPETITION_PENALTY = 1.0

DEFAULT_NUM_BEAMS = 1


# Finish reasons
FINISH_REASON_MAX_LENGTH = "max_length"

FINISH_REASON_EOS = "eos"

FINISH_REASON_TIMEOUT = "timeout"


# Numerical stability
EPSILON = 1e-10

