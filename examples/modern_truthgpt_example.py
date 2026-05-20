"""
Modern TruthGPT Example
Demonstrating deep learning best practices for LLM optimization
"""

import torch
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Import our modern components
from core.modern_truthgpt_optimizer import ModernTruthGPTOptimizer, TruthGPTConfig
from core.training_pipeline import ModernTrainingPipeline, TrainingConfig
from examples.gradio_interface import TruthGPTGradioInterface


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('truthgpt_example.log')
        ]
    )
    return logging.getLogger("TruthGPTExample")


def create_sample_data() -> List[str]:
    """Create sample training data"""
    sample_texts = [
        "Hello, how are you today?",
        "What is the weather like?",
        "Tell me about artificial intelligence.",
        "How does machine learning work?",
        "What are the benefits of deep learning?",
        "Explain neural networks in simple terms.",
        "What is the difference between AI and ML?",
        "How do transformers work?",
        "What is attention mechanism?",
        "Explain the concept of embeddings.",
        "What is fine-tuning in deep learning?",
        "How do you train a language model?",
        "What are the challenges in NLP?",
        "Explain the concept of transfer learning.",
        "What is the future of AI?",
        "How do you evaluate language models?",
        "What is the role of data in AI?",
        "Explain the concept of bias in AI.",
        "What are the ethical considerations in AI?",
        "How do you deploy AI models in production?"
    ]
    
    # Repeat data for more training examples
    return sample_texts * 5


def demonstrate_model_initialization():
    """Demonstrate model initialization with best practices"""
    logger = logging.getLogger("ModelInit")
    logger.info("=== Model Initialization Demo ===")
    
    # Create configuration
    config = TruthGPTConfig(
        model_name="microsoft/DialoGPT-medium",
        max_length=512,  # Smaller for demo
        batch_size=8,    # Smaller for demo
        learning_rate=1e-4,
        use_mixed_precision=True,
        use_gradient_checkpointing=True,
        use_flash_attention=True,
        experiment_name="truthgpt_demo"
    )
    
    logger.info(f"Configuration: {config}")
    
    # Initialize model
    model = ModernTruthGPTOptimizer(config)
    
    # Get model information
    model_info = model.get_model_info()
    logger.info(f"Model Info: {json.dumps(model_info, indent=2)}")
    
    return model, config


def demonstrate_training_pipeline():
    """Demonstrate training pipeline with best practices"""
    logger = logging.getLogger("TrainingPipeline")
    logger.info("=== Training Pipeline Demo ===")
    
    # Create sample data
    sample_texts = create_sample_data()
    logger.info(f"Created {len(sample_texts)} training examples")
    
    # Create model configuration
    model_config = TruthGPTConfig(
        model_name="microsoft/DialoGPT-medium",
        max_length=256,  # Smaller for demo
        batch_size=4,   # Smaller for demo
        learning_rate=1e-4,
        use_mixed_precision=True,
        use_gradient_checkpointing=True,
        use_flash_attention=True,
        experiment_name="truthgpt_training_demo"
    )
    
    # Create training configuration
    training_config = TrainingConfig(
        num_epochs=3,  # Small for demo
        early_stopping_patience=2,
        eval_interval=50,
        use_wandb=False  # Disable for demo
    )
    
    # Create training pipeline
    pipeline = ModernTrainingPipeline(model_config, training_config)
    
    try:
        # Prepare data
        logger.info("Preparing data...")
        train_loader, val_loader, test_loader = pipeline.prepare_data(sample_texts)
        
        # Train model
        logger.info("Starting training...")
        history = pipeline.train(train_loader, val_loader)
        
        # Evaluate model
        logger.info("Evaluating model...")
        eval_metrics = pipeline.evaluate(test_loader)
        
        # Generate samples
        logger.info("Generating samples...")
        sample_inputs = [
            "Hello, how are you?",
            "What is AI?",
            "Tell me about machine learning."
        ]
        generated_samples = pipeline.generate_samples(sample_inputs, max_length=50)
        
        # Create results
        results = {
            'history': history,
            'eval_metrics': eval_metrics,
            'generated_samples': generated_samples,
            'model_info': pipeline.model.get_model_info()
        }
        
        logger.info("Training completed successfully!")
        logger.info(f"Final metrics: {eval_metrics}")
        logger.info(f"Generated samples: {generated_samples}")
        
        return results
        
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise
    finally:
        pipeline.cleanup()


