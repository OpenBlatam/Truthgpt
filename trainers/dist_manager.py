"""
Distributed training helper module for trainers.

Handles PyTorch DDP rank resolution, device assignment, world size query,
all-reduce operations, process group setup/teardown, and barrier synchronization.
"""
import os
import logging
from typing import Dict, Any, Optional
import torch

from .exceptions import HardwareError, DistributedError

logger = logging.getLogger(__name__)


class DistributedManager:
    """
    Manages process group initialization and environment queries for distributed training.
    """

    def __init__(self) -> None:
        self._is_initialized: bool = False
        self._rank: int = 0
        self._local_rank: int = 0
        self._world_size: int = 1
        self._detect_environment()

    def _detect_environment(self) -> None:
        """Detect environment variables for rank and world size."""
        if "RANK" in os.environ and "WORLD_SIZE" in os.environ:
            self._rank = int(os.environ.get("RANK", 0))
            self._local_rank = int(os.environ.get("LOCAL_RANK", 0))
            self._world_size = int(os.environ.get("WORLD_SIZE", 1))

        if torch.distributed.is_available() and torch.distributed.is_initialized():
            self._is_initialized = True
            self._rank = torch.distributed.get_rank()
            self._world_size = torch.distributed.get_world_size()

    @property
    def is_main_process(self) -> bool:
        """Check if current process is rank 0 main process."""
        return self._rank == 0

    @property
    def rank(self) -> int:
        """Get global process rank integer."""
        return self._rank

    @property
    def local_rank(self) -> int:
        """Get local GPU rank integer."""
        return self._local_rank

    @property
    def world_size(self) -> int:
        """Get total world size integer."""
        return self._world_size

    def barrier(self) -> None:
        """Execute distributed process barrier synchronization."""
        if self._is_initialized and torch.distributed.is_available():
            try:
                torch.distributed.barrier()
            except Exception as e:
                logger.warning(f"Distributed barrier failed: {e}")

    def all_reduce_mean(self, tensor: torch.Tensor) -> torch.Tensor:
        """Reduce tensor across all distributed processes and compute mean."""
        if not self._is_initialized or not torch.distributed.is_available():
            return tensor
        try:
            cloned = tensor.clone()
            torch.distributed.all_reduce(cloned, op=torch.distributed.ReduceOp.SUM)
            return cloned / float(self._world_size)
        except Exception as e:
            logger.warning(f"All-reduce failed: {e}")
            return tensor

    def init_process_group(self, backend: str = "nccl") -> None:
        """Initialize PyTorch distributed process group if environment variables are present."""
        if not torch.distributed.is_available():
            raise DistributedError("PyTorch distributed package is not available.")
        if not torch.distributed.is_initialized():
            try:
                torch.distributed.init_process_group(backend=backend)
                self._detect_environment()
                logger.info(f"Initialized distributed process group: rank={self._rank}, world_size={self._world_size}, backend={backend}")
            except Exception as e:
                raise DistributedError(f"Failed to initialize distributed process group: {e}") from e

    def destroy_process_group(self) -> None:
        """Clean up and destroy distributed process group."""
        if torch.distributed.is_available() and torch.distributed.is_initialized():
            try:
                torch.distributed.destroy_process_group()
                self._is_initialized = False
                logger.info("Distributed process group destroyed.")
            except Exception as e:
                logger.warning(f"Failed to destroy process group: {e}")

    def info(self) -> Dict[str, Any]:
        """Return distributed status metadata."""
        return {
            "is_initialized": self._is_initialized,
            "rank": self._rank,
            "local_rank": self._local_rank,
            "world_size": self._world_size,
            "is_main_process": self.is_main_process,
        }


__all__ = ["DistributedManager"]

import sys
_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod
