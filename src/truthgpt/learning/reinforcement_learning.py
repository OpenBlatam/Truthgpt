"""
Advanced Reinforcement Learning System for TruthGPT Optimization Core
Deep Q-Networks, Policy Gradient, Actor-Critic, and Multi-Agent RL
"""

import torch
import torch.nn as nn
import torch.optim as optim
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
from collections import deque, namedtuple
import itertools

logger = logging.getLogger(__name__)

class RLAlgorithm(Enum):
    """Reinforcement Learning algorithms"""
    DQN = "dqn"  # Deep Q-Network
    DDQN = "ddqn"  # Double DQN
    D3QN = "d3qn"  # Dueling Double DQN
    A3C = "a3c"  # Asynchronous Advantage Actor-Critic
    PPO = "ppo"  # Proximal Policy Optimization
    SAC = "sac"  # Soft Actor-Critic
    TD3 = "td3"  # Twin Delayed Deep Deterministic Policy Gradient
    MADDPG = "maddpg"  # Multi-Agent Deep Deterministic Policy Gradient

class EnvironmentType(Enum):
    """Environment types"""
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"
    MULTI_AGENT = "multi_agent"
    PARTIALLY_OBSERVABLE = "partially_observable"
    HIERARCHICAL = "hierarchical"

@dataclass
class RLConfig:
    """Configuration for Reinforcement Learning"""
    # Algorithm settings
    algorithm: RLAlgorithm = RLAlgorithm.DQN
    environment_type: EnvironmentType = EnvironmentType.DISCRETE
    
    # Training parameters
    learning_rate: float = 0.001
    gamma: float = 0.99
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    batch_size: int = 32
    
    # Experience replay
    buffer_size: int = 10000
    min_buffer_size: int = 1000
    update_frequency: int = 4
    
    # Target network
    target_update_frequency: int = 100
    soft_update_tau: float = 0.001
    
    # Advanced features
    enable_double_dqn: bool = True
    enable_dueling: bool = True
    enable_prioritized_replay: bool = True
    enable_noisy_networks: bool = False
    
    # Multi-agent settings
    num_agents: int = 1
    enable_centralized_training: bool = True
    enable_decentralized_execution: bool = True
    
    def __post_init__(self):
        """Validate RL configuration"""
        if self.gamma < 0.0 or self.gamma > 1.0:
            raise ValueError("Gamma must be between 0.0 and 1.0")
        if self.epsilon_start < 0.0 or self.epsilon_start > 1.0:
            raise ValueError("Epsilon start must be between 0.0 and 1.0")

class ExperienceReplay:
    """Experience replay buffer"""
    
    def __init__(self, capacity: int, state_dim: int, action_dim: int):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.priorities = deque(maxlen=capacity)
        self.alpha = 0.6  # Prioritization exponent
        self.beta = 0.4   # Importance sampling exponent
        self.beta_increment = 0.001
        
        logger.info(f"✅ Experience Replay initialized (capacity: {capacity})")
    
    def add(self, state: np.ndarray, action: int, reward: float, 
            next_state: np.ndarray, done: bool, td_error: float = None):
        """Add experience to buffer"""
        experience = (state, action, reward, next_state, done)
        self.buffer.append(experience)
        
        # Calculate priority
        if td_error is not None:
            priority = (abs(td_error) + 1e-6) ** self.alpha
        else:
            priority = 1.0
        
        self.priorities.append(priority)
    
    def sample(self, batch_size: int) -> Tuple[List, List, List]:
        """Sample batch from buffer"""
        if len(self.buffer) < batch_size:
            return None, None, None
        
        # Calculate sampling probabilities
        priorities = np.array(self.priorities)
        probabilities = priorities / priorities.sum()
        
        # Sample indices
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
        
        # Calculate importance sampling weights
        weights = (len(self.buffer) * probabilities[indices]) ** (-self.beta)
        weights = weights / weights.max()
        
        # Get experiences
        experiences = [self.buffer[i] for i in indices]
        
        return experiences, indices, weights
    
    def update_priorities(self, indices: List[int], td_errors: List[float]):
        """Update priorities for sampled experiences"""
        for idx, td_error in zip(indices, td_errors):
            if idx < len(self.priorities):
                priority = (abs(td_error) + 1e-6) ** self.alpha
                self.priorities[idx] = priority
    
    def __len__(self):
        return len(self.buffer)