def demonstrate_text_generation():
    """Demonstrate text generation capabilities"""
    logger = logging.getLogger("TextGeneration")
    logger.info("=== Text Generation Demo ===")
    
    # Initialize model
    model, config = demonstrate_model_initialization()
    
    # Sample prompts
    prompts = [
        "Hello, how are you?",
        "What is artificial intelligence?",
        "Tell me a story about",
        "Explain the concept of",
        "What are the benefits of"
    ]
    
    logger.info("Generating text samples...")
    
    for i, prompt in enumerate(prompts):
        try:
            logger.info(f"Prompt {i+1}: {prompt}")
            
            # Generate with different parameters
            generated = model.generate(
                input_text=prompt,
                max_length=100,
                temperature=1.0,
                top_p=0.9,
                do_sample=True
            )
            
            logger.info(f"Generated: {generated}")
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"Generation error for prompt '{prompt}': {e}")


def demonstrate_model_analysis():
    """Demonstrate model analysis capabilities"""
    logger = logging.getLogger("ModelAnalysis")
    logger.info("=== Model Analysis Demo ===")
    
    # Initialize model
    model, config = demonstrate_model_initialization()
    
    # Get model information
    model_info = model.get_model_info()
    
    logger.info("Model Analysis Results:")
    logger.info(f"Total Parameters: {model_info['total_parameters']:,}")
    logger.info(f"Trainable Parameters: {model_info['trainable_parameters']:,}")
    logger.info(f"Model Size: {model_info['model_size_mb']:.2f} MB")
    logger.info(f"Device: {model_info['device']}")
    
    # Analyze text complexity
    sample_texts = [
        "Hello world!",
        "The quick brown fox jumps over the lazy dog.",
        "Artificial intelligence is a branch of computer science that aims to create intelligent machines."
    ]
    
    logger.info("Text Analysis:")
    for text in sample_texts:
        word_count = len(text.split())
        char_count = len(text)
        complexity = word_count / max(1, text.count('.') + text.count('!') + text.count('?'))
        
        logger.info(f"Text: '{text}'")
        logger.info(f"  Words: {word_count}, Characters: {char_count}, Complexity: {complexity:.2f}")


def demonstrate_optimization_techniques():
    """Demonstrate various optimization techniques"""
    logger = logging.getLogger("OptimizationTechniques")
    logger.info("=== Optimization Techniques Demo ===")
    
    # Mixed Precision Training
    logger.info("1. Mixed Precision Training:")
    config_mixed = TruthGPTConfig(use_mixed_precision=True)
    model_mixed = ModernTruthGPTOptimizer(config_mixed)
    logger.info(f"Mixed precision enabled: {config_mixed.use_mixed_precision}")
    
    # Gradient Checkpointing
    logger.info("2. Gradient Checkpointing:")
    config_checkpoint = TruthGPTConfig(use_gradient_checkpointing=True)
    model_checkpoint = ModernTruthGPTOptimizer(config_checkpoint)
    logger.info(f"Gradient checkpointing enabled: {config_checkpoint.use_gradient_checkpointing}")
    
    # LoRA Fine-tuning
    logger.info("3. LoRA Fine-tuning:")
    config_lora = TruthGPTConfig(use_lora=True, lora_rank=16, lora_alpha=32)
    model_lora = ModernTruthGPTOptimizer(config_lora)
    logger.info(f"LoRA enabled: {config_lora.use_lora}, Rank: {config_lora.lora_rank}")
    
    # Flash Attention
    logger.info("4. Flash Attention:")
    config_flash = TruthGPTConfig(use_flash_attention=True)
    model_flash = ModernTruthGPTOptimizer(config_flash)
    logger.info(f"Flash attention enabled: {config_flash.use_flash_attention}")


def demonstrate_gradio_interface():
    """Demonstrate Gradio interface (optional)"""
    logger = logging.getLogger("GradioInterface")
    logger.info("=== Gradio Interface Demo ===")
    
    try:
        # Create Gradio interface
        interface = TruthGPTGradioInterface()
        logger.info("Gradio interface created successfully")
        logger.info("To launch the interface, run: interface.launch()")
        
        # Note: Uncomment the following line to actually launch the interface
        # interface.launch(share=False, server_port=7860)
        
    except Exception as e:
        logger.error(f"Gradio interface error: {e}")


