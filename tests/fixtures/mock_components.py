"""
Comprehensive Mock Components for Testing TruthGPT Optimization Core.
"""

from __future__ import annotations

import time
import random
from typing import Any, Dict, List, Optional, Tuple, Union
import torch
import torch.nn as nn


class MockOptimizer:
    """Mock optimizer for testing."""

    def __init__(self, name: str = "MockOptimizer", learning_rate: float = 0.001):
        self.name = name
        self.learning_rate = learning_rate
        self.step_count = 0
        self.optimization_history: List[Dict[str, Any]] = []

    def step(self, loss: Optional[torch.Tensor] = None) -> Dict[str, Any]:
        """Mock optimization step."""
        self.step_count += 1
        loss_val = loss.item() if isinstance(loss, torch.Tensor) else float(loss or 0.0)
        self.optimization_history.append({
            'step': self.step_count,
            'loss': loss_val,
            'learning_rate': self.learning_rate,
            'timestamp': time.time()
        })
        return {'optimized': True, 'step': self.step_count}

    def zero_grad(self) -> None:
        """Mock gradient zeroing."""
        pass

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        return {
            'total_steps': self.step_count,
            'current_lr': self.learning_rate,
            'history_length': len(self.optimization_history)
        }


class MockModel(nn.Module):
    """Mock model for testing."""

    def __init__(self, input_size: int = 512, hidden_size: int = 1024, output_size: int = 512):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        self.linear1 = nn.Linear(input_size, hidden_size)
        self.activation = nn.ReLU()
        self.linear2 = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(0.1)

        self.forward_count = 0
        self.performance_metrics: List[Dict[str, Any]] = []

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Mock forward pass."""
        start_time = time.time()
        self.forward_count += 1

        x = self.linear1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.linear2(x)

        end_time = time.time()
        self.performance_metrics.append({
            'forward_time': end_time - start_time,
            'input_shape': list(x.shape),
            'forward_count': self.forward_count
        })

        return x

    def generate(self, prompt: Any = "Hello world", **kwargs: Any) -> str:
        """Simulate text generation for testing."""
        return f"Generated text response for prompt: {prompt}"

    def get_model_stats(self) -> Dict[str, Any]:
        """Get model statistics."""
        total_params = sum(p.numel() for p in self.parameters())
        return {
            'total_parameters': total_params,
            'forward_count': self.forward_count,
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'output_size': self.output_size
        }


class MockAttention(nn.Module):
    """Mock attention mechanism for testing."""

    def __init__(self, d_model: int = 512, n_heads: int = 8):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads

        self.q_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)
        self.out_linear = nn.Linear(d_model, d_model)

        self.attention_count = 0
        self.attention_weights: List[float] = []

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Mock attention forward pass."""
        self.attention_count += 1
        batch_size, seq_len, d_model = query.shape

        q = self.q_linear(query)
        k = self.k_linear(key)
        v = self.v_linear(value)

        weights = torch.softmax(torch.randn(batch_size, self.n_heads, seq_len, seq_len), dim=-1)
        self.attention_weights.append(float(weights.mean().item()))

        output = self.out_linear(v)
        return output, weights

    def get_attention_stats(self) -> Dict[str, Any]:
        """Get attention statistics."""
        return {
            'attention_count': self.attention_count,
            'avg_attention_weight': sum(self.attention_weights) / len(self.attention_weights) if self.attention_weights else 0.0,
            'd_model': self.d_model,
            'n_heads': self.n_heads
        }


class MockMLP(nn.Module):
    """Mock MLP for testing."""

    def __init__(self, input_size: int = 512, hidden_size: int = 2048, output_size: int = 512):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        self.linear1 = nn.Linear(input_size, hidden_size)
        self.activation = nn.GELU()
        self.linear2 = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(0.1)

        self.forward_count = 0

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Mock MLP forward pass."""
        self.forward_count += 1
        x = self.linear1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.linear2(x)
        return x

    def get_mlp_stats(self) -> Dict[str, Any]:
        """Get MLP statistics."""
        return {
            'forward_count': self.forward_count,
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'output_size': self.output_size
        }


class MockDataset:
    """Mock dataset for testing."""

    def __init__(self, size: int = 1000, input_size: int = 512, output_size: int = 512):
        self.size = size
        self.input_size = input_size
        self.output_size = output_size

        self.data: List[Dict[str, torch.Tensor]] = []
        for i in range(size):
            self.data.append({
                'input': torch.randn(input_size),
                'target': torch.randn(output_size),
                'index': torch.tensor(i)
            })

        self.current_index = 0

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        return self.data[idx]

    def get_batch(self, batch_size: int = 32) -> Dict[str, torch.Tensor]:
        """Get a batch of data."""
        batch = []
        for _ in range(batch_size):
            batch.append(self.data[self.current_index % self.size])
            self.current_index += 1

        return {
            'input': torch.stack([item['input'] for item in batch]),
            'target': torch.stack([item['target'] for item in batch])
        }

    def get_dataset_stats(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        return {
            'size': self.size,
            'input_size': self.input_size,
            'output_size': self.output_size,
            'current_index': self.current_index
        }


class MockKVCache:
    """Mock KV cache for testing."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, torch.Tensor] = {}
        self.hit_count = 0
        self.miss_count = 0

    def put(self, key: str, value: torch.Tensor) -> bool:
        """Put value in cache."""
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = value
        return True

    def get(self, key: str) -> Optional[torch.Tensor]:
        """Get value from cache."""
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        self.miss_count += 1
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0.0
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache),
            'max_size': self.max_size
        }


