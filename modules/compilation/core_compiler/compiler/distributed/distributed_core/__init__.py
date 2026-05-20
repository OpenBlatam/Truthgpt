import logging
from .base import (
    DistributedCompilationMode, LoadBalancingStrategy,
    DistributedCompilationTarget, DistributedCompilationConfig,
    DistributedCompilationResult
)
from .nodes import WorkerNode
from .balancer import LoadBalancer
from .fault_tolerance import FaultToleranceManager
from .compiler import DistributedCompiler

logger = logging.getLogger(__name__)

def create_distributed_compiler(config: DistributedCompilationConfig) -> DistributedCompiler:
    """Create a distributed compiler instance"""
    return DistributedCompiler(config)

def distributed_compilation_context(config: DistributedCompilationConfig):
    """Create a distributed compilation context"""
    class DistributedCompilationContext:
        def __init__(self, cfg: DistributedCompilationConfig):
            self.config = cfg
            self.compiler = None
            
        def __enter__(self):
            self.compiler = create_distributed_compiler(self.config)
            logger.info("Distributed compilation context started")
            return self.compiler
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.compiler:
                self.compiler.cleanup()
            logger.info("Distributed compilation context ended")
    
    return DistributedCompilationContext(config)

__all__ = [
    'DistributedCompilationMode',
    'LoadBalancingStrategy',
    'DistributedCompilationTarget',
    'DistributedCompilationConfig',
    'DistributedCompilationResult',
    'WorkerNode',
    'LoadBalancer',
    'FaultToleranceManager',
    'DistributedCompiler',
    'create_distributed_compiler',
    'distributed_compilation_context'
]