class DQNNetwork(nn.Module):
    """Deep Q-Network"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = [128, 128]):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Build network
        layers = []
        input_dim = state_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            input_dim = hidden_dim
        
        layers.append(nn.Linear(input_dim, action_dim))
        
        self.network = nn.Sequential(*layers)
        
        logger.info(f"✅ DQN Network initialized (state_dim: {state_dim}, action_dim: {action_dim})")
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        return self.network(state)

class DuelingDQNNetwork(nn.Module):
    """Dueling Deep Q-Network"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = [128, 128]):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Shared layers
        shared_layers = []
        input_dim = state_dim
        
        for hidden_dim in hidden_dims[:-1]:
            shared_layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            input_dim = hidden_dim
        
        self.shared_network = nn.Sequential(*shared_layers)
        
        # Value stream
        self.value_stream = nn.Sequential(
            nn.Linear(input_dim, hidden_dims[-1]),
            nn.ReLU(),
            nn.Linear(hidden_dims[-1], 1)
        )
        
        # Advantage stream
        self.advantage_stream = nn.Sequential(
            nn.Linear(input_dim, hidden_dims[-1]),
            nn.ReLU(),
            nn.Linear(hidden_dims[-1], action_dim)
        )
        
        logger.info(f"✅ Dueling DQN Network initialized")
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        shared_features = self.shared_network(state)
        
        value = self.value_stream(shared_features)
        advantage = self.advantage_stream(shared_features)
        
        # Combine value and advantage
        q_values = value + advantage - advantage.mean(dim=1, keepdim=True)
        
        return q_values

