"""
Advanced Neural Network Adversarial Learning System for TruthGPT Optimization Core
Complete adversarial learning with attack generation, defense strategies, and robustness analysis
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
import logging
from dataclasses import dataclass, field
from enum import Enum
import time
import json
from pathlib import Path
import pickle
from abc import ABC, abstractmethod
import math
import random
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class AdversarialAttackType(Enum):
    """Adversarial attack types"""
    FGSM = "fgsm"
    PGD = "pgd"
    C_W = "c_w"
    DEEPFOOL = "deepfool"
    BIM = "bim"
    MIM = "mim"
    JSMA = "jsma"
    CWL2 = "cwl2"
    CWL0 = "cwl0"
    CWLINF = "cwlinf"

class GANType(Enum):
    """GAN types"""
    VANILLA_GAN = "vanilla_gan"
    DCGAN = "dcgan"
    WGAN = "wgan"
    WGAN_GP = "wgan_gp"
    LSGAN = "lsgan"
    BEGAN = "began"
    PROGRESSIVE_GAN = "progressive_gan"
    STYLEGAN = "stylegan"

class DefenseStrategy(Enum):
    """Defense strategies"""
    ADVERSARIAL_TRAINING = "adversarial_training"
    DISTILLATION = "distillation"
    DETECTION = "detection"
    INPUT_TRANSFORMATION = "input_transformation"
    CERTIFIED_DEFENSE = "certified_defense"
    RANDOMIZATION = "randomization"
    ENSEMBLE_DEFENSE = "ensemble_defense"

class AdversarialConfig:
    """Configuration for adversarial learning system"""
    # Basic settings
    attack_type: AdversarialAttackType = AdversarialAttackType.FGSM
    gan_type: GANType = GANType.VANILLA_GAN
    defense_strategy: DefenseStrategy = DefenseStrategy.ADVERSARIAL_TRAINING
    
    # Attack settings
    attack_epsilon: float = 0.1
    attack_alpha: float = 0.01
    attack_iterations: int = 10
    attack_norm: str = "inf"
    attack_targeted: bool = False
    
    # GAN settings
    generator_lr: float = 0.0002
    discriminator_lr: float = 0.0002
    gan_beta1: float = 0.5
    gan_beta2: float = 0.999
    gan_latent_dim: int = 100
    
    # Defense settings
    defense_epsilon: float = 0.1
    defense_alpha: float = 0.01
    defense_iterations: int = 10
    defense_norm: str = "inf"
    
    # Training settings
    batch_size: int = 64
    num_epochs: int = 100
    learning_rate: float = 0.001
    
    # Advanced features
    enable_robustness_analysis: bool = True
    enable_attack_generation: bool = True
    enable_defense_training: bool = True
    enable_adversarial_training: bool = True
    
    def __post_init__(self):
        """Validate adversarial configuration"""
        if self.attack_epsilon <= 0:
            raise ValueError("Attack epsilon must be positive")
        if self.attack_alpha <= 0:
            raise ValueError("Attack alpha must be positive")
        if self.attack_iterations <= 0:
            raise ValueError("Attack iterations must be positive")
        if self.generator_lr <= 0:
            raise ValueError("Generator learning rate must be positive")
        if self.discriminator_lr <= 0:
            raise ValueError("Discriminator learning rate must be positive")
        if self.gan_latent_dim <= 0:
            raise ValueError("GAN latent dimension must be positive")
        if self.defense_epsilon <= 0:
            raise ValueError("Defense epsilon must be positive")
        if self.defense_alpha <= 0:
            raise ValueError("Defense alpha must be positive")
        if self.defense_iterations <= 0:
            raise ValueError("Defense iterations must be positive")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        if self.num_epochs <= 0:
            raise ValueError("Number of epochs must be positive")
        if self.learning_rate <= 0:
            raise ValueError("Learning rate must be positive")

class AdversarialAttacker:
    """Adversarial attack generator"""
    
    def __init__(self, config: AdversarialConfig):
        self.config = config
        self.attack_history = []
        logger.info("✅ Adversarial Attacker initialized")
    
    def generate_attack(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Generate adversarial attack"""
        logger.info(f"🎯 Generating {self.config.attack_type.value} attack")
        
        if self.config.attack_type == AdversarialAttackType.FGSM:
            adversarial_x = self._fgsm_attack(model, x, y)
        elif self.config.attack_type == AdversarialAttackType.PGD:
            adversarial_x = self._pgd_attack(model, x, y)
        elif self.config.attack_type == AdversarialAttackType.C_W:
            adversarial_x = self._cw_attack(model, x, y)
        elif self.config.attack_type == AdversarialAttackType.DEEPFOOL:
            adversarial_x = self._deepfool_attack(model, x, y)
        elif self.config.attack_type == AdversarialAttackType.BIM:
            adversarial_x = self._bim_attack(model, x, y)
        elif self.config.attack_type == AdversarialAttackType.MIM:
            adversarial_x = self._mim_attack(model, x, y)
        else:
            adversarial_x = self._fgsm_attack(model, x, y)
        
        # Store attack history
        self.attack_history.append({
            'attack_type': self.config.attack_type.value,
            'original_x': x,
            'adversarial_x': adversarial_x,
            'perturbation': adversarial_x - x,
            'epsilon': self.config.attack_epsilon
        })
        
        return adversarial_x
    
    def _fgsm_attack(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Fast Gradient Sign Method attack"""
        logger.info("⚡ Generating FGSM attack")
        
        x.requires_grad_(True)
        
        # Forward pass
        output = model(x)
        loss = F.cross_entropy(output, y)
        
        # Backward pass
        model.zero_grad()
        loss.backward()
        
        # Generate adversarial example
        adversarial_x = x + self.config.attack_epsilon * x.grad.sign()
        
        # Clip to valid range
        adversarial_x = torch.clamp(adversarial_x, 0, 1)
        
        return adversarial_x.detach()
    
    def _pgd_attack(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Projected Gradient Descent attack"""
        logger.info("🎯 Generating PGD attack")
        
        adversarial_x = x.clone()
        
        for i in range(self.config.attack_iterations):
            adversarial_x.requires_grad_(True)
            
            # Forward pass
            output = model(adversarial_x)
            loss = F.cross_entropy(output, y)
            
            # Backward pass
            model.zero_grad()
            loss.backward()
            
            # Update adversarial example
            adversarial_x = adversarial_x + self.config.attack_alpha * adversarial_x.grad.sign()
            
            # Project to epsilon ball
            perturbation = adversarial_x - x
            if self.config.attack_norm == "inf":
                perturbation = torch.clamp(perturbation, -self.config.attack_epsilon, self.config.attack_epsilon)
            elif self.config.attack_norm == "2":
                perturbation = perturbation * min(1, self.config.attack_epsilon / torch.norm(perturbation))
            
            adversarial_x = x + perturbation
            
            # Clip to valid range
            adversarial_x = torch.clamp(adversarial_x, 0, 1)
        
        return adversarial_x.detach()
    
    def _cw_attack(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Carlini & Wagner attack"""
        logger.info("🔧 Generating C&W attack")
        
        # Simplified C&W attack
        adversarial_x = x.clone()
        
        for i in range(self.config.attack_iterations):
            adversarial_x.requires_grad_(True)
            
            # Forward pass
            output = model(adversarial_x)
            loss = F.cross_entropy(output, y)
            
            # Backward pass
            model.zero_grad()
            loss.backward()
            
            # Update adversarial example
            adversarial_x = adversarial_x - self.config.attack_alpha * adversarial_x.grad
            
            # Clip to valid range
            adversarial_x = torch.clamp(adversarial_x, 0, 1)
        
        return adversarial_x.detach()
    
    def _deepfool_attack(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """DeepFool attack"""
        logger.info("🌀 Generating DeepFool attack")
        
        adversarial_x = x.clone()
        
        for i in range(self.config.attack_iterations):
            adversarial_x.requires_grad_(True)
            
            # Forward pass
            output = model(adversarial_x)
            
            # Get current prediction
            _, predicted = torch.max(output, 1)
            
            if predicted != y:
                break
            
            # Calculate gradients for all classes
            gradients = []
            for class_idx in range(output.shape[1]):
                if class_idx != y:
                    grad = torch.autograd.grad(output[0, class_idx], adversarial_x, 
                                             retain_graph=True, create_graph=True)[0]
                    gradients.append(grad)
            
            # Calculate perturbation
            if gradients:
                perturbation = self._calculate_deepfool_perturbation(gradients, output, y)
                adversarial_x = adversarial_x + perturbation
            
            # Clip to valid range
            adversarial_x = torch.clamp(adversarial_x, 0, 1)
        
        return adversarial_x.detach()
    
    def _calculate_deepfool_perturbation(self, gradients: List[torch.Tensor], 
                                       output: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Calculate DeepFool perturbation"""
        # Simplified DeepFool perturbation calculation
        perturbation = torch.zeros_like(gradients[0])
        
        for i, grad in enumerate(gradients):
            perturbation += grad / (torch.norm(grad) + 1e-8)
        
        perturbation = perturbation / len(gradients)
        
        return perturbation
    
    def _bim_attack(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Basic Iterative Method attack"""
        logger.info("🔄 Generating BIM attack")
        
        adversarial_x = x.clone()
        
        for i in range(self.config.attack_iterations):
            adversarial_x.requires_grad_(True)
            
            # Forward pass
            output = model(adversarial_x)
            loss = F.cross_entropy(output, y)
            
            # Backward pass
            model.zero_grad()
            loss.backward()
            
            # Update adversarial example
            adversarial_x = adversarial_x + self.config.attack_alpha * adversarial_x.grad.sign()
            
            # Clip to epsilon ball
            perturbation = adversarial_x - x
            perturbation = torch.clamp(perturbation, -self.config.attack_epsilon, self.config.attack_epsilon)
            adversarial_x = x + perturbation
            
            # Clip to valid range
            adversarial_x = torch.clamp(adversarial_x, 0, 1)
        
        return adversarial_x.detach()
    
    def _mim_attack(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Momentum Iterative Method attack"""
        logger.info("🌊 Generating MIM attack")
        
        adversarial_x = x.clone()
        momentum = torch.zeros_like(x)
        
        for i in range(self.config.attack_iterations):
            adversarial_x.requires_grad_(True)
            
            # Forward pass
            output = model(adversarial_x)
            loss = F.cross_entropy(output, y)
            
            # Backward pass
            model.zero_grad()
            loss.backward()
            
            # Update momentum
            momentum = 0.9 * momentum + adversarial_x.grad / torch.norm(adversarial_x.grad)
            
            # Update adversarial example
            adversarial_x = adversarial_x + self.config.attack_alpha * momentum.sign()
            
            # Clip to epsilon ball
            perturbation = adversarial_x - x
            perturbation = torch.clamp(perturbation, -self.config.attack_epsilon, self.config.attack_epsilon)
            adversarial_x = x + perturbation
            
            # Clip to valid range
            adversarial_x = torch.clamp(adversarial_x, 0, 1)
        
        return adversarial_x.detach()

class GANGenerator:
    """GAN Generator"""
    
    def __init__(self, config: AdversarialConfig):
        self.config = config
        self.generator = None
        self.generator_history = []
        logger.info("✅ GAN Generator initialized")
    
    def create_generator(self, input_dim: int, output_dim: int) -> nn.Module:
        """Create generator network"""
        logger.info(f"🏗️ Creating {self.config.gan_type.value} generator")
        
        if self.config.gan_type == GANType.VANILLA_GAN:
            generator = self._create_vanilla_generator(input_dim, output_dim)
        elif self.config.gan_type == GANType.DCGAN:
            generator = self._create_dcgan_generator(input_dim, output_dim)
        elif self.config.gan_type == GANType.WGAN:
            generator = self._create_wgan_generator(input_dim, output_dim)
        else:
            generator = self._create_vanilla_generator(input_dim, output_dim)
        
        self.generator = generator
        return generator
    
    def _create_vanilla_generator(self, input_dim: int, output_dim: int) -> nn.Module:
        """Create vanilla GAN generator"""
        return nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Linear(512, output_dim),
            nn.Tanh()
        )
    
    def _create_dcgan_generator(self, input_dim: int, output_dim: int) -> nn.Module:
        """Create DCGAN generator"""
        return nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Linear(512, output_dim),
            nn.Tanh()
        )
    
    def _create_wgan_generator(self, input_dim: int, output_dim: int) -> nn.Module:
        """Create WGAN generator"""
        return nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Linear(512, output_dim),
            nn.Tanh()
        )
    
    def generate_samples(self, n_samples: int) -> torch.Tensor:
        """Generate samples from generator"""
        if self.generator is None:
            raise ValueError("Generator must be created first")
        
        # Generate random noise
        noise = torch.randn(n_samples, self.config.gan_latent_dim)
        
        # Generate samples
        with torch.no_grad():
            samples = self.generator(noise)
        
        return samples

