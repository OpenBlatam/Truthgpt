from enum import Enum
from dataclasses import dataclass, field
from typing import List

class OptimizerType(Enum):
    """Optimizer types"""
    ADAM = "adam"
    ADAMW = "adamw"
    SGD = "sgd"
    RMSPROP = "rmsprop"
    ADAGRAD = "adagrad"
    ADADELTA = "adadelta"
    LAMB = "lamb"
    LION = "lion"
    ADAMAX = "adamax"
    RPROP = "rprop"
    ADABOUND = "adabound"
    YOGI = "yogi"
    RANGER = "ranger"
    RANGERLARS = "rangerlars"
    RANGERQH = "rangerqh"
    RANGER21 = "ranger21"
    MADGRAD = "madgrad"
    ADAM_P = "adam_p"
    ADAMW_P = "adamw_p"
    SGD_P = "sgd_p"
    RMSPROP_P = "rmsprop_p"
    ADAGRAD_P = "adagrad_p"
    ADADELTA_P = "adadelta_p"
    LAMB_P = "lamb_p"
    LION_P = "lion_p"
    ADAMAX_P = "adamax_p"
    RPROP_P = "rprop_p"
    ADABOUND_P = "adabound_p"
    YOGI_P = "yogi_p"
    RANGER_P = "ranger_p"
    RANGERLARS_P = "rangerlars_p"
    RANGERQH_P = "rangerqh_p"
    RANGER21_P = "ranger21_p"
    MADGRAD_P = "madgrad_p"

class SchedulerType(Enum):
    """Scheduler types"""
    NONE = "none"
    STEP = "step"
    EXPONENTIAL = "exponential"
    COSINE = "cosine"
    LINEAR = "linear"
    POLYNOMIAL = "polynomial"
    PLATEAU = "plateau"
    WARMUP = "warmup"
    COSINE_WARM_RESTARTS = "cosine_warm_restarts"
    ONE_CYCLE = "one_cycle"
    CYCLIC = "cyclic"
    LAMBDA = "lambda"
    CUSTOM = "custom"

class OptimizationStrategy(Enum):
    """Supported industrial optimization strategies"""
    STANDARD = "standard"
    GRADIENT_ACCUMULATION = "gradient_accumulation"
    MIXED_PRECISION = "mixed_precision"
    DISTRIBUTED = "distributed"
    CONTINUAL = "continual"
    CURRICULUM = "curriculum"
    ADVERSARIAL = "adversarial"
    REINFORCEMENT = "reinforcement"

@dataclass
class OptimizationConfig:
    """Optimization configuration"""
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    momentum: float = 0.9
    beta1: float = 0.9
    beta2: float = 0.999
    eps: float = 1e-8
    optimizer: OptimizerType = OptimizerType.ADAMW
    use_amsgrad: bool = False
    use_amsbound: bool = False
    use_adabound: bool = False
    use_yogi: bool = False
    use_ranger: bool = False
    use_rangerlars: bool = False
    use_rangerqh: bool = False
    use_ranger21: bool = False
    use_madgrad: bool = False
    scheduler: SchedulerType = SchedulerType.COSINE
    warmup_steps: int = 100
    total_steps: int = 1000
    gamma: float = 0.1
    step_size: int = 30
    min_lr: float = 1e-6
    max_lr: float = 1e-2
    T_max: int = 1000
    T_0: int = 100
    T_mult: int = 1
    eta_min: float = 1e-6
    eta_max: float = 1e-2
    base_lr: float = 1e-4
    step_size_up: int = 2000
    step_size_down: int = 2000
    mode: str = "triangular"
    scale_mode: str = "cycle"
    cycle_momentum: bool = True
    base_momentum: float = 0.8
    max_momentum: float = 0.9
    use_gradient_clipping: bool = True
    gradient_clip_norm: float = 1.0
    use_gradient_accumulation: bool = False
    gradient_accumulation_steps: int = 1
    use_mixed_precision: bool = False
    use_distributed: bool = False
    use_continual: bool = False
    use_curriculum: bool = False
    use_adversarial: bool = False
    use_reinforcement: bool = False
    num_workers: int = 4
    pin_memory: bool = True
    prefetch_factor: int = 2
    persistent_workers: bool = True
    debug: bool = False
    use_autograd_anomaly: bool = False
    profile: bool = False
    profile_frequency: int = 100
