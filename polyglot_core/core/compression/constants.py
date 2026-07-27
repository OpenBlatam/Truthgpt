from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union, Tuple
import time
from polyglot_core.core.backend import Backend, get_best_backend, is_backend_available


class CompressionAlgorithm(Enum):
    LZ4 = "lz4"
    ZSTD = "zstd"
    GZIP = "gzip"
    SNAPPY = "snappy"
    NONE = "none"



# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Default compression parameters
DEFAULT_ALGORITHM = "lz4"

DEFAULT_LEVEL = 3

DEFAULT_CHUNK_SIZE = 65536  # 64 KB


# Zstd compression levels
ZSTD_MIN_LEVEL = 1

ZSTD_MAX_LEVEL = 22

ZSTD_DEFAULT_LEVEL = 3

ZSTD_FAST_LEVEL = 1

ZSTD_HIGH_LEVEL = 19


# Time conversion
MICROSECONDS_PER_SECOND = 1_000_000