class MockTokenizer:
    """Mock tokenizer for text encoding and decoding tests."""

    def __init__(self, vocab_size: int = 1000):
        self.vocab_size = vocab_size
        self.pad_token_id = 0
        self.eos_token_id = 1
        self.bos_token_id = 2

    def encode(self, text: str, max_length: int = 128) -> List[int]:
        tokens = [abs(hash(w)) % (self.vocab_size - 3) + 3 for w in text.split()]
        return tokens[:max_length]

    def decode(self, tokens: List[int]) -> str:
        return " ".join(f"token_{t}" for t in tokens)

    def __call__(self, text: Union[str, List[str]], max_length: int = 128, return_tensors: str = "pt") -> Dict[str, Any]:
        if isinstance(text, str):
            text = [text]
        input_ids = [self.encode(t, max_length=max_length) for t in text]
        max_len = max(len(ids) for ids in input_ids)
        padded = [ids + [self.pad_token_id] * (max_len - len(ids)) for ids in input_ids]
        mask = [[1] * len(ids) + [0] * (max_len - len(ids)) for ids in input_ids]
        if return_tensors == "pt":
            return {
                "input_ids": torch.tensor(padded, dtype=torch.long),
                "attention_mask": torch.tensor(mask, dtype=torch.long),
            }
        return {"input_ids": padded, "attention_mask": mask}


class MockTrainer:
    """Mock trainer orchestrator for training pipeline testing."""

    def __init__(self, model: Optional[Any] = None, optimizer: Optional[Any] = None):
        self.model = model or MockModel()
        self.optimizer = optimizer or MockOptimizer()
        self.epochs_trained = 0
        self.is_trained = False

    def train_epoch(self, dataloader: Any) -> Dict[str, float]:
        self.epochs_trained += 1
        loss = 0.5 / self.epochs_trained
        self.optimizer.step(loss)
        return {"loss": loss, "learning_rate": 0.001}

    def train(self, num_epochs: int = 3, dataloader: Optional[Any] = None) -> Dict[str, Any]:
        history = []
        for _ in range(num_epochs):
            res = self.train_epoch(dataloader)
            history.append(res)
        self.is_trained = True
        return {"epochs": num_epochs, "final_loss": history[-1]["loss"], "history": history}


class MockCompiler:
    """Mock compiler for JIT and kernel fusion testing."""

    def __init__(self, target_backend: str = "torchscript"):
        self.target_backend = target_backend
        self.compiled_models: Dict[str, Any] = {}

    def compile(self, model: nn.Module, sample_input: Optional[torch.Tensor] = None) -> Any:
        model_name = getattr(model, "__class__", type(model)).__name__
        self.compiled_models[model_name] = model
        return model

    def is_compiled(self, model_name: str) -> bool:
        return model_name in self.compiled_models


class MockAgent:
    """Mock autonomous optimization agent."""

    def __init__(self, name: str = "MockAgent", role: str = "optimizer"):
        self.name = name
        self.role = role
        self.state: Dict[str, Any] = {"status": "idle"}

    def act(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        self.state["status"] = "active"
        return {"action": "optimize", "parameters": {"lr": 1e-4}}

    def reset(self) -> None:
        self.state = {"status": "idle"}


class MockEvaluator:
    """Mock evaluation engine for metric computation."""

    def __init__(self, metrics: Optional[List[str]] = None):
        self.metrics = metrics or ["accuracy", "perplexity", "f1"]

    def evaluate(self, model: Any, dataloader: Any) -> Dict[str, float]:
        return {
            "accuracy": 0.945,
            "perplexity": 12.3,
            "f1": 0.91,
        }


__all__ = [
    "MockOptimizer",
    "MockModel",
    "MockAttention",
    "MockMLP",
    "MockDataset",
    "MockKVCache",
    "MockTokenizer",
    "MockTrainer",
    "MockCompiler",
    "MockAgent",
    "MockEvaluator",
]
