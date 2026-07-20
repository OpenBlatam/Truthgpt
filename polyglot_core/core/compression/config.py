from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union, Tuple
import time
from .backend import Backend, get_best_backend, is_backend_available

from .constants import *

class CompressionConfig:
    """
    Configuration for compression.
    
    Attributes:
        algorithm: Compression algorithm to use
        level: Compression level (1-22 for zstd, ignored for lz4)
        chunk_size: Chunk size for streaming compression
    """
    algorithm: CompressionAlgorithm = CompressionAlgorithm.LZ4
    level: int = DEFAULT_LEVEL
    chunk_size: int = DEFAULT_CHUNK_SIZE
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.level < 1 or self.level > ZSTD_MAX_LEVEL:
            raise ValueError(
                f"Compression level must be in [1, {ZSTD_MAX_LEVEL}], got {self.level}"
            )
        if self.chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {self.chunk_size}")

class CompressionStats:
    """
    Compression statistics.
    
    Attributes:
        original_size: Original data size in bytes
        compressed_size: Compressed data size in bytes
        compression_time_us: Compression time in microseconds
        decompression_time_us: Decompression time in microseconds
        algorithm: Algorithm used for compression
    """
    original_size: int
    compressed_size: int
    compression_time_us: float = 0.0
    decompression_time_us: float = 0.0
    algorithm: str = ""
    
    @property
    def compression_ratio(self) -> float:
        """
        Calculate compression ratio (compressed / original).
        
        Returns:
            Compression ratio (0.0 if original_size is 0)
        """
        if self.original_size == 0:
            return 0.0
        return self.compressed_size / self.original_size
    
    @property
    def space_savings(self) -> float:
        """
        Calculate space savings percentage.
        
        Returns:
            Space savings as fraction (1.0 = 100% savings)
        """
        return 1.0 - self.compression_ratio
    
    @property
    def compression_throughput_mbps(self) -> float:
        """
        Calculate compression throughput in MB/s.
        
        Returns:
            Throughput in MB/s (0.0 if compression_time_us <= 0)
        """
        if self.compression_time_us <= 0:
            return 0.0
        # Convert bytes to MB and microseconds to seconds
        size_mb = self.original_size / 1_000_000
        time_seconds = self.compression_time_us / MICROSECONDS_PER_SECOND
        return size_mb / time_seconds

class CompressionResult:
    """
    Result from compression operation.
    
    Attributes:
        data: Compressed data bytes
        stats: Compression statistics
        success: Whether compression succeeded
        error: Error message if compression failed
    """
    data: bytes
    stats: CompressionStats
    success: bool = True
    error: str = ""

