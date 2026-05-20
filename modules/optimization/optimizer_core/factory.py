import torch.optim as optim
import torch.nn as nn
from .base import OptimizerType, OptimizationConfig

def setup_optimizer(model: nn.Module, config: OptimizationConfig) -> optim.Optimizer:
    if config.optimizer == OptimizerType.ADAM: return optim.Adam(model.parameters(), config.learning_rate, (config.beta1, config.beta2), config.eps, config.weight_decay, config.use_amsgrad)
    if config.optimizer == OptimizerType.ADAMW: return optim.AdamW(model.parameters(), config.learning_rate, (config.beta1, config.beta2), config.eps, config.weight_decay, config.use_amsgrad)
    if config.optimizer == OptimizerType.SGD: return optim.SGD(model.parameters(), config.learning_rate, config.momentum, weight_decay=config.weight_decay)
    if config.optimizer == OptimizerType.RMSPROP: return optim.RMSprop(model.parameters(), config.learning_rate, config.momentum, weight_decay=config.weight_decay)
    if config.optimizer == OptimizerType.ADAGRAD: return optim.Adagrad(model.parameters(), config.learning_rate, config.weight_decay)
    if config.optimizer == OptimizerType.ADADELTA: return optim.Adadelta(model.parameters(), config.learning_rate, config.weight_decay)
    if config.optimizer == OptimizerType.ADAMAX: return optim.Adamax(model.parameters(), config.learning_rate, (config.beta1, config.beta2), config.eps, config.weight_decay)
    if config.optimizer == OptimizerType.RPROP: return optim.Rprop(model.parameters(), config.learning_rate)
    raise ValueError(f"Unsupported optimizer: {config.optimizer}")
