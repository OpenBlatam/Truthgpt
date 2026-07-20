"""
Advanced Multi-Modal AI Module for PiMoE System
Implements cross-modal understanding and fusion capabilities
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
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
class MultiModalInput:
    """Multi-modal input representation"""
    text: Optional[torch.Tensor] = None
    image: Optional[torch.Tensor] = None
    audio: Optional[torch.Tensor] = None
    video: Optional[torch.Tensor] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class CrossModalAlignment:
    """Cross-modal alignment representation"""
    alignment_scores: torch.Tensor
    attention_weights: torch.Tensor
    fusion_weights: torch.Tensor
    modality_importance: Dict[str, float]

@dataclass
class MultiModalOutput:
    """Multi-modal output representation"""
    fused_representation: torch.Tensor
    modality_specific_outputs: Dict[str, torch.Tensor]
    cross_modal_attention: torch.Tensor
    confidence_scores: Dict[str, float]

class TextEncoder(nn.Module):
    """Advanced Text Encoder"""
    
    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int, num_layers: int = 6):
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Text embedding
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.positional_encoding = nn.Parameter(torch.randn(1000, embed_dim))
        
        # Transformer layers
        self.transformer_layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=embed_dim,
                nhead=8,
                dim_feedforward=hidden_dim,
                dropout=0.1,
                batch_first=True
            )
            for _ in range(num_layers)
        ])
        
        # Output projection
        self.output_projection = nn.Linear(embed_dim, hidden_dim)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize model weights"""
        nn.init.normal_(self.embedding.weight, mean=0, std=0.02)
        nn.init.normal_(self.positional_encoding, mean=0, std=0.02)
    
    def forward(self, text_tokens: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Forward pass through text encoder"""
        batch_size, seq_len = text_tokens.size()
        
        # Embed tokens
        embedded = self.embedding(text_tokens)
        
        # Add positional encoding
        if seq_len <= self.positional_encoding.size(0):
            embedded = embedded + self.positional_encoding[:seq_len].unsqueeze(0)
        
        # Apply transformer layers
        for layer in self.transformer_layers:
            embedded = layer(embedded, src_key_padding_mask=attention_mask)
        
        # Project to hidden dimension
        output = self.output_projection(embedded)
        
        return output

class ImageEncoder(nn.Module):
    """Advanced Image Encoder"""
    
    def __init__(self, input_channels: int = 3, hidden_dim: int = 512, num_layers: int = 6):
        super().__init__()
        self.input_channels = input_channels
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Convolutional layers
        self.conv_layers = nn.ModuleList([
            nn.Conv2d(input_channels, 64, kernel_size=7, stride=2, padding=3),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.Conv2d(256, 512, kernel_size=3, stride=2, padding=1),
        ])
        
        # Batch normalization
        self.batch_norms = nn.ModuleList([
            nn.BatchNorm2d(64),
            nn.BatchNorm2d(128),
            nn.BatchNorm2d(256),
            nn.BatchNorm2d(512),
        ])
        
        # Activation
        self.activation = nn.ReLU(inplace=True)
        
        # Global average pooling
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Projection to hidden dimension
        self.projection = nn.Linear(512, hidden_dim)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize model weights"""
        for layer in self.conv_layers:
            nn.init.kaiming_normal_(layer.weight, mode='fan_out', nonlinearity='relu')
            nn.init.constant_(layer.bias, 0)
        
        for bn in self.batch_norms:
            nn.init.constant_(bn.weight, 1)
            nn.init.constant_(bn.bias, 0)
    
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """Forward pass through image encoder"""
        x = images
        
        # Apply convolutional layers
        for conv, bn in zip(self.conv_layers, self.batch_norms):
            x = conv(x)
            x = bn(x)
            x = self.activation(x)
        
        # Global average pooling
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        
        # Project to hidden dimension
        output = self.projection(x)
        
        return output

class AudioEncoder(nn.Module):
    """Advanced Audio Encoder"""
    
    def __init__(self, input_dim: int = 80, hidden_dim: int = 512, num_layers: int = 6):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Convolutional layers for audio
        self.conv_layers = nn.ModuleList([
            nn.Conv1d(input_dim, 128, kernel_size=3, padding=1),
            nn.Conv1d(128, 256, kernel_size=3, padding=1),
            nn.Conv1d(256, 512, kernel_size=3, padding=1),
        ])
        
        # Batch normalization
        self.batch_norms = nn.ModuleList([
            nn.BatchNorm1d(128),
            nn.BatchNorm1d(256),
            nn.BatchNorm1d(512),
        ])
        
        # Activation
        self.activation = nn.ReLU(inplace=True)
        
        # LSTM layers
        self.lstm = nn.LSTM(512, hidden_dim, num_layers, batch_first=True, bidirectional=True)
        
        # Projection
        self.projection = nn.Linear(hidden_dim * 2, hidden_dim)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize model weights"""
        for layer in self.conv_layers:
            nn.init.kaiming_normal_(layer.weight, mode='fan_out', nonlinearity='relu')
            nn.init.constant_(layer.bias, 0)
        
        for bn in self.batch_norms:
            nn.init.constant_(bn.weight, 1)
            nn.init.constant_(bn.bias, 0)
    
    def forward(self, audio_features: torch.Tensor) -> torch.Tensor:
        """Forward pass through audio encoder"""
        x = audio_features
        
        # Apply convolutional layers
        for conv, bn in zip(self.conv_layers, self.batch_norms):
            x = conv(x)
            x = bn(x)
            x = self.activation(x)
        
        # Transpose for LSTM
        x = x.transpose(1, 2)
        
        # Apply LSTM
        lstm_out, _ = self.lstm(x)
        
        # Project to hidden dimension
        output = self.projection(lstm_out)
        
        return output

class VideoEncoder(nn.Module):
    """Advanced Video Encoder"""
    
    def __init__(self, input_channels: int = 3, hidden_dim: int = 512, num_layers: int = 6):
        super().__init__()
        self.input_channels = input_channels
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # 3D Convolutional layers
        self.conv3d_layers = nn.ModuleList([
            nn.Conv3d(input_channels, 64, kernel_size=(3, 7, 7), stride=(1, 2, 2), padding=(1, 3, 3)),
            nn.Conv3d(64, 128, kernel_size=(3, 3, 3), stride=(1, 2, 2), padding=(1, 1, 1)),
            nn.Conv3d(128, 256, kernel_size=(3, 3, 3), stride=(1, 2, 2), padding=(1, 1, 1)),
            nn.Conv3d(256, 512, kernel_size=(3, 3, 3), stride=(1, 2, 2), padding=(1, 1, 1)),
        ])
        
        # Batch normalization
        self.batch_norms = nn.ModuleList([
            nn.BatchNorm3d(64),
            nn.BatchNorm3d(128),
            nn.BatchNorm3d(256),
            nn.BatchNorm3d(512),
        ])
        
        # Activation
        self.activation = nn.ReLU(inplace=True)
        
        # Global average pooling
        self.global_pool = nn.AdaptiveAvgPool3d((1, 1, 1))
        
        # Projection to hidden dimension
        self.projection = nn.Linear(512, hidden_dim)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize model weights"""
        for layer in self.conv3d_layers:
            nn.init.kaiming_normal_(layer.weight, mode='fan_out', nonlinearity='relu')
            nn.init.constant_(layer.bias, 0)
        
        for bn in self.batch_norms:
            nn.init.constant_(bn.weight, 1)
            nn.init.constant_(bn.bias, 0)
    
    def forward(self, video_frames: torch.Tensor) -> torch.Tensor:
        """Forward pass through video encoder"""
        x = video_frames
        
        # Apply 3D convolutional layers
        for conv, bn in zip(self.conv3d_layers, self.batch_norms):
            x = conv(x)
            x = bn(x)
            x = self.activation(x)
        
        # Global average pooling
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        
        # Project to hidden dimension
        output = self.projection(x)
        
        return output

class CrossModalAttention(nn.Module):
    """Cross-Modal Attention Mechanism"""
    
    def __init__(self, hidden_dim: int, num_heads: int = 8):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        
        # Multi-head attention
        self.multihead_attn = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            batch_first=True
        )
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(hidden_dim)
        
        # Feed-forward network
        self.feed_forward = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.ReLU(),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(0.1)
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize model weights"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.constant_(module.bias, 0)
    
    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor) -> torch.Tensor:
        """Forward pass through cross-modal attention"""
        # Multi-head attention
        attn_output, attn_weights = self.multihead_attn(query, key, value)
        
        # Residual connection and layer normalization
        output = self.layer_norm(attn_output + query)
        
        # Feed-forward network
        ff_output = self.feed_forward(output)
        
        # Residual connection and layer normalization
        output = self.layer_norm(ff_output + output)
        
        return output

