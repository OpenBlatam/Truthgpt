from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union, Tuple
import time
from polyglot_core.core.backend import Backend, get_best_backend, is_backend_available

from .constants import *
from .config import *


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS AND CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class CompressionAlgorithm(Enum):
    """Compression algorithms supported."""
    NONE = "none"
    LZ4 = "lz4"
    LZ4_HC = "lz4_hc"  # High compression variant
    ZSTD = "zstd"
    ZSTD_FAST = "zstd_fast"
    ZSTD_HIGH = "zstd_high"


# ═══════════════════════════════════════════════════════════════════════════════
# COMPRESSOR CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class Compressor:
    """
    High-performance compressor with automatic backend selection.
    
    Automatically selects the best backend:
    - Rust: 5+ GB/s with LZ4 (fastest)
    - C++: Similar performance with LZ4/Zstd
    - Python: Fallback with lz4/zstd packages
    
    Example:
        >>> compressor = Compressor(algorithm="lz4")
        >>> result = compressor.compress(data)
        >>> print(f"Ratio: {result.stats.compression_ratio:.2%}")
        >>> original = compressor.decompress(result.data)
    """
    
    def __init__(
        self,
        config: Optional[CompressionConfig] = None,
        algorithm: str = DEFAULT_ALGORITHM,
        level: int = DEFAULT_LEVEL,
        backend: Optional[Backend] = None
    ):
        """
        Initialize Compressor.
        
        Args:
            config: Compression configuration
            algorithm: Algorithm name (if config not provided)
            level: Compression level (if config not provided)
            backend: Force specific backend (None = auto-select)
            
        Raises:
            ValueError: If algorithm is invalid or level is out of range
        """
        if config is None:
            try:
                algo = CompressionAlgorithm(algorithm.lower())
            except ValueError:
                valid_algorithms = [a.value for a in CompressionAlgorithm]
                raise ValueError(
                    f"Invalid algorithm '{algorithm}'. "
                    f"Must be one of: {valid_algorithms}"
                )
            config = CompressionConfig(algorithm=algo, level=level)
        
        self.config = config
        self._backend = backend or get_best_backend('compression')
        self._impl = self._create_implementation()
    
    def _create_implementation(self):
        """
        Create backend-specific implementation.
        
        Returns:
            Backend implementation or None (use Python fallback)
        """
        if self._backend == Backend.RUST and is_backend_available(Backend.RUST):
            return self._create_rust_impl()
        elif self._backend == Backend.CPP and is_backend_available(Backend.CPP):
            return self._create_cpp_impl()
        else:
            return None  # Use Python fallback
    
    def _create_rust_impl(self):
        """
        Create Rust implementation.
        
        Returns:
            Rust compressor or None if unavailable
        """
        try:
            from optimization_core.rust_core import truthgpt_rust
            algo = self.config.algorithm.value
            return truthgpt_rust.PyCompressor(algo, self.config.level)
        except (ImportError, AttributeError, Exception):
            # Fallback to Python if Rust backend unavailable
            return None
    
    def _create_cpp_impl(self):
        """
        Create C++ implementation.
        
        Returns:
            C++ compressor or None if unavailable
        """
        # TODO: Implement C++ compression bindings
        # For now, fallback to Python
        return None
    
    def compress(self, data: bytes) -> CompressionResult:
        """
        Compress data.
        
        Args:
            data: Input bytes to compress
            
        Returns:
            CompressionResult with compressed data and statistics
            
        Note:
            Automatically falls back to Python implementation if backend fails.
        """
        if not data:
            return CompressionResult(
                data=b"",
                stats=CompressionStats(original_size=0, compressed_size=0),
                success=True
            )
        
        start_time = time.perf_counter()
        
        # Try backend implementation first
        if self._impl is not None:
            try:
                compressed = self._impl.compress(data)
                elapsed_us = (time.perf_counter() - start_time) * MICROSECONDS_PER_SECOND
                
                return CompressionResult(
                    data=compressed,
                    stats=CompressionStats(
                        original_size=len(data),
                        compressed_size=len(compressed),
                        compression_time_us=elapsed_us,
                        algorithm=self.config.algorithm.value
                    ),
                    success=True
                )
            except Exception as e:
                # Fallback to Python if backend fails
                return self._python_compress(data, error_msg=str(e))
        
        # Use Python fallback
        return self._python_compress(data)
    
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress data.
        
        Args:
            data: Compressed bytes to decompress
            
        Returns:
            Decompressed bytes
            
        Raises:
            ValueError: If decompression fails
            
        Note:
            Automatically falls back to Python implementation if backend fails.
        """
        if not data:
            return b""
        
        # Try backend implementation first
        if self._impl is not None:
            try:
                return self._impl.decompress(data)
            except Exception:
                # Fallback to Python if backend fails
                pass
        
        # Use Python fallback
        return self._python_decompress(data)
    
    def compress_with_stats(self, data: bytes) -> Tuple[bytes, CompressionStats]:
        """
        Compress and return stats separately.
        
        Args:
            data: Input bytes to compress
            
        Returns:
            Tuple of (compressed_data, stats)
        """
        result = self.compress(data)
        return result.data, result.stats
    
    def _python_compress(self, data: bytes, error_msg: str = "") -> CompressionResult:
        """
        Python fallback compression.
        
        Args:
            data: Input bytes to compress
            error_msg: Optional error message from failed backend
            
        Returns:
            CompressionResult
        """
        start_time = time.perf_counter()
        algo = self.config.algorithm
        
        try:
            if algo in (CompressionAlgorithm.LZ4, CompressionAlgorithm.LZ4_HC):
                compressed = self._compress_lz4(data)
            elif algo in (CompressionAlgorithm.ZSTD, CompressionAlgorithm.ZSTD_FAST,
                         CompressionAlgorithm.ZSTD_HIGH):
                compressed = self._compress_zstd(data, algo)
            else:
                # No compression
                compressed = data
            
            elapsed_us = (time.perf_counter() - start_time) * MICROSECONDS_PER_SECOND
            
            return CompressionResult(
                data=compressed,
                stats=CompressionStats(
                    original_size=len(data),
                    compressed_size=len(compressed),
                    compression_time_us=elapsed_us,
                    algorithm=algo.value
                ),
                success=True
            )
        except ImportError as e:
            return CompressionResult(
                data=data,
                stats=CompressionStats(
                    original_size=len(data),
                    compressed_size=len(data),
                    algorithm=algo.value
                ),
                success=False,
                error=f"Missing library: {e}. {error_msg}".strip()
            )
        except Exception as e:
            return CompressionResult(
                data=data,
                stats=CompressionStats(
                    original_size=len(data),
                    compressed_size=len(data),
                    algorithm=algo.value
                ),
                success=False,
                error=f"Compression failed: {e}. {error_msg}".strip()
            )
    
    def _compress_lz4(self, data: bytes) -> bytes:
        """
        Compress using LZ4.
        
        Args:
            data: Input bytes
            
        Returns:
            Compressed bytes
        """
        import lz4.frame
        
        if self.config.algorithm == CompressionAlgorithm.LZ4_HC:
            # High compression mode
            return lz4.frame.compress(data, compression_level=lz4.frame.COMPRESSIONLEVEL_MAXHC)
        else:
            # Fast mode (default)
            return lz4.frame.compress(data)
    
    def _compress_zstd(self, data: bytes, algo: CompressionAlgorithm) -> bytes:
        """
        Compress using Zstd.
        
        Args:
            data: Input bytes
            algo: Zstd algorithm variant
            
        Returns:
            Compressed bytes
        """
        import zstandard
        
        # Determine compression level based on algorithm variant
        level_map = {
            CompressionAlgorithm.ZSTD_FAST: ZSTD_FAST_LEVEL,
            CompressionAlgorithm.ZSTD: self.config.level,
            CompressionAlgorithm.ZSTD_HIGH: ZSTD_HIGH_LEVEL
        }
        level = level_map.get(algo, ZSTD_DEFAULT_LEVEL)
        
        # Clamp level to valid range
        level = max(ZSTD_MIN_LEVEL, min(level, ZSTD_MAX_LEVEL))
        
        cctx = zstandard.ZstdCompressor(level=level)
        return cctx.compress(data)
    
    def _python_decompress(self, data: bytes) -> bytes:
        """
        Python fallback decompression.
        
        Args:
            data: Compressed bytes
            
        Returns:
            Decompressed bytes
            
        Raises:
            ValueError: If decompression fails
        """
        algo = self.config.algorithm
        
        try:
            if algo in (CompressionAlgorithm.LZ4, CompressionAlgorithm.LZ4_HC):
                import lz4.frame
                return lz4.frame.decompress(data)
            elif algo in (CompressionAlgorithm.ZSTD, CompressionAlgorithm.ZSTD_FAST,
                         CompressionAlgorithm.ZSTD_HIGH):
                import zstandard
                dctx = zstandard.ZstdDecompressor()
                return dctx.decompress(data)
            else:
                # No compression
                return data
        except ImportError as e:
            raise ValueError(f"Missing library for decompression: {e}")
        except Exception as e:
            raise ValueError(f"Decompression failed: {e}")
    
    @property
    def backend(self) -> Backend:
        """Get current backend."""
        return self._backend
    
    def __repr__(self) -> str:
        return (f"Compressor(algorithm={self.config.algorithm.value}, "
                f"level={self.config.level}, backend={self._backend.name})")


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def compress(data: bytes, algorithm: str = DEFAULT_ALGORITHM, level: int = DEFAULT_LEVEL) -> bytes:
    """
    Quick compress function.
    
    Args:
        data: Input bytes to compress
        algorithm: Compression algorithm (default: "lz4")
        level: Compression level (default: 3)
        
    Returns:
        Compressed bytes
    """
    return Compressor(algorithm=algorithm, level=level).compress(data).data



def decompress(data: bytes, algorithm: str = DEFAULT_ALGORITHM) -> bytes:
    """
    Quick decompress function.
    
    Args:
        data: Compressed bytes to decompress
        algorithm: Compression algorithm (default: "lz4")
        
    Returns:
        Decompressed bytes
    """
    return Compressor(algorithm=algorithm).decompress(data)

