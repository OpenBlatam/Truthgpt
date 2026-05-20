"""
Reasoning Expert Module
Specialized expert for logical reasoning and problem-solving tasks.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import time
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .base_expert import BaseExpert, ExpertConfig, ExpertResult, ExpertType, ExpertStatus

@dataclass
class ReasoningExpertConfig(ExpertConfig):
    """Configuration for reasoning expert."""
    reasoning_layers: int = 6
    reasoning_heads: int = 12
    logical_attention: bool = True
    causal_reasoning: bool = True
    deductive_reasoning: bool = True
    inductive_reasoning: bool = True
    abductive_reasoning: bool = True
    reasoning_temperature: float = 0.7
    confidence_threshold: float = 0.8
    enable_step_by_step: bool = True
    max_reasoning_steps: int = 10

class ReasoningExpert(BaseExpert):
    """
    Expert specialized in logical reasoning and problem-solving.
    """
    
    def __init__(self, config: ReasoningExpertConfig):
        super().__init__(config)
        self.config = config
        self.reasoning_chain = []
        self.reasoning_steps = 0
        
    def initialize(self) -> None:
        """Initialize the reasoning expert."""
        # Create reasoning-specific model
        self.model = ReasoningModel(self.config)
        
        # Initialize reasoning components
        if self.config.logical_attention:
            self.logical_attention = LogicalAttentionLayer(
                hidden_size=self.config.hidden_size,
                num_heads=self.config.reasoning_heads
            )
        
        if self.config.causal_reasoning:
            self.causal_reasoner = CausalReasoningLayer(
                hidden_size=self.config.hidden_size
            )
        
        if self.config.deductive_reasoning:
            self.deductive_reasoner = DeductiveReasoningLayer(
                hidden_size=self.config.hidden_size
            )
        
        if self.config.inductive_reasoning:
            self.inductive_reasoner = InductiveReasoningLayer(
                hidden_size=self.config.hidden_size
            )
        
        if self.config.abductive_reasoning:
            self.abductive_reasoner = AbductiveReasoningLayer(
                hidden_size=self.config.hidden_size
            )
        
        # Step-by-step reasoning
        if self.config.enable_step_by_step:
            self.step_reasoner = StepByStepReasoningLayer(
                hidden_size=self.config.hidden_size,
                max_steps=self.config.max_reasoning_steps
            )
        
        # Initialize weights
        self._initialize_weights()
        
        self._initialized = True
        self.logger.info(f"Reasoning expert {self.config.expert_id} initialized")
    
    def _initialize_weights(self) -> None:
        """Initialize model weights."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.LayerNorm):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)
    
    def process_tokens(
        self, 
        input_tokens: torch.Tensor, 
        attention_mask: Optional[torch.Tensor] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ExpertResult:
        """Process tokens through reasoning expert."""
        start_time = time.time()
        
        try:
            # Validate input
            self.validate_input(input_tokens)
            
            # Check cache
            cache_key = self.get_cache_key(input_tokens, context)
            if cache_key:
                cached_result = self.get_cached_result(cache_key)
                if cached_result:
                    return cached_result
            
            # Set status
            self.set_status(ExpertStatus.PROCESSING)
            
            # Perform reasoning
            reasoning_output, reasoning_confidence = self._perform_reasoning(
                input_tokens, attention_mask, context
            )
            
            # Create result
            result = ExpertResult(
                output=reasoning_output,
                processing_time=time.time() - start_time,
                expert_id=self.config.expert_id,
                expert_type=self.config.expert_type.value,
                confidence=reasoning_confidence,
                metadata={
                    'reasoning_steps': self.reasoning_steps,
                    'reasoning_chain': self.reasoning_chain.copy(),
                    'reasoning_types': self._get_active_reasoning_types()
                },
                success=True
            )
            
            # Cache result
            if cache_key:
                self.cache_result(cache_key, result)
            
            # Record metrics and log
            self.record_metrics(result)
            self.log_processing(result, input_tokens.shape)
            
            # Reset for next processing
            self.reasoning_chain.clear()
            self.reasoning_steps = 0
            
            return result
            
        except Exception as e:
            self.set_status(ExpertStatus.ERROR)
            self.logger.error(f"Reasoning expert processing failed: {e}")
            
            return ExpertResult(
                output=input_tokens,  # Return input as fallback
                processing_time=time.time() - start_time,
                expert_id=self.config.expert_id,
                expert_type=self.config.expert_type.value,
                confidence=0.0,
                metadata={'error': str(e)},
                success=False,
                error_message=str(e)
            )
        
        finally:
            self.set_status(ExpertStatus.IDLE)
    
    def _perform_reasoning(
        self, 
        input_tokens: torch.Tensor, 
        attention_mask: Optional[torch.Tensor] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[torch.Tensor, float]:
        """Perform reasoning on input tokens."""
        batch_size, seq_len, hidden_size = input_tokens.shape
        
        # Start with input tokens
        reasoning_output = input_tokens.clone()
        total_confidence = 0.0
        reasoning_count = 0
        
        # Apply logical attention if enabled
        if self.config.logical_attention and hasattr(self, 'logical_attention'):
            reasoning_output = self.logical_attention(reasoning_output, attention_mask)
            self.reasoning_chain.append("logical_attention")
            reasoning_count += 1
        
        # Apply causal reasoning
        if self.config.causal_reasoning and hasattr(self, 'causal_reasoner'):
            reasoning_output = self.causal_reasoner(reasoning_output)
            self.reasoning_chain.append("causal_reasoning")
            reasoning_count += 1
        
        # Apply deductive reasoning
        if self.config.deductive_reasoning and hasattr(self, 'deductive_reasoner'):
            reasoning_output = self.deductive_reasoner(reasoning_output)
            self.reasoning_chain.append("deductive_reasoning")
            reasoning_count += 1
        
        # Apply inductive reasoning
        if self.config.inductive_reasoning and hasattr(self, 'inductive_reasoner'):
            reasoning_output = self.inductive_reasoner(reasoning_output)
            self.reasoning_chain.append("inductive_reasoning")
            reasoning_count += 1
        
        # Apply abductive reasoning
        if self.config.abductive_reasoning and hasattr(self, 'abductive_reasoner'):
            reasoning_output = self.abductive_reasoner(reasoning_output)
            self.reasoning_chain.append("abductive_reasoning")
            reasoning_count += 1
        
        # Step-by-step reasoning
        if self.config.enable_step_by_step and hasattr(self, 'step_reasoner'):
            reasoning_output, step_confidence = self.step_reasoner(
                reasoning_output, attention_mask, context
            )
            total_confidence += step_confidence
            reasoning_count += 1
        
        # Apply main reasoning model
        reasoning_output = self.model(reasoning_output, attention_mask)
        
        # Compute confidence
        if reasoning_count > 0:
            confidence = total_confidence / reasoning_count
        else:
            confidence = 0.5  # Default confidence
        
        # Apply temperature scaling
        confidence = confidence * self.config.reasoning_temperature
        
        # Update reasoning steps
        self.reasoning_steps = len(self.reasoning_chain)
        
        return reasoning_output, min(1.0, max(0.0, confidence))
    
    def _get_active_reasoning_types(self) -> List[str]:
        """Get list of active reasoning types."""
        active_types = []
        
        if self.config.logical_attention:
            active_types.append("logical_attention")
        if self.config.causal_reasoning:
            active_types.append("causal_reasoning")
        if self.config.deductive_reasoning:
            active_types.append("deductive_reasoning")
        if self.config.inductive_reasoning:
            active_types.append("inductive_reasoning")
        if self.config.abductive_reasoning:
            active_types.append("abductive_reasoning")
        if self.config.enable_step_by_step:
            active_types.append("step_by_step")
        
        return active_types
    
    def get_expert_info(self) -> Dict[str, Any]:
        """Get expert information and statistics."""
        return {
            'expert_id': self.config.expert_id,
            'expert_type': self.config.expert_type.value,
            'reasoning_layers': self.config.reasoning_layers,
            'reasoning_heads': self.config.reasoning_heads,
            'logical_attention': self.config.logical_attention,
            'causal_reasoning': self.config.causal_reasoning,
            'deductive_reasoning': self.config.deductive_reasoning,
            'inductive_reasoning': self.config.inductive_reasoning,
            'abductive_reasoning': self.config.abductive_reasoning,
            'step_by_step': self.config.enable_step_by_step,
            'max_reasoning_steps': self.config.max_reasoning_steps,
            'reasoning_temperature': self.config.reasoning_temperature,
            'confidence_threshold': self.config.confidence_threshold,
            'status': self.status.value,
            'metrics': self.get_metrics()
        }

class ReasoningModel(nn.Module):
    """Main reasoning model."""
    
    def __init__(self, config: ReasoningExpertConfig):
        super().__init__()
        self.config = config
        
        # Input embedding
        self.input_embedding = nn.Linear(config.hidden_size, config.hidden_size)
        
        # Reasoning layers
        self.reasoning_layers = nn.ModuleList([
            ReasoningLayer(config, i) for i in range(config.reasoning_layers)
        ])
        
        # Output projection
        self.output_projection = nn.Linear(config.hidden_size, config.hidden_size)
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(config.hidden_size)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout)
    
    def forward(
        self, 
        x: torch.Tensor, 
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Forward pass through reasoning model."""
        # Input embedding
        x = self.input_embedding(x)
        
        # Reasoning layers
        for layer in self.reasoning_layers:
            x = layer(x, attention_mask)
        
        # Output projection
        x = self.output_projection(x)
        
        # Layer normalization and dropout
        x = self.layer_norm(x)
        x = self.dropout(x)
        
        return x

class ReasoningLayer(nn.Module):
    """Single reasoning layer."""
    
    def __init__(self, config: ReasoningExpertConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx
        
        # Self-attention
        self.self_attention = nn.MultiheadAttention(
            embed_dim=config.hidden_size,
            num_heads=config.reasoning_heads,
            dropout=config.dropout,
            batch_first=True
        )
        
        # Cross-attention for reasoning
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=config.hidden_size,
            num_heads=config.reasoning_heads,
            dropout=config.dropout,
            batch_first=True
        )
        
        # Feed-forward network
        self.feed_forward = nn.Sequential(
            nn.Linear(config.hidden_size, config.intermediate_size),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.intermediate_size, config.hidden_size)
        )
        
        # Layer normalization
        self.layer_norm1 = nn.LayerNorm(config.hidden_size)
        self.layer_norm2 = nn.LayerNorm(config.hidden_size)
        self.layer_norm3 = nn.LayerNorm(config.hidden_size)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout)
    
    def forward(
        self, 
        x: torch.Tensor, 
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Forward pass through reasoning layer."""
        # Self-attention
        attn_output, _ = self.self_attention(x, x, x, key_padding_mask=attention_mask)
        x = x + self.dropout(attn_output)
        x = self.layer_norm1(x)
        
        # Cross-attention (reasoning about relationships)
        cross_attn_output, _ = self.cross_attention(x, x, x, key_padding_mask=attention_mask)
        x = x + self.dropout(cross_attn_output)
        x = self.layer_norm2(x)
        
        # Feed-forward
        ff_output = self.feed_forward(x)
        x = x + self.dropout(ff_output)
        x = self.layer_norm3(x)
        
        return x

class LogicalAttentionLayer(nn.Module):
    """Logical attention layer for reasoning."""
    
    def __init__(self, hidden_size: int, num_heads: int):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        
        self.q_linear = nn.Linear(hidden_size, hidden_size)
        self.k_linear = nn.Linear(hidden_size, hidden_size)
        self.v_linear = nn.Linear(hidden_size, hidden_size)
        self.out_linear = nn.Linear(hidden_size, hidden_size)
        
        # Logical operators
        self.logical_operators = nn.Parameter(torch.randn(4, hidden_size))  # AND, OR, NOT, IMPLIES
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Apply logical attention."""
        batch_size, seq_len, hidden_size = x.shape
        
        # Compute Q, K, V
        q = self.q_linear(x).view(batch_size, seq_len, self.num_heads, self.head_dim)
        k = self.k_linear(x).view(batch_size, seq_len, self.num_heads, self.head_dim)
        v = self.v_linear(x).view(batch_size, seq_len, self.num_heads, self.head_dim)
        
        # Compute attention scores
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        # Apply logical constraints
        scores = self._apply_logical_constraints(scores)
        
        # Apply mask
        if mask is not None:
            scores = scores.masked_fill(mask.unsqueeze(1).unsqueeze(2), float('-inf'))
        
        # Softmax
        attn_weights = F.softmax(scores, dim=-1)
        
        # Apply attention
        out = torch.matmul(attn_weights, v)
        out = out.view(batch_size, seq_len, hidden_size)
        
        return self.out_linear(out)
    
    def _apply_logical_constraints(self, scores: torch.Tensor) -> torch.Tensor:
        """Apply logical constraints to attention scores."""
        # This is a simplified logical constraint application
        # In practice, you would implement more sophisticated logical reasoning
        return scores

class CausalReasoningLayer(nn.Module):
    """Causal reasoning layer."""
    
    def __init__(self, hidden_size: int):
        super().__init__()
        self.hidden_size = hidden_size
        
        # Causal attention
        self.causal_attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=8,
            batch_first=True
        )
        
        # Causal projection
        self.causal_projection = nn.Linear(hidden_size, hidden_size)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply causal reasoning."""
        # Apply causal attention (causal mask)
        causal_output, _ = self.causal_attention(x, x, x)
        
        # Apply causal projection
        output = self.causal_projection(causal_output)
        
        return output

class DeductiveReasoningLayer(nn.Module):
    """Deductive reasoning layer."""
    
    def __init__(self, hidden_size: int):
        super().__init__()
        self.hidden_size = hidden_size
        
        # Deductive reasoning network
        self.deductive_net = nn.Sequential(
            nn.Linear(hidden_size, hidden_size * 2),
            nn.GELU(),
            nn.Linear(hidden_size * 2, hidden_size)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply deductive reasoning."""
        return self.deductive_net(x)

class InductiveReasoningLayer(nn.Module):
    """Inductive reasoning layer."""
    
    def __init__(self, hidden_size: int):
        super().__init__()
        self.hidden_size = hidden_size
        
        # Inductive reasoning network
        self.inductive_net = nn.Sequential(
            nn.Linear(hidden_size, hidden_size * 2),
            nn.GELU(),
            nn.Linear(hidden_size * 2, hidden_size)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply inductive reasoning."""
        return self.inductive_net(x)

class AbductiveReasoningLayer(nn.Module):
    """Abductive reasoning layer."""
    
    def __init__(self, hidden_size: int):
        super().__init__()
        self.hidden_size = hidden_size
        
        # Abductive reasoning network
        self.abductive_net = nn.Sequential(
            nn.Linear(hidden_size, hidden_size * 2),
            nn.GELU(),
            nn.Linear(hidden_size * 2, hidden_size)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply abductive reasoning."""
        return self.abductive_net(x)

class StepByStepReasoningLayer(nn.Module):
    """Step-by-step reasoning layer."""
    
    def __init__(self, hidden_size: int, max_steps: int):
        super().__init__()
        self.hidden_size = hidden_size
        self.max_steps = max_steps
        
        # Step reasoning network
        self.step_net = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.GELU(),
            nn.Linear(hidden_size, hidden_size)
        )
        
        # Step confidence network
        self.confidence_net = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self, 
        x: torch.Tensor, 
        mask: Optional[torch.Tensor] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[torch.Tensor, float]:
        """Apply step-by-step reasoning."""
        current_x = x
        total_confidence = 0.0
        
        for step in range(self.max_steps):
            # Apply step reasoning
            step_output = self.step_net(current_x)
            
            # Compute step confidence
            step_confidence = self.confidence_net(step_output).mean().item()
            total_confidence += step_confidence
            
            # Update current state
            current_x = step_output
            
            # Early stopping if confidence is high enough
            if step_confidence > 0.9:
                break
        
        # Average confidence
        avg_confidence = total_confidence / max(1, step + 1)
        
        return current_x, avg_confidence