class MultiModalFusion(nn.Module):
    """Multi-Modal Fusion Network"""
    
    def __init__(self, hidden_dim: int, num_modalities: int = 4):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_modalities = num_modalities
        
        # Cross-modal attention layers
        self.cross_modal_attention = nn.ModuleList([
            CrossModalAttention(hidden_dim)
            for _ in range(num_modalities)
        ])
        
        # Fusion weights
        self.fusion_weights = nn.Parameter(torch.ones(num_modalities))
        
        # Fusion network
        self.fusion_network = nn.Sequential(
            nn.Linear(hidden_dim * num_modalities, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.LayerNorm(hidden_dim)
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize model weights"""
        nn.init.constant_(self.fusion_weights, 1.0 / self.num_modalities)
        
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.constant_(module.bias, 0)
    
    def forward(self, modality_embeddings: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Forward pass through multi-modal fusion"""
        # Get modality names and embeddings
        modality_names = list(modality_embeddings.keys())
        embeddings = list(modality_embeddings.values())
        
        # Apply cross-modal attention
        attended_embeddings = []
        for i, embedding in enumerate(embeddings):
            # Use other modalities as key and value
            other_embeddings = [emb for j, emb in enumerate(embeddings) if j != i]
            if other_embeddings:
                key_value = torch.cat(other_embeddings, dim=1)
                attended = self.cross_modal_attention[i](embedding, key_value, key_value)
            else:
                attended = embedding
            attended_embeddings.append(attended)
        
        # Apply fusion weights
        weighted_embeddings = []
        for i, embedding in enumerate(attended_embeddings):
            weighted = embedding * self.fusion_weights[i]
            weighted_embeddings.append(weighted)
        
        # Concatenate embeddings
        concatenated = torch.cat(weighted_embeddings, dim=-1)
        
        # Apply fusion network
        fused_output = self.fusion_network(concatenated)
        
        return fused_output

class MultiModalPiMoE(nn.Module):
    """Multi-Modal PiMoE System"""
    
    def __init__(self, 
                 text_vocab_size: int = 30000,
                 hidden_dim: int = 512,
                 num_experts: int = 8,
                 expert_capacity: int = 1000):
        super().__init__()
        self.text_vocab_size = text_vocab_size
        self.hidden_dim = hidden_dim
        self.num_experts = num_experts
        self.expert_capacity = expert_capacity
        
        # Modality encoders
        self.text_encoder = TextEncoder(text_vocab_size, hidden_dim, hidden_dim)
        self.image_encoder = ImageEncoder(3, hidden_dim)
        self.audio_encoder = AudioEncoder(80, hidden_dim)
        self.video_encoder = VideoEncoder(3, hidden_dim)
        
        # Multi-modal fusion
        self.multi_modal_fusion = MultiModalFusion(hidden_dim, 4)
        
        # Expert networks
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim * 2),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden_dim * 2, hidden_dim),
                nn.LayerNorm(hidden_dim)
            )
            for _ in range(num_experts)
        ])
        
        # Router
        self.router = nn.Linear(hidden_dim, num_experts)
        
        # Load balancer
        self.load_balancer = nn.Linear(num_experts, num_experts)
        
        # Gating network
        self.gating = nn.Linear(hidden_dim, num_experts)
        
        # Output projection
        self.output_projection = nn.Linear(hidden_dim, hidden_dim)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize model weights"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.constant_(module.bias, 0)
    
    def forward(self, multi_modal_input: MultiModalInput) -> MultiModalOutput:
        """Forward pass through multi-modal PiMoE"""
        modality_embeddings = {}
        
        # Encode each modality
        if multi_modal_input.text is not None:
            text_embedding = self.text_encoder(multi_modal_input.text)
            modality_embeddings['text'] = text_embedding
        
        if multi_modal_input.image is not None:
            image_embedding = self.image_encoder(multi_modal_input.image)
            modality_embeddings['image'] = image_embedding
        
        if multi_modal_input.audio is not None:
            audio_embedding = self.audio_encoder(multi_modal_input.audio)
            modality_embeddings['audio'] = audio_embedding
        
        if multi_modal_input.video is not None:
            video_embedding = self.video_encoder(multi_modal_input.video)
            modality_embeddings['video'] = video_embedding
        
        # Multi-modal fusion
        fused_representation = self.multi_modal_fusion(modality_embeddings)
        
        # Router
        routing_scores = self.router(fused_representation)
        routing_scores = torch.softmax(routing_scores, dim=-1)
        
        # Load balancer
        balanced_scores = self.load_balancer(routing_scores)
        balanced_scores = torch.softmax(balanced_scores, dim=-1)
        
        # Gating
        gates = self.gating(fused_representation)
        gates = torch.softmax(gates, dim=-1)
        
        # Apply gates to routing scores
        gated_scores = routing_scores * gates
        
        # Process through experts
        expert_outputs = []
        for expert in self.experts:
            expert_output = expert(fused_representation)
            expert_outputs.append(expert_output)
        
        # Stack expert outputs
        expert_outputs = torch.stack(expert_outputs, dim=1)
        
        # Apply gating to expert outputs
        gated_outputs = expert_outputs * gated_scores.unsqueeze(-1)
        
        # Aggregate expert outputs
        aggregated_output = torch.sum(gated_outputs, dim=1)
        
        # Output projection
        final_output = self.output_projection(aggregated_output)
        
        # Create output
        output = MultiModalOutput(
            fused_representation=final_output,
            modality_specific_outputs=modality_embeddings,
            cross_modal_attention=gated_scores,
            confidence_scores={
                'text': 0.9 if 'text' in modality_embeddings else 0.0,
                'image': 0.9 if 'image' in modality_embeddings else 0.0,
                'audio': 0.9 if 'audio' in modality_embeddings else 0.0,
                'video': 0.9 if 'video' in modality_embeddings else 0.0
            }
        )
        
        return output