class GANDiscriminator:
    """GAN Discriminator"""
    
    def __init__(self, config: AdversarialConfig):
        self.config = config
        self.discriminator = None
        self.discriminator_history = []
        logger.info("✅ GAN Discriminator initialized")
    
    def create_discriminator(self, input_dim: int) -> nn.Module:
        """Create discriminator network"""
        logger.info(f"🏗️ Creating {self.config.gan_type.value} discriminator")
        
        if self.config.gan_type == GANType.VANILLA_GAN:
            discriminator = self._create_vanilla_discriminator(input_dim)
        elif self.config.gan_type == GANType.DCGAN:
            discriminator = self._create_dcgan_discriminator(input_dim)
        elif self.config.gan_type == GANType.WGAN:
            discriminator = self._create_wgan_discriminator(input_dim)
        else:
            discriminator = self._create_vanilla_discriminator(input_dim)
        
        self.discriminator = discriminator
        return discriminator
    
    def _create_vanilla_discriminator(self, input_dim: int) -> nn.Module:
        """Create vanilla GAN discriminator"""
        return nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.LeakyReLU(0.2),
            nn.Linear(512, 256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
    
    def _create_dcgan_discriminator(self, input_dim: int) -> nn.Module:
        """Create DCGAN discriminator"""
        return nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.LeakyReLU(0.2),
            nn.Linear(512, 256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
    
    def _create_wgan_discriminator(self, input_dim: int) -> nn.Module:
        """Create WGAN discriminator"""
        return nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.LeakyReLU(0.2),
            nn.Linear(512, 256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 1)
        )
    
    def discriminate(self, samples: torch.Tensor) -> torch.Tensor:
        """Discriminate samples"""
        if self.discriminator is None:
            raise ValueError("Discriminator must be created first")
        
        with torch.no_grad():
            predictions = self.discriminator(samples)
        
        return predictions

class GANTrainer:
    """GAN Trainer"""
    
    def __init__(self, config: AdversarialConfig):
        self.config = config
        self.generator = GANGenerator(config)
        self.discriminator = GANDiscriminator(config)
        self.training_history = []
        logger.info("✅ GAN Trainer initialized")
    
    def train_gan(self, real_data: torch.Tensor) -> Dict[str, Any]:
        """Train GAN"""
        logger.info(f"🚀 Training {self.config.gan_type.value} GAN")
        
        training_results = {
            'start_time': time.time(),
            'config': self.config,
            'epochs': []
        }
        
        # Create networks
        input_dim = real_data.shape[1]
        output_dim = real_data.shape[1]
        
        generator = self.generator.create_generator(self.config.gan_latent_dim, output_dim)
        discriminator = self.discriminator.create_discriminator(input_dim)
        
        # Create optimizers
        generator_optimizer = torch.optim.Adam(generator.parameters(), 
                                             lr=self.config.generator_lr, 
                                             betas=(self.config.gan_beta1, self.config.gan_beta2))
        discriminator_optimizer = torch.optim.Adam(discriminator.parameters(), 
                                                  lr=self.config.discriminator_lr, 
                                                  betas=(self.config.gan_beta1, self.config.gan_beta2))
        
        # Training loop
        for epoch in range(self.config.num_epochs):
            logger.info(f"🔄 Epoch {epoch + 1}/{self.config.num_epochs}")
            
            # Train discriminator
            d_loss = self._train_discriminator(discriminator, generator, real_data, discriminator_optimizer)
            
            # Train generator
            g_loss = self._train_generator(discriminator, generator, generator_optimizer)
            
            # Store epoch results
            epoch_result = {
                'epoch': epoch,
                'discriminator_loss': d_loss,
                'generator_loss': g_loss
            }
            
            training_results['epochs'].append(epoch_result)
            
            if epoch % 10 == 0:
                logger.info(f"   Epoch {epoch}: D Loss = {d_loss:.4f}, G Loss = {g_loss:.4f}")
        
        # Final evaluation
        training_results['end_time'] = time.time()
        training_results['total_duration'] = training_results['end_time'] - training_results['start_time']
        
        # Store results
        self.training_history.append(training_results)
        
        logger.info("✅ GAN training completed")
        return training_results
    
    def _train_discriminator(self, discriminator: nn.Module, generator: nn.Module, 
                           real_data: torch.Tensor, optimizer: torch.optim.Optimizer) -> float:
        """Train discriminator"""
        discriminator.train()
        
        # Real data
        real_labels = torch.ones(real_data.shape[0], 1)
        real_output = discriminator(real_data)
        real_loss = F.binary_cross_entropy(real_output, real_labels)
        
        # Fake data
        noise = torch.randn(real_data.shape[0], self.config.gan_latent_dim)
        fake_data = generator(noise)
        fake_labels = torch.zeros(fake_data.shape[0], 1)
        fake_output = discriminator(fake_data.detach())
        fake_loss = F.binary_cross_entropy(fake_output, fake_labels)
        
        # Total discriminator loss
        d_loss = real_loss + fake_loss
        
        # Backward pass
        optimizer.zero_grad()
        d_loss.backward()
        optimizer.step()
        
        return d_loss.item()
    
    def _train_generator(self, discriminator: nn.Module, generator: nn.Module, 
                       optimizer: torch.optim.Optimizer) -> float:
        """Train generator"""
        generator.train()
        
        # Generate fake data
        noise = torch.randn(self.config.batch_size, self.config.gan_latent_dim)
        fake_data = generator(noise)
        
        # Discriminator output
        fake_output = discriminator(fake_data)
        real_labels = torch.ones(fake_data.shape[0], 1)
        
        # Generator loss
        g_loss = F.binary_cross_entropy(fake_output, real_labels)
        
        # Backward pass
        optimizer.zero_grad()
        g_loss.backward()
        optimizer.step()
        
        return g_loss.item()

class AdversarialDefense:
    """Adversarial defense strategies"""
    
    def __init__(self, config: AdversarialConfig):
        self.config = config
        self.defense_history = []
        logger.info("✅ Adversarial Defense initialized")
    
    def apply_defense(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Apply defense strategy"""
        logger.info(f"🛡️ Applying {self.config.defense_strategy.value} defense")
        
        if self.config.defense_strategy == DefenseStrategy.ADVERSARIAL_TRAINING:
            defended_x = self._adversarial_training_defense(model, x, y)
        elif self.config.defense_strategy == DefenseStrategy.DISTILLATION:
            defended_x = self._distillation_defense(model, x, y)
        elif self.config.defense_strategy == DefenseStrategy.DETECTION:
            defended_x = self._detection_defense(model, x, y)
        elif self.config.defense_strategy == DefenseStrategy.INPUT_TRANSFORMATION:
            defended_x = self._input_transformation_defense(model, x, y)
        else:
            defended_x = self._adversarial_training_defense(model, x, y)
        
        # Store defense history
        self.defense_history.append({
            'defense_strategy': self.config.defense_strategy.value,
            'original_x': x,
            'defended_x': defended_x,
            'defense_applied': True
        })
        
        return defended_x
    
    def _adversarial_training_defense(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Adversarial training defense"""
        logger.info("🛡️ Applying adversarial training defense")
        
        # Generate adversarial examples
        attacker = AdversarialAttacker(self.config)
        adversarial_x = attacker.generate_attack(model, x, y)
        
        # Train on both clean and adversarial examples
        model.train()
        
        # Clean data loss
        clean_output = model(x)
        clean_loss = F.cross_entropy(clean_output, y)
        
        # Adversarial data loss
        adv_output = model(adversarial_x)
        adv_loss = F.cross_entropy(adv_output, y)
        
        # Combined loss
        total_loss = clean_loss + adv_loss
        
        # Backward pass
        model.zero_grad()
        total_loss.backward()
        
        return adversarial_x
    
    def _distillation_defense(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Distillation defense"""
        logger.info("🛡️ Applying distillation defense")
        
        # Create teacher model (original model)
        teacher_model = model
        
        # Create student model (defended model)
        student_model = type(model)()
        student_model.load_state_dict(model.state_dict())
        
        # Distillation training
        student_model.train()
        
        # Teacher predictions
        with torch.no_grad():
            teacher_output = teacher_model(x)
            teacher_probs = F.softmax(teacher_output, dim=1)
        
        # Student predictions
        student_output = student_model(x)
        student_probs = F.softmax(student_output, dim=1)
        
        # Distillation loss
        distillation_loss = F.kl_div(student_probs.log(), teacher_probs, reduction='batchmean')
        
        # Backward pass
        student_model.zero_grad()
        distillation_loss.backward()
        
        return x
    
    def _detection_defense(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Detection defense"""
        logger.info("🛡️ Applying detection defense")
        
        # Detect adversarial examples
        is_adversarial = self._detect_adversarial(model, x, y)
        
        if is_adversarial:
            # Apply defense
            defended_x = self._apply_detection_defense(x)
        else:
            defended_x = x
        
        return defended_x
    
    def _detect_adversarial(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> bool:
        """Detect adversarial examples"""
        # Simplified adversarial detection
        model.eval()
        
        with torch.no_grad():
            output = model(x)
            prediction = torch.argmax(output, dim=1)
            
            # Check if prediction matches label
            is_adversarial = (prediction != y).any().item()
        
        return is_adversarial
    
    def _apply_detection_defense(self, x: torch.Tensor) -> torch.Tensor:
        """Apply detection defense"""
        # Simplified detection defense
        defended_x = x + torch.randn_like(x) * 0.01
        defended_x = torch.clamp(defended_x, 0, 1)
        
        return defended_x
    
    def _input_transformation_defense(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Input transformation defense"""
        logger.info("🛡️ Applying input transformation defense")
        
        # Apply input transformations
        transformed_x = self._apply_input_transformations(x)
        
        return transformed_x
    
    def _apply_input_transformations(self, x: torch.Tensor) -> torch.Tensor:
        """Apply input transformations"""
        # Random rotation
        angle = torch.randn(1) * 0.1
        transformed_x = x + angle
        
        # Random noise
        noise = torch.randn_like(x) * 0.01
        transformed_x = transformed_x + noise
        
        # Clip to valid range
        transformed_x = torch.clamp(transformed_x, 0, 1)
        
        return transformed_x

class RobustnessAnalyzer:
    """Robustness analysis for adversarial learning"""
    
    def __init__(self, config: AdversarialConfig):
        self.config = config
        self.robustness_history = []
        logger.info("✅ Robustness Analyzer initialized")
    
    def analyze_robustness(self, model: nn.Module, test_data: torch.Tensor, 
                          test_labels: torch.Tensor) -> Dict[str, Any]:
        """Analyze model robustness"""
        logger.info("🔍 Analyzing model robustness")
        
        # Clean accuracy
        clean_accuracy = self._evaluate_accuracy(model, test_data, test_labels)
        
        # Adversarial accuracy
        attacker = AdversarialAttacker(self.config)
        adversarial_data = attacker.generate_attack(model, test_data, test_labels)
        adversarial_accuracy = self._evaluate_accuracy(model, adversarial_data, test_labels)
        
        # Robustness metrics
        robustness_metrics = {
            'clean_accuracy': clean_accuracy,
            'adversarial_accuracy': adversarial_accuracy,
            'robustness_gap': clean_accuracy - adversarial_accuracy,
            'robustness_ratio': adversarial_accuracy / clean_accuracy if clean_accuracy > 0 else 0
        }
        
        # Store robustness history
        self.robustness_history.append({
            'robustness_metrics': robustness_metrics,
            'attack_type': self.config.attack_type.value,
            'epsilon': self.config.attack_epsilon
        })
        
        return robustness_metrics
    
    def _evaluate_accuracy(self, model: nn.Module, data: torch.Tensor, labels: torch.Tensor) -> float:
        """Evaluate model accuracy"""
        model.eval()
        
        with torch.no_grad():
            output = model(data)
            predictions = torch.argmax(output, dim=1)
            accuracy = (predictions == labels).float().mean().item()
        
        return accuracy

class AdversarialLearningSystem:
    """Main adversarial learning system"""
    
    def __init__(self, config: AdversarialConfig):
        self.config = config
        
        # Components
        self.adversarial_attacker = AdversarialAttacker(config)
        self.gan_trainer = GANTrainer(config)
        self.adversarial_defense = AdversarialDefense(config)
        self.robustness_analyzer = RobustnessAnalyzer(config)
        
        # Adversarial learning state
        self.adversarial_learning_history = []
        
        logger.info("✅ Adversarial Learning System initialized")
    
    def run_adversarial_learning(self, model: nn.Module, train_data: torch.Tensor, 
                                train_labels: torch.Tensor, test_data: torch.Tensor, 
                                test_labels: torch.Tensor) -> Dict[str, Any]:
        """Run adversarial learning process"""
        logger.info(f"🚀 Running adversarial learning with attack: {self.config.attack_type.value}")
        
        adversarial_results = {
            'start_time': time.time(),
            'config': self.config,
            'stages': {}
        }
        
        # Stage 1: Attack Generation
        if self.config.enable_attack_generation:
            logger.info("🎯 Stage 1: Attack Generation")
            
            attack_result = self._generate_attacks(model, test_data, test_labels)
            
            adversarial_results['stages']['attack_generation'] = attack_result
        
        # Stage 2: GAN Training
        if self.config.gan_type != GANType.VANILLA_GAN:
            logger.info("🎨 Stage 2: GAN Training")
            
            gan_result = self.gan_trainer.train_gan(train_data)
            
            adversarial_results['stages']['gan_training'] = gan_result
        
        # Stage 3: Defense Training
        if self.config.enable_defense_training:
            logger.info("🛡️ Stage 3: Defense Training")
            
            defense_result = self._train_defense(model, train_data, train_labels)
            
            adversarial_results['stages']['defense_training'] = defense_result
        
        # Stage 4: Robustness Analysis
        if self.config.enable_robustness_analysis:
            logger.info("🔍 Stage 4: Robustness Analysis")
            
            robustness_result = self.robustness_analyzer.analyze_robustness(
                model, test_data, test_labels
            )
            
            adversarial_results['stages']['robustness_analysis'] = robustness_result
        
        # Final evaluation
        adversarial_results['end_time'] = time.time()
        adversarial_results['total_duration'] = adversarial_results['end_time'] - adversarial_results['start_time']
        
        # Store results
        self.adversarial_learning_history.append(adversarial_results)
        
        logger.info("✅ Adversarial learning completed")
        return adversarial_results
    
    def _generate_attacks(self, model: nn.Module, test_data: torch.Tensor, 
                         test_labels: torch.Tensor) -> Dict[str, Any]:
        """Generate adversarial attacks"""
        # Generate attacks on subset of test data
        n_samples = min(100, len(test_data))
        indices = torch.randperm(len(test_data))[:n_samples]
        
        subset_data = test_data[indices]
        subset_labels = test_labels[indices]
        
        # Generate adversarial examples
        adversarial_data = self.adversarial_attacker.generate_attack(model, subset_data, subset_labels)
        
        attack_result = {
            'n_samples': n_samples,
            'attack_type': self.config.attack_type.value,
            'epsilon': self.config.attack_epsilon,
            'adversarial_data': adversarial_data,
            'status': 'success'
        }
        
        return attack_result
    
    def _train_defense(self, model: nn.Module, train_data: torch.Tensor, 
                      train_labels: torch.Tensor) -> Dict[str, Any]:
        """Train defense strategies"""
        # Apply defense on subset of training data
        n_samples = min(100, len(train_data))
        indices = torch.randperm(len(train_data))[:n_samples]
        
        subset_data = train_data[indices]
        subset_labels = train_labels[indices]
        
        # Apply defense
        defended_data = self.adversarial_defense.apply_defense(model, subset_data, subset_labels)
        
        defense_result = {
            'n_samples': n_samples,
            'defense_strategy': self.config.defense_strategy.value,
            'defended_data': defended_data,
            'status': 'success'
        }
        
        return defense_result
    
    def generate_adversarial_report(self, results: Dict[str, Any]) -> str:
        """Generate adversarial learning report"""
        report = []
        report.append("=" * 50)
        report.append("ADVERSARIAL LEARNING REPORT")
        report.append("=" * 50)
        
        # Configuration
        report.append("\nADVERSARIAL LEARNING CONFIGURATION:")
        report.append("-" * 35)
        report.append(f"Attack Type: {self.config.attack_type.value}")
        report.append(f"GAN Type: {self.config.gan_type.value}")
        report.append(f"Defense Strategy: {self.config.defense_strategy.value}")
        report.append(f"Attack Epsilon: {self.config.attack_epsilon}")
        report.append(f"Attack Alpha: {self.config.attack_alpha}")
        report.append(f"Attack Iterations: {self.config.attack_iterations}")
        report.append(f"Attack Norm: {self.config.attack_norm}")
        report.append(f"Attack Targeted: {'Enabled' if self.config.attack_targeted else 'Disabled'}")
        report.append(f"Generator Learning Rate: {self.config.generator_lr}")
        report.append(f"Discriminator Learning Rate: {self.config.discriminator_lr}")
        report.append(f"GAN Beta1: {self.config.gan_beta1}")
        report.append(f"GAN Beta2: {self.config.gan_beta2}")
        report.append(f"GAN Latent Dimension: {self.config.gan_latent_dim}")
        report.append(f"Defense Epsilon: {self.config.defense_epsilon}")
        report.append(f"Defense Alpha: {self.config.defense_alpha}")
        report.append(f"Defense Iterations: {self.config.defense_iterations}")
        report.append(f"Defense Norm: {self.config.defense_norm}")
        report.append(f"Batch Size: {self.config.batch_size}")
        report.append(f"Number of Epochs: {self.config.num_epochs}")
        report.append(f"Learning Rate: {self.config.learning_rate}")
        report.append(f"Robustness Analysis: {'Enabled' if self.config.enable_robustness_analysis else 'Disabled'}")
        report.append(f"Attack Generation: {'Enabled' if self.config.enable_attack_generation else 'Disabled'}")
        report.append(f"Defense Training: {'Enabled' if self.config.enable_defense_training else 'Disabled'}")
        report.append(f"Adversarial Training: {'Enabled' if self.config.enable_adversarial_training else 'Disabled'}")
        
        # Results
        report.append("\nADVERSARIAL LEARNING RESULTS:")
        report.append("-" * 30)
        report.append(f"Total Duration: {results.get('total_duration', 0):.2f} seconds")
        report.append(f"Start Time: {results.get('start_time', 'Unknown')}")
        report.append(f"End Time: {results.get('end_time', 'Unknown')}")
        
        # Stage results
        if 'stages' in results:
            for stage_name, stage_data in results['stages'].items():
                report.append(f"\n{stage_name.upper()}:")
                report.append("-" * len(stage_name))
                
                if isinstance(stage_data, dict):
                    for key, value in stage_data.items():
                        report.append(f"  {key}: {value}")
        
        return "\n".join(report)
    
    def visualize_adversarial_results(self, save_path: str = None):
        """Visualize adversarial learning results"""
        if not self.adversarial_learning_history:
            logger.warning("No adversarial learning history to visualize")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Adversarial learning duration over time
        durations = [r.get('total_duration', 0) for r in self.adversarial_learning_history]
        axes[0, 0].plot(durations, 'b-', linewidth=2)
        axes[0, 0].set_xlabel('Adversarial Learning Run')
        axes[0, 0].set_ylabel('Duration (seconds)')
        axes[0, 0].set_title('Adversarial Learning Duration Over Time')
        axes[0, 0].grid(True)
        
        # Plot 2: Attack type distribution
        attack_types = [self.config.attack_type.value]
        attack_counts = [1]
        
        axes[0, 1].pie(attack_counts, labels=attack_types, autopct='%1.1f%%')
        axes[0, 1].set_title('Attack Type Distribution')
        
        # Plot 3: GAN type distribution
        gan_types = [self.config.gan_type.value]
        gan_counts = [1]
        
        axes[1, 0].pie(gan_counts, labels=gan_types, autopct='%1.1f%%')
        axes[1, 0].set_title('GAN Type Distribution')
        
        # Plot 4: Adversarial configuration
        config_values = [
            self.config.attack_epsilon,
            self.config.attack_iterations,
            self.config.gan_latent_dim,
            self.config.batch_size
        ]
        config_labels = ['Attack Epsilon', 'Attack Iterations', 'GAN Latent Dim', 'Batch Size']
        
        axes[1, 1].bar(config_labels, config_values, color=['blue', 'green', 'orange', 'red'])
        axes[1, 1].set_ylabel('Value')
        axes[1, 1].set_title('Adversarial Configuration')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close()

# Factory functions
def create_adversarial_config(**kwargs) -> AdversarialConfig:
    """Create adversarial configuration"""
    return AdversarialConfig(**kwargs)

def create_adversarial_attacker(config: AdversarialConfig) -> AdversarialAttacker:
    """Create adversarial attacker"""
    return AdversarialAttacker(config)

def create_gan_generator(config: AdversarialConfig) -> GANGenerator:
    """Create GAN generator"""
    return GANGenerator(config)

def create_gan_discriminator(config: AdversarialConfig) -> GANDiscriminator:
    """Create GAN discriminator"""
    return GANDiscriminator(config)

def create_gan_trainer(config: AdversarialConfig) -> GANTrainer:
    """Create GAN trainer"""
    return GANTrainer(config)

def create_adversarial_defense(config: AdversarialConfig) -> AdversarialDefense:
    """Create adversarial defense"""
    return AdversarialDefense(config)

def create_robustness_analyzer(config: AdversarialConfig) -> RobustnessAnalyzer:
    """Create robustness analyzer"""
    return RobustnessAnalyzer(config)

def create_adversarial_learning_system(config: AdversarialConfig) -> AdversarialLearningSystem:
    """Create adversarial learning system"""
    return AdversarialLearningSystem(config)

# Example usage
def example_adversarial_learning():
    """Example of adversarial learning system"""
    # Create configuration
    config = create_adversarial_config(
        attack_type=AdversarialAttackType.FGSM,
        gan_type=GANType.VANILLA_GAN,
        defense_strategy=DefenseStrategy.ADVERSARIAL_TRAINING,
        attack_epsilon=0.1,
        attack_alpha=0.01,
        attack_iterations=10,
        attack_norm="inf",
        attack_targeted=False,
        generator_lr=0.0002,
        discriminator_lr=0.0002,
        gan_beta1=0.5,
        gan_beta2=0.999,
        gan_latent_dim=100,
        defense_epsilon=0.1,
        defense_alpha=0.01,
        defense_iterations=10,
        defense_norm="inf",
        batch_size=64,
        num_epochs=100,
        learning_rate=0.001,
        enable_robustness_analysis=True,
        enable_attack_generation=True,
        enable_defense_training=True,
        enable_adversarial_training=True
    )
    
    # Create adversarial learning system
    adversarial_system = create_adversarial_learning_system(config)
    
    # Create dummy model and data
    model = nn.Sequential(
        nn.Linear(784, 256),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(256, 128),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(128, 10)
    )
    
    # Generate dummy data
    n_samples = 1000
    n_features = 784
    
    train_data = torch.randn(n_samples, n_features)
    train_labels = torch.randint(0, 10, (n_samples,))
    test_data = torch.randn(200, n_features)
    test_labels = torch.randint(0, 10, (200,))
    
    # Run adversarial learning
    adversarial_results = adversarial_system.run_adversarial_learning(
        model, train_data, train_labels, test_data, test_labels
    )
    
    # Generate report
    adversarial_report = adversarial_system.generate_adversarial_report(adversarial_results)
    
    print(f"✅ Adversarial Learning Example Complete!")
    print(f"🚀 Adversarial Learning Statistics:")
    print(f"   Attack Type: {config.attack_type.value}")
    print(f"   GAN Type: {config.gan_type.value}")
    print(f"   Defense Strategy: {config.defense_strategy.value}")
    print(f"   Attack Epsilon: {config.attack_epsilon}")
    print(f"   Attack Alpha: {config.attack_alpha}")
    print(f"   Attack Iterations: {config.attack_iterations}")
    print(f"   Attack Norm: {config.attack_norm}")
    print(f"   Attack Targeted: {'Enabled' if config.attack_targeted else 'Disabled'}")
    print(f"   Generator Learning Rate: {config.generator_lr}")
    print(f"   Discriminator Learning Rate: {config.discriminator_lr}")
    print(f"   GAN Beta1: {config.gan_beta1}")
    print(f"   GAN Beta2: {config.gan_beta2}")
    print(f"   GAN Latent Dimension: {config.gan_latent_dim}")
    print(f"   Defense Epsilon: {config.defense_epsilon}")
    print(f"   Defense Alpha: {config.defense_alpha}")
    print(f"   Defense Iterations: {config.defense_iterations}")
    print(f"   Defense Norm: {config.defense_norm}")
    print(f"   Batch Size: {config.batch_size}")
    print(f"   Number of Epochs: {config.num_epochs}")
    print(f"   Learning Rate: {config.learning_rate}")
    print(f"   Robustness Analysis: {'Enabled' if config.enable_robustness_analysis else 'Disabled'}")
    print(f"   Attack Generation: {'Enabled' if config.enable_attack_generation else 'Disabled'}")
    print(f"   Defense Training: {'Enabled' if config.enable_defense_training else 'Disabled'}")
    print(f"   Adversarial Training: {'Enabled' if config.enable_adversarial_training else 'Disabled'}")
    
    print(f"\n📊 Adversarial Learning Results:")
    print(f"   Adversarial Learning History Length: {len(adversarial_system.adversarial_learning_history)}")
    print(f"   Total Duration: {adversarial_results.get('total_duration', 0):.2f} seconds")
    
    # Show stage results summary
    if 'stages' in adversarial_results:
        for stage_name, stage_data in adversarial_results['stages'].items():
            print(f"   {stage_name}: {len(stage_data) if isinstance(stage_data, dict) else 'N/A'} results")
    
    print(f"\n📋 Adversarial Learning Report:")
    print(adversarial_report)
    
    return adversarial_system

# Export utilities
__all__ = [
    'AdversarialAttackType',
    'GANType',
    'DefenseStrategy',
    'AdversarialConfig',
    'AdversarialAttacker',
    'GANGenerator',
    'GANDiscriminator',
    'GANTrainer',
    'AdversarialDefense',
    'RobustnessAnalyzer',
    'AdversarialLearningSystem',
    'create_adversarial_config',
    'create_adversarial_attacker',
    'create_gan_generator',
    'create_gan_discriminator',
    'create_gan_trainer',
    'create_adversarial_defense',
    'create_robustness_analyzer',
    'create_adversarial_learning_system',
    'example_adversarial_learning'
]

if __name__ == "__main__":
    example_adversarial_learning()
    print("✅ Adversarial learning example completed successfully!")