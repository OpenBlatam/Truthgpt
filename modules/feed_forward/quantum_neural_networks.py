"""
Quantum Neural Networks Module for PiMoE System
Implements quantum computing capabilities for enhanced AI performance
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, Empty
import json
import pickle
import hashlib
import math
import random
from collections import defaultdict, deque
import warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QuantumState:
    """Quantum state representation"""
    amplitude: complex
    phase: float
    entanglement: List[int]
    coherence: float
    decoherence_rate: float

@dataclass
class QuantumGate:
    """Quantum gate representation"""
    gate_type: str
    parameters: Dict[str, float]
    qubits: List[int]
    matrix: np.ndarray

@dataclass
class QuantumCircuit:
    """Quantum circuit representation"""
    gates: List[QuantumGate]
    qubits: int
    depth: int
    fidelity: float
    error_rate: float

class QuantumNeuralLayer(nn.Module):
    """Quantum Neural Network Layer"""
    
    def __init__(self, input_dim: int, output_dim: int, qubits: int = 8):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.qubits = qubits
        self.quantum_states = nn.Parameter(torch.randn(qubits, 2, dtype=torch.complex64))
        self.quantum_gates = nn.Parameter(torch.randn(qubits, qubits, dtype=torch.complex64))
        self.measurement_weights = nn.Parameter(torch.randn(qubits, output_dim))
        self.entanglement_matrix = nn.Parameter(torch.randn(qubits, qubits))
        
        # Initialize quantum parameters
        self._initialize_quantum_parameters()
    
    def _initialize_quantum_parameters(self):
        """Initialize quantum parameters with proper constraints"""
        with torch.no_grad():
            # Normalize quantum states
            self.quantum_states.data = torch.nn.functional.normalize(
                self.quantum_states.data, dim=1
            )
            
            # Initialize quantum gates as unitary matrices
            self.quantum_gates.data = self._create_unitary_matrix(self.qubits)
            
            # Initialize entanglement matrix
            self.entanglement_matrix.data = torch.randn_like(self.entanglement_matrix.data) * 0.1
    
    def _create_unitary_matrix(self, size: int) -> torch.Tensor:
        """Create a random unitary matrix"""
        # Generate random complex matrix
        real_part = torch.randn(size, size)
        imag_part = torch.randn(size, size)
        complex_matrix = torch.complex(real_part, imag_part)
        
        # Make it unitary using QR decomposition
        Q, R = torch.linalg.qr(complex_matrix)
        return Q
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through quantum neural layer"""
        batch_size = x.size(0)
        
        # Encode classical input into quantum state
        quantum_input = self._encode_classical_to_quantum(x)
        
        # Apply quantum gates
        quantum_output = self._apply_quantum_gates(quantum_input)
        
        # Apply entanglement
        entangled_output = self._apply_entanglement(quantum_output)
        
        # Measure quantum state
        classical_output = self._measure_quantum_state(entangled_output)
        
        return classical_output
    
    def _encode_classical_to_quantum(self, x: torch.Tensor) -> torch.Tensor:
        """Encode classical input into quantum state"""
        # Project input to quantum state space
        quantum_input = torch.matmul(x, self.quantum_states.real)
        quantum_input = torch.complex(quantum_input, torch.zeros_like(quantum_input))
        return quantum_input
    
    def _apply_quantum_gates(self, quantum_state: torch.Tensor) -> torch.Tensor:
        """Apply quantum gates to quantum state"""
        # Apply quantum gates
        quantum_output = torch.matmul(quantum_state, self.quantum_gates)
        return quantum_output
    
    def _apply_entanglement(self, quantum_state: torch.Tensor) -> torch.Tensor:
        """Apply quantum entanglement"""
        # Apply entanglement matrix
        entangled_state = torch.matmul(quantum_state, self.entanglement_matrix)
        return entangled_state
    
    def _measure_quantum_state(self, quantum_state: torch.Tensor) -> torch.Tensor:
        """Measure quantum state to get classical output"""
        # Compute measurement probabilities
        probabilities = torch.abs(quantum_state) ** 2
        
        # Apply measurement weights
        classical_output = torch.matmul(probabilities, self.measurement_weights)
        return classical_output