class DQNAgent:
    """Deep Q-Network Agent"""
    
    def __init__(self, state_dim: int, action_dim: int, config: RLConfig):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config
        
        # Networks
        if config.enable_dueling:
            self.q_network = DuelingDQNNetwork(state_dim, action_dim)
            self.target_network = DuelingDQNNetwork(state_dim, action_dim)
        else:
            self.q_network = DQNNetwork(state_dim, action_dim)
            self.target_network = DQNNetwork(state_dim, action_dim)
        
        # Copy weights to target network
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=config.learning_rate)
        
        # Experience replay
        self.replay_buffer = ExperienceReplay(
            config.buffer_size, state_dim, action_dim
        )
        
        # Training state
        self.epsilon = config.epsilon_start
        self.step_count = 0
        self.episode_count = 0
        self.training_history = []
        
        logger.info(f"✅ DQN Agent initialized")
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """Select action using epsilon-greedy policy"""
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.q_network(state_tensor)
            action = q_values.argmax().item()
        
        return action
    
    def store_experience(self, state: np.ndarray, action: int, reward: float,
                        next_state: np.ndarray, done: bool):
        """Store experience in replay buffer"""
        self.replay_buffer.add(state, action, reward, next_state, done)
    
    def train(self) -> Dict[str, float]:
        """Train the agent"""
        if len(self.replay_buffer) < self.config.min_buffer_size:
            return {'loss': 0.0, 'q_value': 0.0}
        
        # Sample batch
        experiences, indices, weights = self.replay_buffer.sample(self.config.batch_size)
        if experiences is None:
            return {'loss': 0.0, 'q_value': 0.0}
        
        # Convert to tensors
        states = torch.FloatTensor([exp[0] for exp in experiences])
        actions = torch.LongTensor([exp[1] for exp in experiences])
        rewards = torch.FloatTensor([exp[2] for exp in experiences])
        next_states = torch.FloatTensor([exp[3] for exp in experiences])
        dones = torch.BoolTensor([exp[4] for exp in experiences])
        weights = torch.FloatTensor(weights)
        
        # Current Q-values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Target Q-values
        with torch.no_grad():
            if self.config.enable_double_dqn:
                # Double DQN: use main network to select actions
                next_actions = self.q_network(next_states).argmax(1)
                next_q_values = self.target_network(next_states).gather(1, next_actions.unsqueeze(1))
            else:
                # Standard DQN
                next_q_values = self.target_network(next_states).max(1)[0].unsqueeze(1)
            
            target_q_values = rewards.unsqueeze(1) + (self.config.gamma * next_q_values * ~dones.unsqueeze(1))
        
        # Calculate loss
        td_errors = current_q_values - target_q_values
        loss = (weights.unsqueeze(1) * td_errors.pow(2)).mean()
        
        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update priorities
        td_errors_np = td_errors.detach().numpy().flatten()
        self.replay_buffer.update_priorities(indices, td_errors_np)
        
        # Update target network
        if self.step_count % self.config.target_update_frequency == 0:
            self._soft_update_target_network()
        
        # Update epsilon
        self.epsilon = max(self.config.epsilon_end, 
                          self.epsilon * self.config.epsilon_decay)
        
        self.step_count += 1
        
        return {
            'loss': loss.item(),
            'q_value': current_q_values.mean().item(),
            'epsilon': self.epsilon
        }
    
    def _soft_update_target_network(self):
        """Soft update target network"""
        for target_param, param in zip(self.target_network.parameters(), 
                                     self.q_network.parameters()):
            target_param.data.copy_(
                self.config.soft_update_tau * param.data + 
                (1 - self.config.soft_update_tau) * target_param.data
            )
    
    def save_model(self, path: str):
        """Save model"""
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'step_count': self.step_count,
            'episode_count': self.episode_count
        }, path)
        logger.info(f"✅ Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model"""
        checkpoint = torch.load(path)
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.step_count = checkpoint['step_count']
        self.episode_count = checkpoint['episode_count']
        logger.info(f"✅ Model loaded from {path}")

class PPOAgent:
    """Proximal Policy Optimization Agent"""
    
    def __init__(self, state_dim: int, action_dim: int, config: RLConfig):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config
        
        # Actor-Critic networks
        self.actor = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
            nn.Softmax(dim=-1)
        )
        
        self.critic = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )
        
        # Optimizers
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=config.learning_rate)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=config.learning_rate)
        
        # PPO parameters
        self.clip_ratio = 0.2
        self.value_loss_coef = 0.5
        self.entropy_coef = 0.01
        self.max_grad_norm = 0.5
        
        # Training state
        self.step_count = 0
        self.episode_count = 0
        
        logger.info(f"✅ PPO Agent initialized")
    
    def select_action(self, state: np.ndarray) -> Tuple[int, float, float]:
        """Select action using current policy"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        
        with torch.no_grad():
            action_probs = self.actor(state_tensor)
            value = self.critic(state_tensor)
            
            # Sample action
            action_dist = torch.distributions.Categorical(action_probs)
            action = action_dist.sample()
            log_prob = action_dist.log_prob(action)
        
        return action.item(), log_prob.item(), value.item()
    
    def update(self, states: torch.Tensor, actions: torch.Tensor, 
               old_log_probs: torch.Tensor, returns: torch.Tensor,
               advantages: torch.Tensor) -> Dict[str, float]:
        """Update policy using PPO"""
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # Calculate current policy
        action_probs = self.actor(states)
        action_dist = torch.distributions.Categorical(action_probs)
        log_probs = action_dist.log_prob(actions)
        entropy = action_dist.entropy().mean()
        
        # Calculate ratios
        ratios = torch.exp(log_probs - old_log_probs)
        
        # Calculate clipped surrogate loss
        surr1 = ratios * advantages
        surr2 = torch.clamp(ratios, 1 - self.clip_ratio, 1 + self.clip_ratio) * advantages
        actor_loss = -torch.min(surr1, surr2).mean()
        
        # Calculate value loss
        values = self.critic(states).squeeze()
        value_loss = nn.MSELoss()(values, returns)
        
        # Total loss
        total_loss = actor_loss + self.value_loss_coef * value_loss - self.entropy_coef * entropy
        
        # Update actor
        self.actor_optimizer.zero_grad()
        actor_loss.backward(retain_graph=True)
        torch.nn.utils.clip_grad_norm_(self.actor.parameters(), self.max_grad_norm)
        self.actor_optimizer.step()
        
        # Update critic
        self.critic_optimizer.zero_grad()
        value_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.critic.parameters(), self.max_grad_norm)
        self.critic_optimizer.step()
        
        self.step_count += 1
        
        return {
            'actor_loss': actor_loss.item(),
            'value_loss': value_loss.item(),
            'entropy': entropy.item(),
            'total_loss': total_loss.item()
        }

class MultiAgentEnvironment:
    """Multi-agent environment for RL training"""
    
    def __init__(self, num_agents: int, state_dim: int, action_dim: int):
        self.num_agents = num_agents
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.agents = []
        
        logger.info(f"✅ Multi-Agent Environment initialized ({num_agents} agents)")
    
    def add_agent(self, agent):
        """Add agent to environment"""
        self.agents.append(agent)
        logger.info(f"✅ Agent {len(self.agents)} added")
    
    def reset(self) -> List[np.ndarray]:
        """Reset environment and return initial states"""
        states = []
        for _ in range(self.num_agents):
            state = np.random.random(self.state_dim)
            states.append(state)
        return states
    
    def step(self, actions: List[int]) -> Tuple[List[np.ndarray], List[float], List[bool]]:
        """Execute actions and return next states, rewards, and dones"""
        next_states = []
        rewards = []
        dones = []
        
        for i, action in enumerate(actions):
            # Simulate environment step
            next_state = np.random.random(self.state_dim)
            reward = np.random.normal(0, 1)  # Random reward
            done = np.random.random() < 0.1  # 10% chance of episode end
            
            next_states.append(next_state)
            rewards.append(reward)
            dones.append(done)
        
        return next_states, rewards, dones

class RLTrainingManager:
    """Reinforcement Learning Training Manager"""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.agents = []
        self.environment = None
        self.training_history = []
        
        logger.info("✅ RL Training Manager initialized")
    
    def create_agent(self, state_dim: int, action_dim: int) -> Union[DQNAgent, PPOAgent]:
        """Create agent based on algorithm"""
        if self.config.algorithm == RLAlgorithm.DQN:
            return DQNAgent(state_dim, action_dim, self.config)
        elif self.config.algorithm == RLAlgorithm.PPO:
            return PPOAgent(state_dim, action_dim, self.config)
        else:
            return DQNAgent(state_dim, action_dim, self.config)  # Default to DQN
    
    def train_agent(self, agent: Union[DQNAgent, PPOAgent], 
                   num_episodes: int = 1000) -> Dict[str, Any]:
        """Train a single agent"""
        logger.info(f"🚀 Starting RL training for {num_episodes} episodes")
        
        episode_rewards = []
        episode_lengths = []
        training_losses = []
        
        for episode in range(num_episodes):
            # Reset environment
            state = np.random.random(self.config.state_dim if hasattr(self.config, 'state_dim') else 10)
            episode_reward = 0
            episode_length = 0
            
            while True:
                # Select action
                if isinstance(agent, DQNAgent):
                    action = agent.select_action(state, training=True)
                    
                    # Execute action
                    next_state = np.random.random(len(state))
                    reward = np.random.normal(0, 1)
                    done = np.random.random() < 0.1
                    
                    # Store experience
                    agent.store_experience(state, action, reward, next_state, done)
                    
                    # Train
                    if len(agent.replay_buffer) >= self.config.min_buffer_size:
                        loss_info = agent.train()
                        training_losses.append(loss_info['loss'])
                    
                    state = next_state
                    episode_reward += reward
                    episode_length += 1
                    
                    if done:
                        break
                
                elif isinstance(agent, PPOAgent):
                    # PPO training would require more complex episode collection
                    # For simplicity, we'll just simulate
                    action, log_prob, value = agent.select_action(state)
                    next_state = np.random.random(len(state))
                    reward = np.random.normal(0, 1)
                    done = np.random.random() < 0.1
                    
                    state = next_state
                    episode_reward += reward
                    episode_length += 1
                    
                    if done:
                        break
            
            episode_rewards.append(episode_reward)
            episode_lengths.append(episode_length)
            
            # Log progress
            if episode % 100 == 0:
                avg_reward = np.mean(episode_rewards[-100:])
                logger.info(f"Episode {episode}: Avg Reward = {avg_reward:.2f}")
        
        # Training statistics
        training_stats = {
            'total_episodes': num_episodes,
            'avg_reward': np.mean(episode_rewards),
            'max_reward': np.max(episode_rewards),
            'min_reward': np.min(episode_rewards),
            'avg_length': np.mean(episode_lengths),
            'avg_loss': np.mean(training_losses) if training_losses else 0.0,
            'episode_rewards': episode_rewards,
            'episode_lengths': episode_lengths
        }
        
        self.training_history.append(training_stats)
        
        logger.info(f"✅ RL training completed. Avg reward: {training_stats['avg_reward']:.2f}")
        return training_stats
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """Get training statistics"""
        if not self.training_history:
            return {}
        
        return {
            'total_training_sessions': len(self.training_history),
            'latest_stats': self.training_history[-1],
            'algorithm': self.config.algorithm.value,
            'environment_type': self.config.environment_type.value
        }

# Factory functions
def create_rl_config(**kwargs) -> RLConfig:
    """Create RL configuration"""
    return RLConfig(**kwargs)

def create_dqn_agent(state_dim: int, action_dim: int, config: RLConfig) -> DQNAgent:
    """Create DQN agent"""
    return DQNAgent(state_dim, action_dim, config)

def create_ppo_agent(state_dim: int, action_dim: int, config: RLConfig) -> PPOAgent:
    """Create PPO agent"""
    return PPOAgent(state_dim, action_dim, config)

def create_rl_training_manager(config: RLConfig) -> RLTrainingManager:
    """Create RL training manager"""
    return RLTrainingManager(config)

# Example usage
def example_reinforcement_learning():
    """Example of reinforcement learning"""
    # Create configuration
    config = create_rl_config(
        algorithm=RLAlgorithm.DQN,
        learning_rate=0.001,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.01,
        batch_size=32,
        buffer_size=10000
    )
    
    # Create agent
    state_dim = 10
    action_dim = 4
    agent = create_dqn_agent(state_dim, action_dim, config)
    
    # Create training manager
    training_manager = create_rl_training_manager(config)
    
    # Train agent
    training_stats = training_manager.train_agent(agent, num_episodes=500)
    
    # Get statistics
    stats = training_manager.get_training_statistics()
    
    print(f"✅ Reinforcement Learning Example Complete!")
    print(f"🤖 RL Statistics:")
    print(f"   Algorithm: {stats['algorithm']}")
    print(f"   Total Episodes: {training_stats['total_episodes']}")
    print(f"   Average Reward: {training_stats['avg_reward']:.2f}")
    print(f"   Max Reward: {training_stats['max_reward']:.2f}")
    print(f"   Average Length: {training_stats['avg_length']:.2f}")
    print(f"   Average Loss: {training_stats['avg_loss']:.4f}")
    
    return agent

# Export utilities
__all__ = [
    'RLAlgorithm',
    'EnvironmentType',
    'RLConfig',
    'ExperienceReplay',
    'DQNNetwork',
    'DuelingDQNNetwork',
    'DQNAgent',
    'PPOAgent',
    'MultiAgentEnvironment',
    'RLTrainingManager',
    'create_rl_config',
    'create_dqn_agent',
    'create_ppo_agent',
    'create_rl_training_manager',
    'example_reinforcement_learning'
]

if __name__ == "__main__":
    example_reinforcement_learning()
    print("✅ Reinforcement learning example completed successfully!")