class MultiModalPiMoEDemo:
    """Multi-Modal PiMoE Demo"""
    
    def __init__(self):
        self.model = None
        self.performance_metrics = {}
        
        # Initialize demo
        self._initialize_demo()
    
    def _initialize_demo(self):
        """Initialize multi-modal PiMoE demo"""
        logger.info("Initializing Multi-Modal PiMoE Demo...")
        
        # Create multi-modal PiMoE model
        self.model = MultiModalPiMoE(
            text_vocab_size=30000,
            hidden_dim=512,
            num_experts=8,
            expert_capacity=1000
        )
        
        logger.info("Multi-Modal PiMoE Demo initialized successfully!")
    
    def run_multi_modal_demo(self):
        """Run multi-modal PiMoE demo"""
        logger.info("Running Multi-Modal PiMoE Demo...")
        
        # Generate sample data
        batch_size = 16
        
        # Create sample multi-modal input
        sample_input = MultiModalInput(
            text=torch.randint(0, 30000, (batch_size, 128)),
            image=torch.randn(batch_size, 3, 224, 224),
            audio=torch.randn(batch_size, 80, 1000),
            video=torch.randn(batch_size, 3, 16, 224, 224)
        )
        
        # Run multi-modal PiMoE
        start_time = time.time()
        with torch.no_grad():
            output = self.model(sample_input)
        end_time = time.time()
        
        # Compute performance metrics
        inference_time = end_time - start_time
        throughput = batch_size / inference_time
        
        # Store performance metrics
        self.performance_metrics = {
            'inference_time': inference_time,
            'throughput': throughput,
            'output_shape': output.fused_representation.shape,
            'num_experts': self.model.num_experts,
            'hidden_dim': self.model.hidden_dim,
            'modalities': list(sample_input.__dict__.keys())
        }
        
        # Log results
        logger.info(f"Multi-Modal PiMoE Demo Results:")
        logger.info(f"  Inference Time: {inference_time:.4f} seconds")
        logger.info(f"  Throughput: {throughput:.2f} samples/second")
        logger.info(f"  Output Shape: {output.fused_representation.shape}")
        logger.info(f"  Number of Experts: {self.model.num_experts}")
        logger.info(f"  Hidden Dimension: {self.model.hidden_dim}")
        logger.info(f"  Modalities: {list(sample_input.__dict__.keys())}")
        
        return self.performance_metrics
    
    def run_cross_modal_demo(self):
        """Run cross-modal alignment demo"""
        logger.info("Running Cross-Modal Alignment Demo...")
        
        # Generate sample data
        batch_size = 16
        
        # Create sample multi-modal input
        sample_input = MultiModalInput(
            text=torch.randint(0, 30000, (batch_size, 128)),
            image=torch.randn(batch_size, 3, 224, 224)
        )
        
        # Run cross-modal alignment
        start_time = time.time()
        with torch.no_grad():
            output = self.model(sample_input)
        end_time = time.time()
        
        # Compute performance metrics
        alignment_time = end_time - start_time
        alignment_throughput = batch_size / alignment_time
        
        # Store performance metrics
        self.performance_metrics['cross_modal_alignment'] = {
            'alignment_time': alignment_time,
            'alignment_throughput': alignment_throughput,
            'cross_modal_attention_shape': output.cross_modal_attention.shape,
            'confidence_scores': output.confidence_scores
        }
        
        logger.info(f"Cross-Modal Alignment Demo Results:")
        logger.info(f"  Alignment Time: {alignment_time:.4f} seconds")
        logger.info(f"  Alignment Throughput: {alignment_throughput:.2f} samples/second")
        logger.info(f"  Cross-Modal Attention Shape: {output.cross_modal_attention.shape}")
        logger.info(f"  Confidence Scores: {output.confidence_scores}")
        
        return self.performance_metrics
    
    def run_modality_specific_demo(self):
        """Run modality-specific processing demo"""
        logger.info("Running Modality-Specific Processing Demo...")
        
        # Generate sample data
        batch_size = 16
        
        # Test each modality individually
        modalities = ['text', 'image', 'audio', 'video']
        modality_results = {}
        
        for modality in modalities:
            # Create sample input for specific modality
            if modality == 'text':
                sample_input = MultiModalInput(text=torch.randint(0, 30000, (batch_size, 128)))
            elif modality == 'image':
                sample_input = MultiModalInput(image=torch.randn(batch_size, 3, 224, 224))
            elif modality == 'audio':
                sample_input = MultiModalInput(audio=torch.randn(batch_size, 80, 1000))
            elif modality == 'video':
                sample_input = MultiModalInput(video=torch.randn(batch_size, 3, 16, 224, 224))
            
            # Run modality-specific processing
            start_time = time.time()
            with torch.no_grad():
                output = self.model(sample_input)
            end_time = time.time()
            
            # Compute performance metrics
            modality_time = end_time - start_time
            modality_throughput = batch_size / modality_time
            
            # Store results
            modality_results[modality] = {
                'processing_time': modality_time,
                'throughput': modality_throughput,
                'output_shape': output.fused_representation.shape,
                'confidence': output.confidence_scores[modality]
            }
            
            logger.info(f"{modality.capitalize()} Processing Results:")
            logger.info(f"  Processing Time: {modality_time:.4f} seconds")
            logger.info(f"  Throughput: {modality_throughput:.2f} samples/second")
            logger.info(f"  Output Shape: {output.fused_representation.shape}")
            logger.info(f"  Confidence: {output.confidence_scores[modality]}")
        
        # Store modality results
        self.performance_metrics['modality_specific'] = modality_results
        
        return self.performance_metrics
    
    def run_comprehensive_multi_modal_demo(self):
        """Run comprehensive multi-modal demo"""
        logger.info("Running Comprehensive Multi-Modal Demo...")
        
        # Run all demos
        self.run_multi_modal_demo()
        self.run_cross_modal_demo()
        self.run_modality_specific_demo()
        
        # Compute overall performance
        overall_performance = self._compute_overall_performance()
        
        logger.info("Comprehensive Multi-Modal Demo completed successfully!")
        return overall_performance
    
    def _compute_overall_performance(self) -> Dict[str, Any]:
        """Compute overall performance metrics"""
        overall_performance = {
            'multi_modal_pimoe': self.performance_metrics.get('inference_time', 0),
            'cross_modal_alignment': self.performance_metrics.get('cross_modal_alignment', {}).get('alignment_time', 0),
            'modality_specific': self.performance_metrics.get('modality_specific', {}),
            'total_experts': self.model.num_experts,
            'hidden_dim': self.model.hidden_dim,
            'supported_modalities': ['text', 'image', 'audio', 'video']
        }
        
        return overall_performance

def main():
    """Main function to run multi-modal PiMoE demo"""
    try:
        # Create multi-modal PiMoE demo
        demo = MultiModalPiMoEDemo()
        
        # Run comprehensive demo
        performance = demo.run_comprehensive_multi_modal_demo()
        
        logger.info("Multi-Modal PiMoE Demo completed successfully!")
        logger.info(f"Overall Performance: {performance}")
        
    except Exception as e:
        logger.error(f"Error running multi-modal PiMoE demo: {e}")
        raise

if __name__ == "__main__":
    main()

