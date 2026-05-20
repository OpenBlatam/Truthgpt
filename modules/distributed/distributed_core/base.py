import enum
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

class DistributionStrategy(enum.Enum):
    """Distribution strategies for computing"""
    DATA_PARALLEL = "data_parallel"
    MODEL_PARALLEL = "model_parallel"
    PIPELINE_PARALLEL = "pipeline_parallel"
    TENSOR_PARALLEL = "tensor_parallel"
    HYBRID_PARALLEL = "hybrid_parallel"
    CLOUD_COMPUTING = "cloud_computing"

class CommunicationBackend(enum.Enum):
    """Communication backends for distributed computing"""
    TCP = "tcp"
    UDP = "udp"
    ZMQ = "zmq"
    GRPC = "grpc"
    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    NATS = "nats"
    CONSUL = "consul"
    ETCD = "etcd"

class LoadBalancingStrategy(enum.Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    CONSISTENT_HASH = "consistent_hash"
    ADAPTIVE_LOAD_BALANCING = "adaptive"
    MACHINE_LEARNING_BASED = "resource_aware"

class WorkerStatus(enum.Enum):
    """Worker status"""
    IDLE = "idle"
    BUSY = "busy"
    TRAINING = "training"
    INFERENCE = "inference"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

@dataclass
class DistributedConfig:
    """Configuration for distributed computing"""
    distribution_strategy: DistributionStrategy = DistributionStrategy.DATA_PARALLEL
    communication_backend: CommunicationBackend = CommunicationBackend.ZMQ
    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    num_workers: int = 4
    master_port: int = 5555
    worker_ports: List[int] = field(default_factory=lambda: [5556, 5557, 5558, 5559])
    enable_auto_scaling: bool = True
    min_workers: int = 2
    max_workers: int = 16
    scaling_threshold: float = 0.8
    heartbeat_interval: float = 5.0
    timeout: float = 30.0
    enable_fault_tolerance: bool = True
    checkpoint_interval: float = 60.0
    enable_load_balancing: bool = True
    enable_monitoring: bool = True
    enable_optimization: bool = True

@dataclass
class WorkerInfo:
    """Worker information"""
    worker_id: str
    host: str
    port: int
    status: WorkerStatus = WorkerStatus.IDLE
    capabilities: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    last_heartbeat: float = field(default_factory=time.time)
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_response_time: float = 0.0

@dataclass
class TaskAssignment:
    """Task assignment for distributed computing"""
    task_id: str
    worker_id: str
    task_type: str
    priority: int = 1
    estimated_duration: float = 60.0
    data_size: int = 0
    assigned_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "assigned"
    data: Dict[str, Any] = field(default_factory=dict)