class QuantumAttention(nn.Module):
    """Quantum Attention Mechanism"""
    
    def __init__(self, dim: int, num_heads: int = 8, qubits: int = 8):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.qubits = qubits
        self.head_dim = dim // num_heads
        
        # Quantum attention components
        self.quantum_query = QuantumNeuralLayer(dim, self.head_dim, qubits)
        self.quantum_key = QuantumNeuralLayer(dim, self.head_dim, qubits)
        self.quantum_value = QuantumNeuralLayer(dim, self.head_dim, qubits)
        
        # Quantum superposition weights
        self.superposition_weights = nn.Parameter(torch.randn(num_heads, qubits))
        
        # Quantum interference matrix
        self.interference_matrix = nn.Parameter(torch.randn(num_heads, qubits, qubits))
        
        # Output projection
        self.output_projection = nn.Linear(dim, dim)
        
        # Initialize quantum parameters
        self._initialize_quantum_attention()
    
    def _initialize_quantum_attention(self):
        """Initialize quantum attention parameters"""
        with torch.no_grad():
            # Normalize superposition weights
            self.superposition_weights.data = torch.nn.functional.normalize(
                self.superposition_weights.data, dim=1
            )
            
            # Initialize interference matrix
            self.interference_matrix.data = torch.randn_like(self.interference_matrix.data) * 0.1
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Forward pass through quantum attention"""
        batch_size, seq_len, dim = x.size()
        
        # Generate quantum queries, keys, and values
        quantum_queries = self.quantum_query(x)
        quantum_keys = self.quantum_key(x)
        quantum_values = self.quantum_value(x)
        
        # Reshape for multi-head attention
        quantum_queries = quantum_queries.view(batch_size, seq_len, self.num_heads, self.head_dim)
        quantum_keys = quantum_keys.view(batch_size, seq_len, self.num_heads, self.head_dim)
        quantum_values = quantum_values.view(batch_size, seq_len, self.num_heads, self.head_dim)
        
        # Apply quantum superposition
        superposed_queries = self._apply_quantum_superposition(quantum_queries)
        superposed_keys = self._apply_quantum_superposition(quantum_keys)
        superposed_values = self._apply_quantum_superposition(quantum_values)
        
        # Compute quantum attention scores
        attention_scores = self._compute_quantum_attention_scores(
            superposed_queries, superposed_keys
        )
        
        # Apply quantum interference
        interference_scores = self._apply_quantum_interference(attention_scores)
        
        # Apply attention mask if provided
        if mask is not None:
            interference_scores = interference_scores.masked_fill(mask == 0, -1e9)
        
        # Apply softmax
        attention_weights = torch.softmax(interference_scores, dim=-1)
        
        # Apply attention to values
        attended_values = torch.matmul(attention_weights, superposed_values)
        
        # Reshape and project output
        attended_values = attended_values.view(batch_size, seq_len, dim)
        output = self.output_projection(attended_values)
        
        return output
    
    def _apply_quantum_superposition(self, x: torch.Tensor) -> torch.Tensor:
        """Apply quantum superposition to input"""
        # Apply superposition weights
        superposed = torch.matmul(x, self.superposition_weights.unsqueeze(0).unsqueeze(0))
        return superposed
    
    def _compute_quantum_attention_scores(self, queries: torch.Tensor, keys: torch.Tensor) -> torch.Tensor:
        """Compute quantum attention scores"""
        # Compute attention scores
        scores = torch.matmul(queries, keys.transpose(-2, -1))
        scores = scores / math.sqrt(self.head_dim)
        return scores
    
    def _apply_quantum_interference(self, scores: torch.Tensor) -> torch.Tensor:
        """Apply quantum interference to attention scores"""
        # Apply interference matrix
        interference_scores = torch.matmul(scores, self.interference_matrix)
        return interference_scores

class QuantumExpert(nn.Module):
    """Quantum Expert Network"""
    
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, qubits: int = 16):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.qubits = qubits
        
        # Quantum layers
        self.quantum_input_layer = QuantumNeuralLayer(input_dim, hidden_dim, qubits)
        self.quantum_hidden_layer = QuantumNeuralLayer(hidden_dim, hidden_dim, qubits)
        self.quantum_output_layer = QuantumNeuralLayer(hidden_dim, output_dim, qubits)
        
        # Quantum attention
        self.quantum_attention = QuantumAttention(hidden_dim, num_heads=8, qubits=qubits)
        
        # Quantum normalization
        self.quantum_norm = nn.LayerNorm(hidden_dim)
        
        # Quantum activation
        self.quantum_activation = nn.GELU()
        
        # Quantum dropout
        self.quantum_dropout = nn.Dropout(0.1)
        
        # Initialize quantum parameters
        self._initialize_quantum_expert()
    
    def _initialize_quantum_expert(self):
        """Initialize quantum expert parameters"""
        with torch.no_grad():
            # Initialize quantum layers
            for layer in [self.quantum_input_layer, self.quantum_hidden_layer, self.quantum_output_layer]:
                layer._initialize_quantum_parameters()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through quantum expert"""
        # Quantum input processing
        quantum_input = self.quantum_input_layer(x)
        quantum_input = self.quantum_norm(quantum_input)
        quantum_input = self.quantum_activation(quantum_input)
        quantum_input = self.quantum_dropout(quantum_input)
        
        # Quantum attention
        attended_input = self.quantum_attention(quantum_input)
        attended_input = self.quantum_norm(attended_input)
        
        # Quantum hidden processing
        quantum_hidden = self.quantum_hidden_layer(attended_input)
        quantum_hidden = self.quantum_norm(quantum_hidden)
        quantum_hidden = self.quantum_activation(quantum_hidden)
        quantum_hidden = self.quantum_dropout(quantum_hidden)
        
        # Quantum output processing
        quantum_output = self.quantum_output_layer(quantum_hidden)
        
        return quantum_output

