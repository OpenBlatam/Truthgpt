import enum
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from ...core.compiler_core import CompilationConfig, CompilationResult

class DistributedCompilationMode(enum.Enum):
    """Distributed compilation modes"""
    MASTER_WORKER = "master_worker"
    PEER_TO_PEER = "peer_to_peer"
    HIERARCHICAL = "hierarchical"
    MESH = "mesh"
    RING = "ring"
    STAR = "star"
    TREE = "tree"
    GRID = "grid"

class LoadBalancingStrategy(enum.Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    RESOURCE_BASED = "resource_based"
    ADAPTIVE = "adaptive"

class DistributedCompilationTarget(enum.Enum):
    """Distributed compilation targets"""
    MAXIMUM_THROUGHPUT = "maximum_throughput"
    MINIMUM_LATENCY = "minimum_latency"
    OPTIMAL_RESOURCE_USAGE = "optimal_resource_usage"
    FAULT_TOLERANCE = "fault_tolerance"
    SCALABILITY = "scalability"
    ENERGY_EFFICIENCY = "energy_efficiency"
    COST_OPTIMIZATION = "cost_optimization"
    PERFORMANCE_BALANCE = "performance_balance"

@dataclass
class DistributedCompilationConfig(CompilationConfig):
    """Advanced distributed compilation configuration"""
    # Distributed compilation settings
    compilation_mode: DistributedCompilationMode = DistributedCompilationMode.MASTER_WORKER
    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE
    target_metric: DistributedCompilationTarget = DistributedCompilationTarget.MAXIMUM_THROUGHPUT
    
    # Network settings
    master_node: str = os.environ.get("DISTRIBUTED_MASTER_NODE", "localhost:8000")
    worker_nodes: List[str] = field(default_factory=lambda: os.environ.get("DISTRIBUTED_WORKER_NODES", "localhost:8001,localhost:8002").split(","))
    network_timeout: float = 30.0
    network_retries: int = 3
    network_compression: bool = True
    network_encryption: bool = True
    
    # Load balancing settings
    enable_load_balancing: bool = True
    load_balancing_interval: float = 1.0
    load_balancing_threshold: float = 0.8
    adaptive_balancing: bool = True
    
    # Fault tolerance settings
    enable_fault_tolerance: bool = True
    fault_detection_interval: float = 5.0
    fault_recovery_timeout: float = 30.0
    redundancy_factor: int = 2
    checkpoint_interval: float = 10.0
    
    # Scalability settings
    max_workers: int = 100
    min_workers: int = 1
    auto_scaling: bool = True
    scaling_threshold: float = 0.7
    scaling_cooldown: float = 60.0
    
    # Performance settings
    enable_parallel_compilation: bool = True
    parallel_workers: int = 4
    enable_pipeline_compilation: bool = True
    pipeline_stages: int = 8
    enable_streaming_compilation: bool = True
    streaming_buffer_size: int = 1000
    
    # Resource management
    memory_limit_per_worker: int = 4096  # MB
    cpu_limit_per_worker: float = 1.0  # CPU cores
    gpu_limit_per_worker: int = 1
    network_bandwidth_limit: int = 1000  # Mbps
    
    # Advanced features
    enable_consensus_algorithm: bool = True
    consensus_timeout: float = 10.0
    enable_distributed_caching: bool = True
    cache_replication_factor: int = 3
    enable_distributed_monitoring: bool = True
    monitoring_interval: float = 1.0
    
    # Custom parameters
    custom_parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DistributedCompilationResult(CompilationResult):
    """Enhanced distributed compilation result"""
    # Distributed-specific metrics
    distributed_throughput: float = 0.0
    distributed_latency: float = 0.0
    load_balancing_efficiency: float = 0.0
    fault_tolerance_score: float = 0.0
    scalability_factor: float = 0.0
    
    # Network metrics
    network_bandwidth_usage: float = 0.0
    network_latency: float = 0.0
    network_packet_loss: float = 0.0
    network_throughput: float = 0.0
    network_efficiency: float = 0.0
    
    # Worker metrics
    active_workers: int = 0
    total_workers: int = 0
    worker_utilization: float = 0.0
    worker_load_balance: float = 0.0
    worker_fault_rate: float = 0.0
    
    # Resource metrics
    total_memory_usage: int = 0
    total_cpu_usage: float = 0.0
    total_gpu_usage: int = 0
    resource_efficiency: float = 0.0
    energy_consumption: float = 0.0
    
    # Performance metrics
    compilation_parallelism: int = 0
    pipeline_throughput: float = 0.0
    streaming_latency: float = 0.0
    cache_hit_rate: float = 0.0
    consensus_time: float = 0.0
    
    # Advanced metrics
    distributed_consensus: float = 0.0
    distributed_coordination: float = 0.0
    distributed_synchronization: float = 0.0
    distributed_consistency: float = 0.0
    distributed_availability: float = 0.0
    
    # Compilation metadata
    master_node: str = ""
    worker_nodes: List[str] = None
    compilation_topology: str = ""
    load_balancing_strategy: str = ""
    fault_tolerance_level: int = 0

    def __post_init__(self):
        if self.worker_nodes is None:
            self.worker_nodes = []