def create_visualization_report(results: Dict[str, Any], save_path: str = "truthgpt_report.png"):
    """Create visualization report"""
    logger = logging.getLogger("Visualization")
    logger.info("=== Creating Visualization Report ===")
    
    try:
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('TruthGPT Training Report', fontsize=16, fontweight='bold')
        
        # Plot 1: Training and Validation Loss
        if 'history' in results and 'train_loss' in results['history']:
            history = results['history']
            epochs = range(len(history['train_loss']))
            
            axes[0, 0].plot(epochs, history['train_loss'], label='Train Loss', marker='o')
            axes[0, 0].plot(epochs, history['val_loss'], label='Validation Loss', marker='s')
            axes[0, 0].set_xlabel('Epoch')
            axes[0, 0].set_ylabel('Loss')
            axes[0, 0].set_title('Training Progress')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Learning Rate Schedule
        if 'history' in results and 'learning_rate' in results['history']:
            axes[0, 1].plot(epochs, history['learning_rate'], color='green', marker='o')
            axes[0, 1].set_xlabel('Epoch')
            axes[0, 1].set_ylabel('Learning Rate')
            axes[0, 1].set_title('Learning Rate Schedule')
            axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Model Metrics
        if 'eval_metrics' in results:
            metrics = results['eval_metrics']
            metric_names = list(metrics.keys())
            metric_values = list(metrics.values())
            
            bars = axes[1, 0].bar(metric_names, metric_values, color=['blue', 'green', 'red', 'orange'])
            axes[1, 0].set_ylabel('Score')
            axes[1, 0].set_title('Evaluation Metrics')
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, value in zip(bars, metric_values):
                axes[1, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                               f'{value:.3f}', ha='center', va='bottom')
        
        # Plot 4: Model Information
        if 'model_info' in results:
            model_info = results['model_info']
            info_text = f"""
            Total Parameters: {model_info['total_parameters']:,}
            Trainable Parameters: {model_info['trainable_parameters']:,}
            Model Size: {model_info['model_size_mb']:.2f} MB
            Device: {model_info['device']}
            Current Epoch: {model_info['current_epoch']}
            Global Step: {model_info['global_step']}
            """
            
            axes[1, 1].text(0.1, 0.5, info_text, transform=axes[1, 1].transAxes,
                           fontsize=10, verticalalignment='center',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
            axes[1, 1].set_title('Model Information')
            axes[1, 1].axis('off')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Visualization report saved to {save_path}")
        plt.show()
        
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")


def main():
    """Main demonstration function"""
    logger = setup_logging()
    logger.info("=== TruthGPT Modern Example ===")
    logger.info("Demonstrating deep learning best practices for LLM optimization")
    
    try:
        # 1. Model Initialization
        logger.info("\n" + "="*50)
        demonstrate_model_initialization()
        
        # 2. Training Pipeline
        logger.info("\n" + "="*50)
        results = demonstrate_training_pipeline()
        
        # 3. Text Generation
        logger.info("\n" + "="*50)
        demonstrate_text_generation()
        
        # 4. Model Analysis
        logger.info("\n" + "="*50)
        demonstrate_model_analysis()
        
        # 5. Optimization Techniques
        logger.info("\n" + "="*50)
        demonstrate_optimization_techniques()
        
        # 6. Gradio Interface (optional)
        logger.info("\n" + "="*50)
        demonstrate_gradio_interface()
        
        # 7. Create Visualization Report
        logger.info("\n" + "="*50)
        create_visualization_report(results)
        
        # 8. Save Results
        logger.info("\n" + "="*50)
        results_path = "truthgpt_example_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {results_path}")
        
        logger.info("\n=== Example completed successfully! ===")
        logger.info("Key improvements demonstrated:")
        logger.info("✓ Modern PyTorch architecture")
        logger.info("✓ Mixed precision training")
        logger.info("✓ Gradient checkpointing")
        logger.info("✓ LoRA fine-tuning")
        logger.info("✓ Flash attention optimization")
        logger.info("✓ Comprehensive evaluation metrics")
        logger.info("✓ Interactive Gradio interface")
        logger.info("✓ Experiment tracking and visualization")
        logger.info("✓ Error handling and logging")
        logger.info("✓ Modular and maintainable code structure")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise


if __name__ == "__main__":
    main()