class QuantumPiMoE(nn.Module):
    """Quantum PiMoE System"""
    
    def __init__(self, 
                 input_dim: int,
                 output_dim: int,
                 num_experts: int = 8,
                 expert_capacity: int = 1000,
                 qubits: int = 16,
                 quantum_layers: int = 3):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.num_experts = num_experts
        self.expert_capacity = expert_capacity
        self.qubits = qubits
        self.quantum_layers = quantum_layers
        
        # Quantum experts
        self.quantum_experts = nn.ModuleList([
            QuantumExpert(input_dim, 512, output_dim, qubits)
            for _ in range(num_experts)
        ])
        
        # Quantum router
        self.quantum_router = QuantumNeuralLayer(input_dim, num_experts, qubits)
        
        # Quantum load balancer
        self.quantum_load_balancer = QuantumNeuralLayer(num_experts, num_experts, qubits)
        
        # Quantum gating network
        self.quantum_gating = QuantumNeuralLayer(input_dim, num_experts, qubits)
        
        # Quantum aggregation
        self.quantum_aggregation = QuantumNeuralLayer(num_experts * output_dim, output_dim, qubits)
        
        # Quantum normalization
        self.quantum_norm = nn.LayerNorm(output_dim)
        
        # Quantum activation
        self.quantum_activation = nn.GELU()
        
        # Quantum dropout
        self.quantum_dropout = nn.Dropout(0.1)
        
        # Initialize quantum parameters
        self._initialize_quantum_pimoe()
    
    def _initialize_quantum_pimoe(self):
        """Initialize quantum PiMoE parameters"""
        with torch.no_grad():
            # Initialize quantum router
            self.quantum_router._initialize_quantum_parameters()
            
            # Initialize quantum load balancer
            self.quantum_load_balancer._initialize_quantum_parameters()
            
            # Initialize quantum gating
            self.quantum_gating._initialize_quantum_parameters()
            
            # Initialize quantum aggregation
            self.quantum_aggregation._initialize_quantum_parameters()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through quantum PiMoE"""
        batch_size, seq_len, dim = x.size()
        
        # Quantum routing
        quantum_routing_scores = self.quantum_router(x)
        quantum_routing_scores = torch.softmax(quantum_routing_scores, dim=-1)
        
        # Quantum load balancing
        balanced_scores = self.quantum_load_balancer(quantum_routing_scores)
        balanced_scores = torch.softmax(balanced_scores, dim=-1)
        
        # Quantum gating
        quantum_gates = self.quantum_gating(x)
        quantum_gates = torch.softmax(quantum_gates, dim=-1)
        
        # Apply quantum gates to routing scores
        gated_scores = quantum_routing_scores * quantum_gates
        
        # Process through quantum experts
        expert_outputs = []
        for i, expert in enumerate(self.quantum_experts):
            expert_output = expert(x)
            expert_outputs.append(expert_output)
        
        # Stack expert outputs
        expert_outputs = torch.stack(expert_outputs, dim=1)
        
        # Apply quantum gating to expert outputs
        gated_outputs = expert_outputs * gated_scores.unsqueeze(-1)
        
        # Quantum aggregation
        aggregated_output = self.quantum_aggregation(
            gated_outputs.view(batch_size, seq_len, -1)
        )
        
        # Quantum normalization and activation
        output = self.quantum_norm(aggregated_output)
        output = self.quantum_activation(output)
        output = self.quantum_dropout(output)
        
        return output

class QuantumOptimizer:
    """Quantum Optimization Engine"""
    
    def __init__(self, model: nn.Module, learning_rate: float = 1e-3):
        self.model = model
        self.learning_rate = learning_rate
        self.quantum_states = {}
        self.quantum_gates = {}
        self.optimization_history = []
        
        # Initialize quantum optimizer
        self._initialize_quantum_optimizer()
    
    def _initialize_quantum_optimizer(self):
        """Initialize quantum optimizer"""
        # Initialize quantum states for each parameter
        for name, param in self.model.named_parameters():
            if 'quantum' in name.lower():
                self.quantum_states[name] = torch.randn_like(param)
                self.quantum_gates[name] = torch.randn_like(param)
    
    def step(self, loss: torch.Tensor):
        """Perform quantum optimization step"""
        # Compute quantum gradients
        quantum_gradients = self._compute_quantum_gradients(loss)
        
        # Apply quantum gates
        self._apply_quantum_gates(quantum_gradients)
        
        # Update quantum states
        self._update_quantum_states(quantum_gradients)
        
        # Update model parameters
        self._update_model_parameters()
        
        # Record optimization history
        self.optimization_history.append(loss.item())
    
    def _compute_quantum_gradients(self, loss: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Compute quantum gradients"""
        quantum_gradients = {}
        
        # Compute gradients for quantum parameters
        for name, param in self.model.named_parameters():
            if 'quantum' in name.lower():
                if param.grad is not None:
                    quantum_gradients[name] = param.grad.clone()
        
        return quantum_gradients
    
    def _apply_quantum_gates(self, gradients: Dict[str, torch.Tensor]):
        """Apply quantum gates to gradients"""
        for name, grad in gradients.items():
            if name in self.quantum_gates:
                # Apply quantum gate transformation
                transformed_grad = torch.matmul(grad, self.quantum_gates[name])
                gradients[name] = transformed_grad
    
    def _update_quantum_states(self, gradients: Dict[str, torch.Tensor]):
        """Update quantum states"""
        for name, grad in gradients.items():
            if name in self.quantum_states:
                # Update quantum state
                self.quantum_states[name] = self.quantum_states[name] - self.learning_rate * grad
    
    def _update_model_parameters(self):
        """Update model parameters"""
        for name, param in self.model.named_parameters():
            if 'quantum' in name.lower() and name in self.quantum_states:
                param.data = self.quantum_states[name]

