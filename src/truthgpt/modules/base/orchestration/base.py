import enum
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

class AgentType(enum.Enum):
    """Types of AI agents"""
    LEARNING_AGENT = "learning_agent"
    OPTIMIZATION_AGENT = "optimization_agent"
    EVALUATION_AGENT = "evaluation_agent"
    COORDINATION_AGENT = "coordination_agent"
    META_LEARNING_AGENT = "meta_learning_agent"

class TaskType(enum.Enum):
    """Types of tasks for orchestration"""
    TRAINING = "training"
    INFERENCE = "inference"
    OPTIMIZATION = "optimization"
    EVALUATION = "evaluation"
    META_LEARNING = "meta_learning"
    COORDINATION = "coordination"

class AgentStatus(enum.Enum):
    """Agent status"""
    IDLE = "idle"
    BUSY = "busy"
    LEARNING = "learning"
    COORDINATING = "coordinating"
    ERROR = "error"
    OFFLINE = "offline"

class MetaLearningStrategy(enum.Enum):
    """Meta-learning strategies"""
    MODEL_AGNOSTIC_META_LEARNING = "maml"
    GRADIENT_BASED_META_LEARNING = "gbml"
    METRIC_BASED_META_LEARNING = "mbml"
    MEMORY_BASED_META_LEARNING = "memory_based"
    OPTIMIZATION_BASED_META_LEARNING = "optimization_based"
    NEURAL_ARCHITECTURE_SEARCH = "nas"
    AUTOML = "automl"

@dataclass
class AgentConfig:
    """Configuration for AI agents"""
    agent_id: str
    agent_type: AgentType
    capabilities: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 3
    learning_rate: float = 0.001
    memory_size: int = 10000
    communication_range: int = 5
    specialization_level: float = 0.8
    collaboration_threshold: float = 0.6
    enable_meta_learning: bool = True

@dataclass
class Task:
    """Task for AI orchestration"""
    task_id: str
    task_type: TaskType
    priority: int = 1
    complexity: float = 0.5
    estimated_duration: float = 60.0
    required_capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    assigned_agent: Optional[str] = None
    status: str = "pending"

@dataclass
class AgentState:
    """Agent state information"""
    agent_id: str
    status: AgentStatus = AgentStatus.IDLE
    current_tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    learning_history: List[Dict[str, Any]] = field(default_factory=list)
    collaboration_history: Dict[str, int] = field(default_factory=dict)
    last_activity: float = field(default_factory=time.time)
    resource_usage: Dict[str, float] = field(default_factory=dict)

@dataclass
class MetaLearningConfig:
    """Configuration for meta-learning"""
    strategy: MetaLearningStrategy = MetaLearningStrategy.MODEL_AGNOSTIC_META_LEARNING
    inner_loop_steps: int = 5
    outer_loop_steps: int = 10
    meta_learning_rate: float = 0.01
    adaptation_threshold: float = 0.1
    task_similarity_threshold: float = 0.7
    enable_few_shot_learning: bool = True
    enable_zero_shot_learning: bool = True
    memory_bank_size: int = 1000
    enable_neural_architecture_search: bool = False
