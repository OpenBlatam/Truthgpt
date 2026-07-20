"""
Modern Training Pipeline for TruthGPT
Following deep learning best practices for LLM training
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torch.cuda.amp import autocast, GradScaler
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass
import numpy as np
from tqdm import tqdm
import wandb
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import matplotlib.pyplot as plt
import seaborn as sns

from .modern_truthgpt_optimizer import ModernTruthGPTOptimizer, TruthGPTConfig, TruthGPTDataset


@dataclass
class TrainingConfig:
    """Training configuration"""
    # Data parameters
    train_split: float = 0.8
    val_split: float = 0.1
    test_split: float = 0.1
    shuffle: bool = True
    random_seed: int = 42
    
    # Training parameters
    num_epochs: int = 100
    early_stopping_patience: int = 10
    min_delta: float = 1e-4
    
    # Evaluation parameters
    eval_interval: int = 500
    save_best_only: bool = True
    monitor_metric: str = "val_loss"
    mode: str = "min"  # min or max
    
    # Logging parameters
    log_interval: int = 100
    save_interval: int = 1000
    use_wandb: bool = False
    wandb_project: str = "truthgpt"
    
    # Hardware parameters
    num_workers: int = 4
    pin_memory: bool = True
    prefetch_factor: int = 2


class ModernTrainingPipeline:
    """
    Modern training pipeline following deep learning best practices
    """
    
    def __init__(self, model_config: TruthGPTConfig, training_config: TrainingConfig):
        self.model_config = model_config
        self.training_config = training_config
        
        # Initialize logging
        self.logger = self._setup_logging()
        
        # Initialize model
        self.model = ModernTruthGPTOptimizer(model_config)
        
        # Initialize training state
        self.current_epoch = 0
        self.global_step = 0
        self.best_metric = float('inf') if training_config.mode == "min" else float('-inf')
        self.patience_counter = 0
        
        # Initialize experiment tracking
        if training_config.use_wandb:
            self._init_wandb()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("ModernTrainingPipeline")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_wandb(self):
        """Initialize Weights & Biases tracking"""
        try:
            wandb.init(
                project=self.training_config.wandb_project,
                name=self.model_config.experiment_name,
                config={
                    'model_config': self.model_config.__dict__,
                    'training_config': self.training_config.__dict__
                }
            )
            self.logger.info("Initialized Weights & Biases tracking")
        except Exception as e:
            self.logger.error(f"Error initializing wandb: {e}")
            self.training_config.use_wandb = False
    
    def prepare_data(self, texts: List[str]) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """
        Prepare data loaders with proper train/val/test splits
        
        Args:
            texts: List of training texts
            
        Returns:
            Tuple of (train_loader, val_loader, test_loader)
        """
        try:
            # Set random seed for reproducibility
            torch.manual_seed(self.training_config.random_seed)
            np.random.seed(self.training_config.random_seed)
            
            # Create dataset
            dataset = TruthGPTDataset(
                texts=texts,
                tokenizer=self.model.tokenizer,
                max_length=self.model_config.max_length
            )
            
            # Calculate split sizes
            total_size = len(dataset)
            train_size = int(self.training_config.train_split * total_size)
            val_size = int(self.training_config.val_split * total_size)
            test_size = total_size - train_size - val_size
            
            # Split dataset
            train_dataset, val_dataset, test_dataset = random_split(
                dataset, [train_size, val_size, test_size],
                generator=torch.Generator().manual_seed(self.training_config.random_seed)
            )
            
            # Create data loaders
            train_loader = DataLoader(
                train_dataset,
                batch_size=self.model_config.batch_size,
                shuffle=self.training_config.shuffle,
                num_workers=self.training_config.num_workers,
                pin_memory=self.training_config.pin_memory,
                prefetch_factor=self.training_config.prefetch_factor
            )
            
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.model_config.batch_size,
                shuffle=False,
                num_workers=self.training_config.num_workers,
                pin_memory=self.training_config.pin_memory,
                prefetch_factor=self.training_config.prefetch_factor
            )
            
            test_loader = DataLoader(
                test_dataset,
                batch_size=self.model_config.batch_size,
                shuffle=False,
                num_workers=self.training_config.num_workers,
                pin_memory=self.training_config.pin_memory,
                prefetch_factor=self.training_config.prefetch_factor
            )
            
            self.logger.info(f"Data prepared: {len(train_dataset)} train, {len(val_dataset)} val, {len(test_dataset)} test")
            
            return train_loader, val_loader, test_loader
            
        except Exception as e:
            self.logger.error(f"Error preparing data: {e}")
            raise
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader) -> Dict[str, List[float]]:
        """
        Train the model with proper validation and early stopping
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            
        Returns:
            Dictionary with training history
        """
        try:
            # Initialize optimizer and scheduler
            optimizer = self.model.get_optimizer()
            scheduler = self.model.get_scheduler(optimizer, len(train_loader) * self.training_config.num_epochs)
            
            # Training history
            history = {
                'train_loss': [],
                'val_loss': [],
                'learning_rate': [],
                'epoch': []
            }
            
            self.logger.info("Starting training...")
            
            for epoch in range(self.training_config.num_epochs):
                self.current_epoch = epoch
                
                # Training phase
                train_metrics = self.model.train_epoch(train_loader, optimizer, scheduler)
                
                # Validation phase
                val_metrics = self.model.validate(val_loader)
                
                # Update history
                history['train_loss'].append(train_metrics['loss'])
                history['val_loss'].append(val_metrics['loss'])
                history['learning_rate'].append(train_metrics['learning_rate'])
                history['epoch'].append(epoch)
                
                # Log metrics
                self.logger.info(
                    f"Epoch {epoch}: Train Loss: {train_metrics['loss']:.4f}, "
                    f"Val Loss: {val_metrics['loss']:.4f}, "
                    f"LR: {train_metrics['learning_rate']:.2e}"
                )
                
                # Log to wandb
                if self.training_config.use_wandb:
                    wandb.log({
                        'epoch': epoch,
                        'train_loss': train_metrics['loss'],
                        'val_loss': val_metrics['loss'],
                        'learning_rate': train_metrics['learning_rate']
                    })
                
                # Check for improvement
                current_metric = val_metrics['loss']
                is_better = self._is_metric_better(current_metric, self.best_metric)
                
                if is_better:
                    self.best_metric = current_metric
                    self.patience_counter = 0
                    
                    # Save best model
                    if self.training_config.save_best_only:
                        self.model.save_checkpoint(optimizer, scheduler, is_best=True)
                else:
                    self.patience_counter += 1
                
                # Early stopping
                if self.patience_counter >= self.training_config.early_stopping_patience:
                    self.logger.info(f"Early stopping at epoch {epoch}")
                    break
            
            self.logger.info("Training completed")
            return history
            
        except Exception as e:
            self.logger.error(f"Error during training: {e}")
            raise
    
    def _is_metric_better(self, current: float, best: float) -> bool:
        """Check if current metric is better than best"""
        if self.training_config.mode == "min":
            return current < best - self.training_config.min_delta
        else:
            return current > best + self.training_config.min_delta
    
    def evaluate(self, test_loader: DataLoader) -> Dict[str, float]:
        """
        Evaluate model on test set with comprehensive metrics
        
        Args:
            test_loader: Test data loader
            
        Returns:
            Dictionary with evaluation metrics
        """
        try:
            self.model.eval()
            
            total_loss = 0.0
            all_predictions = []
            all_labels = []
            
            with torch.no_grad():
                for batch in tqdm(test_loader, desc="Evaluating"):
                    batch = {k: v.to(self.model.device) if isinstance(v, torch.Tensor) else v 
                            for k, v in batch.items()}
                    
                    # Forward pass
                    if self.model_config.use_mixed_precision:
                        with autocast():
                            outputs = self.model.forward(**batch)
                            loss = self.model.compute_loss(outputs, batch.get('labels'))
                    else:
                        outputs = self.model.forward(**batch)
                        loss = self.model.compute_loss(outputs, batch.get('labels'))
                    
                    total_loss += loss.item()
                    
                    # Get predictions for evaluation
                    logits = outputs['logits']
                    predictions = torch.argmax(logits, dim=-1)
                    
                    # Flatten for metrics calculation
                    predictions_flat = predictions.view(-1).cpu().numpy()
                    labels_flat = batch['labels'].view(-1).cpu().numpy()
                    
                    # Filter out padding tokens
                    mask = labels_flat != -100
                    predictions_flat = predictions_flat[mask]
                    labels_flat = labels_flat[mask]
                    
                    all_predictions.extend(predictions_flat)
                    all_labels.extend(labels_flat)
            
            # Calculate metrics
            avg_loss = total_loss / len(test_loader)
            accuracy = accuracy_score(all_labels, all_predictions)
            precision, recall, f1, _ = precision_recall_fscore_support(
                all_labels, all_predictions, average='weighted'
            )
            
            metrics = {
                'test_loss': avg_loss,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            }
            
            self.logger.info(f"Evaluation metrics: {metrics}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error during evaluation: {e}")
            raise
    
    def generate_samples(self, input_texts: List[str], max_length: int = 100) -> List[str]:
        """
        Generate samples from the model
        
        Args:
            input_texts: List of input texts
            max_length: Maximum generation length
            
        Returns:
            List of generated texts
        """
        try:
            generated_texts = []
            
            for input_text in tqdm(input_texts, desc="Generating samples"):
                generated_text = self.model.generate(
                    input_text=input_text,
                    max_length=max_length,
                    temperature=1.0,
                    top_p=0.9,
                    do_sample=True
                )
                generated_texts.append(generated_text)
            
            return generated_texts
            
        except Exception as e:
            self.logger.error(f"Error generating samples: {e}")
            raise
    
    def plot_training_history(self, history: Dict[str, List[float]], save_path: Optional[str] = None):
        """
        Plot training history
        
        Args:
            history: Training history dictionary
            save_path: Path to save the plot
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Plot training and validation loss
            axes[0, 0].plot(history['epoch'], history['train_loss'], label='Train Loss')
            axes[0, 0].plot(history['epoch'], history['val_loss'], label='Val Loss')
            axes[0, 0].set_xlabel('Epoch')
            axes[0, 0].set_ylabel('Loss')
            axes[0, 0].set_title('Training and Validation Loss')
            axes[0, 0].legend()
            axes[0, 0].grid(True)
            
            # Plot learning rate
            axes[0, 1].plot(history['epoch'], history['learning_rate'])
            axes[0, 1].set_xlabel('Epoch')
            axes[0, 1].set_ylabel('Learning Rate')
            axes[0, 1].set_title('Learning Rate Schedule')
            axes[0, 1].grid(True)
            
            # Plot loss comparison
            axes[1, 0].plot(history['epoch'], history['train_loss'], label='Train Loss')
            axes[1, 0].plot(history['epoch'], history['val_loss'], label='Val Loss')
            axes[1, 0].set_xlabel('Epoch')
            axes[1, 0].set_ylabel('Loss')
            axes[1, 0].set_title('Loss Comparison')
            axes[1, 0].legend()
            axes[1, 0].grid(True)
            
            # Plot learning rate on log scale
            axes[1, 1].semilogy(history['epoch'], history['learning_rate'])
            axes[1, 1].set_xlabel('Epoch')
            axes[1, 1].set_ylabel('Learning Rate (log scale)')
            axes[1, 1].set_title('Learning Rate Schedule (Log Scale)')
            axes[1, 1].grid(True)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Training history plot saved to {save_path}")
            
            plt.show()
            
        except Exception as e:
            self.logger.error(f"Error plotting training history: {e}")
            raise
    
    def save_training_report(self, history: Dict[str, List[float]], 
                           eval_metrics: Dict[str, float], 
                           save_path: str):
        """
        Save comprehensive training report
        
        Args:
            history: Training history
            eval_metrics: Evaluation metrics
            save_path: Path to save the report
        """
        try:
            report = {
                'model_config': self.model_config.__dict__,
                'training_config': self.training_config.__dict__,
                'training_history': history,
                'evaluation_metrics': eval_metrics,
                'model_info': self.model.get_model_info(),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(save_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Training report saved to {save_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving training report: {e}")
            raise
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.training_config.use_wandb:
                wandb.finish()
            
            self.logger.info("Training pipeline cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Utility functions for easy training
def create_training_pipeline(model_name: str = "microsoft/DialoGPT-medium",
                           experiment_name: str = "truthgpt_experiment",
                           use_wandb: bool = False) -> ModernTrainingPipeline:
    """Create a training pipeline with default settings"""
    
    # Model configuration
    model_config = TruthGPTConfig(
        model_name=model_name,
        experiment_name=experiment_name,
        use_mixed_precision=True,
        use_gradient_checkpointing=True,
        use_flash_attention=True
    )
    
    # Training configuration
    training_config = TrainingConfig(
        use_wandb=use_wandb,
        wandb_project="truthgpt",
        num_epochs=50,
        early_stopping_patience=5,
        eval_interval=100
    )
    
    return ModernTrainingPipeline(model_config, training_config)


def train_truthgpt_model(texts: List[str], 
                        model_name: str = "microsoft/DialoGPT-medium",
                        experiment_name: str = "truthgpt_experiment",
                        use_wandb: bool = False) -> Tuple[ModernTrainingPipeline, Dict[str, Any]]:
    """
    Complete training pipeline for TruthGPT model
    
    Args:
        texts: List of training texts
        model_name: Name of the base model
        experiment_name: Name of the experiment
        use_wandb: Whether to use Weights & Biases tracking
        
    Returns:
        Tuple of (pipeline, results)
    """
    try:
        # Create training pipeline
        pipeline = create_training_pipeline(model_name, experiment_name, use_wandb)
        
        # Prepare data
        train_loader, val_loader, test_loader = pipeline.prepare_data(texts)
        
        # Train model
        history = pipeline.train(train_loader, val_loader)
        
        # Evaluate model
        eval_metrics = pipeline.evaluate(test_loader)
        
        # Generate samples
        sample_inputs = ["Hello, how are you?", "What is the meaning of life?", "Tell me a story."]
        generated_samples = pipeline.generate_samples(sample_inputs)
        
        # Create results
        results = {
            'history': history,
            'eval_metrics': eval_metrics,
            'generated_samples': generated_samples,
            'model_info': pipeline.model.get_model_info()
        }
        
        # Save training report
        report_path = f"{experiment_name}_training_report.json"
        pipeline.save_training_report(history, eval_metrics, report_path)
        
        # Plot training history
        plot_path = f"{experiment_name}_training_history.png"
        pipeline.plot_training_history(history, plot_path)
        
        return pipeline, results
        
    except Exception as e:
        logging.error(f"Error in training pipeline: {e}")
        raise
    finally:
        if 'pipeline' in locals():
            pipeline.cleanup()


# Example usage
if __name__ == "__main__":
    # Example training texts
    sample_texts = [
        "Hello, how are you today?",
        "What is the weather like?",
        "Tell me about artificial intelligence.",
        "How does machine learning work?",
        "What are the benefits of deep learning?"
    ] * 100  # Repeat for more training data
    
    # Train model
    pipeline, results = train_truthgpt_model(
        texts=sample_texts,
        model_name="microsoft/DialoGPT-medium",
        experiment_name="truthgpt_demo",
        use_wandb=False
    )
    
    print("Training completed!")
    print(f"Final evaluation metrics: {results['eval_metrics']}")
    print(f"Generated samples: {results['generated_samples']}")