class QuantumPiMoEDemo:
    """Quantum PiMoE Demo"""
    
    def __init__(self):
        self.model = None
        self.optimizer = None
        self.quantum_circuits = {}
        self.performance_metrics = {}
        
        # Initialize demo
        self._initialize_demo()
    
    def _initialize_demo(self):
        """Initialize quantum PiMoE demo"""
        logger.info("Initializing Quantum PiMoE Demo...")
        
        # Create quantum PiMoE model
        self.model = QuantumPiMoE(
            input_dim=512,
            output_dim=256,
            num_experts=8,
            expert_capacity=1000,
            qubits=16,
            quantum_layers=3
        )
        
        # Create quantum optimizer
        self.optimizer = QuantumOptimizer(self.model, learning_rate=1e-3)
        
        # Initialize quantum circuits
        self._initialize_quantum_circuits()
        
        logger.info("Quantum PiMoE Demo initialized successfully!")
    
    def _initialize_quantum_circuits(self):
        """Initialize quantum circuits"""
        # Create quantum circuits for each expert
        for i in range(self.model.num_experts):
            circuit = QuantumCircuit(
                gates=[],
                qubits=self.model.qubits,
                depth=0,
                fidelity=1.0,
                error_rate=0.0
            )
            self.quantum_circuits[f"expert_{i}"] = circuit
    
    def run_quantum_demo(self):
        """Run quantum PiMoE demo"""
        logger.info("Running Quantum PiMoE Demo...")
        
        # Generate sample data
        batch_size = 32
        seq_len = 128
        input_dim = 512
        
        # Create sample input
        sample_input = torch.randn(batch_size, seq_len, input_dim)
        
        # Run quantum PiMoE
        start_time = time.time()
        with torch.no_grad():
            quantum_output = self.model(sample_input)
        end_time = time.time()
        
        # Compute performance metrics
        inference_time = end_time - start_time
        throughput = batch_size * seq_len / inference_time
        
        # Store performance metrics
        self.performance_metrics = {
            'inference_time': inference_time,
            'throughput': throughput,
            'output_shape': quantum_output.shape,
            'quantum_experts': self.model.num_experts,
            'qubits': self.model.qubits,
            'quantum_layers': self.model.quantum_layers
        }
        
        # Log results
        logger.info(f"Quantum PiMoE Demo Results:")
        logger.info(f"  Inference Time: {inference_time:.4f} seconds")
        logger.info(f"  Throughput: {throughput:.2f} tokens/second")
        logger.info(f"  Output Shape: {quantum_output.shape}")
        logger.info(f"  Quantum Experts: {self.model.num_experts}")
        logger.info(f"  Qubits: {self.model.qubits}")
        logger.info(f"  Quantum Layers: {self.model.quantum_layers}")
        
        return self.performance_metrics
    
    def run_quantum_optimization_demo(self):
        """Run quantum optimization demo"""
        logger.info("Running Quantum Optimization Demo...")
        
        # Generate sample data
        batch_size = 16
        seq_len = 64
        input_dim = 512
        
        # Create sample input and target
        sample_input = torch.randn(batch_size, seq_len, input_dim)
        sample_target = torch.randn(batch_size, seq_len, 256)
        
        # Run optimization
        num_epochs = 10
        losses = []
        
        for epoch in range(num_epochs):
            # Forward pass
            output = self.model(sample_input)
            
            # Compute loss
            loss = torch.nn.functional.mse_loss(output, sample_target)
            
            # Backward pass
            loss.backward()
            
            # Quantum optimization step
            self.optimizer.step(loss)
            
            # Clear gradients
            self.model.zero_grad()
            
            # Record loss
            losses.append(loss.item())
            
            logger.info(f"Epoch {epoch + 1}/{num_epochs}, Loss: {loss.item():.6f}")
        
        # Store optimization results
        self.performance_metrics['optimization_losses'] = losses
        self.performance_metrics['final_loss'] = losses[-1]
        self.performance_metrics['loss_reduction'] = losses[0] - losses[-1]
        
        logger.info(f"Quantum Optimization Demo Results:")
        logger.info(f"  Initial Loss: {losses[0]:.6f}")
        logger.info(f"  Final Loss: {losses[-1]:.6f}")
        logger.info(f"  Loss Reduction: {losses[0] - losses[-1]:.6f}")
        
        return self.performance_metrics
    
    def run_quantum_attention_demo(self):
        """Run quantum attention demo"""
        logger.info("Running Quantum Attention Demo...")
        
        # Generate sample data
        batch_size = 16
        seq_len = 64
        dim = 512
        
        # Create sample input
        sample_input = torch.randn(batch_size, seq_len, dim)
        
        # Create quantum attention
        quantum_attention = QuantumAttention(dim, num_heads=8, qubits=16)
        
        # Run quantum attention
        start_time = time.time()
        with torch.no_grad():
            attended_output = quantum_attention(sample_input)
        end_time = time.time()
        
        # Compute performance metrics
        attention_time = end_time - start_time
        attention_throughput = batch_size * seq_len / attention_time
        
        # Store performance metrics
        self.performance_metrics['quantum_attention'] = {
            'attention_time': attention_time,
            'attention_throughput': attention_throughput,
            'output_shape': attended_output.shape,
            'num_heads': 8,
            'qubits': 16
        }
        
        logger.info(f"Quantum Attention Demo Results:")
        logger.info(f"  Attention Time: {attention_time:.4f} seconds")
        logger.info(f"  Attention Throughput: {attention_throughput:.2f} tokens/second")
        logger.info(f"  Output Shape: {attended_output.shape}")
        logger.info(f"  Number of Heads: 8")
        logger.info(f"  Qubits: 16")
        
        return self.performance_metrics
    
    def run_quantum_expert_demo(self):
        """Run quantum expert demo"""
        logger.info("Running Quantum Expert Demo...")
        
        # Generate sample data
        batch_size = 16
        seq_len = 64
        input_dim = 512
        output_dim = 256
        
        # Create sample input
        sample_input = torch.randn(batch_size, seq_len, input_dim)
        
        # Create quantum expert
        quantum_expert = QuantumExpert(input_dim, 512, output_dim, qubits=16)
        
        # Run quantum expert
        start_time = time.time()
        with torch.no_grad():
            expert_output = quantum_expert(sample_input)
        end_time = time.time()
        
        # Compute performance metrics
        expert_time = end_time - start_time
        expert_throughput = batch_size * seq_len / expert_time
        
        # Store performance metrics
        self.performance_metrics['quantum_expert'] = {
            'expert_time': expert_time,
            'expert_throughput': expert_throughput,
            'output_shape': expert_output.shape,
            'input_dim': input_dim,
            'output_dim': output_dim,
            'qubits': 16
        }
        
        logger.info(f"Quantum Expert Demo Results:")
        logger.info(f"  Expert Time: {expert_time:.4f} seconds")
        logger.info(f"  Expert Throughput: {expert_throughput:.2f} tokens/second")
        logger.info(f"  Output Shape: {expert_output.shape}")
        logger.info(f"  Input Dimension: {input_dim}")
        logger.info(f"  Output Dimension: {output_dim}")
        logger.info(f"  Qubits: 16")
        
        return self.performance_metrics
    
    def run_comprehensive_quantum_demo(self):
        """Run comprehensive quantum demo"""
        logger.info("Running Comprehensive Quantum Demo...")
        
        # Run all demos
        self.run_quantum_demo()
        self.run_quantum_optimization_demo()
        self.run_quantum_attention_demo()
        self.run_quantum_expert_demo()
        
        # Compute overall performance
        overall_performance = self._compute_overall_performance()
        
        logger.info("Comprehensive Quantum Demo completed successfully!")
        return overall_performance
    
    def _compute_overall_performance(self) -> Dict[str, Any]:
        """Compute overall performance metrics"""
        overall_performance = {
            'quantum_pimoe': self.performance_metrics.get('inference_time', 0),
            'quantum_optimization': self.performance_metrics.get('final_loss', 0),
            'quantum_attention': self.performance_metrics.get('quantum_attention', {}).get('attention_time', 0),
            'quantum_expert': self.performance_metrics.get('quantum_expert', {}).get('expert_time', 0),
            'total_experts': self.model.num_experts,
            'total_qubits': self.model.qubits,
            'quantum_layers': self.model.quantum_layers
        }
        
        return overall_performance

def main():
    """Main function to run quantum PiMoE demo"""
    try:
        # Create quantum PiMoE demo
        demo = QuantumPiMoEDemo()
        
        # Run comprehensive demo
        performance = demo.run_comprehensive_quantum_demo()
        
        logger.info("Quantum PiMoE Demo completed successfully!")
        logger.info(f"Overall Performance: {performance}")
        
    except Exception as e:
        logger.error(f"Error running quantum PiMoE demo: {e}")
        raise

if __name__ == "__main__":
    main()

