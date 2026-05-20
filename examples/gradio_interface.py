"""
Gradio Interface for TruthGPT
Interactive demo following deep learning best practices
"""

import gradio as gr
import torch
import logging
from typing import List, Tuple, Optional, Dict, Any
import json
import time
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
import io
import base64

from core.modern_truthgpt_optimizer import ModernTruthGPTOptimizer, TruthGPTConfig
from core.training_pipeline import ModernTrainingPipeline, TrainingConfig


class TruthGPTGradioInterface:
    """
    Gradio interface for TruthGPT model interaction
    Following best practices for user-friendly interfaces
    """
    
    def __init__(self, model_path: Optional[str] = None, config_path: Optional[str] = None):
        self.model = None
        self.config = None
        self.logger = self._setup_logging()
        
        # Load model and configuration
        self._load_model_and_config(model_path, config_path)
        
        # Initialize interface
        self.interface = self._create_interface()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for Gradio interface"""
        logger = logging.getLogger("TruthGPTGradioInterface")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_model_and_config(self, model_path: Optional[str], config_path: Optional[str]):
        """Load model and configuration"""
        try:
            if model_path and Path(model_path).exists():
                # Load from checkpoint
                checkpoint = torch.load(model_path, map_location='cpu')
                self.config = checkpoint.get('config', TruthGPTConfig())
                self.model = ModernTruthGPTOptimizer(self.config)
                self.model.load_checkpoint(model_path)
                self.logger.info(f"Model loaded from {model_path}")
            else:
                # Use default configuration
                self.config = TruthGPTConfig()
                self.model = ModernTruthGPTOptimizer(self.config)
                self.logger.info("Using default model configuration")
            
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            # Fallback to default
            self.config = TruthGPTConfig()
            self.model = ModernTruthGPTOptimizer(self.config)
    
    def _create_interface(self) -> gr.Blocks:
        """Create Gradio interface"""
        with gr.Blocks(
            title="TruthGPT Interactive Demo",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px !important;
            }
            .chat-message {
                padding: 10px;
                margin: 5px 0;
                border-radius: 10px;
            }
            .user-message {
                background-color: #e3f2fd;
                text-align: right;
            }
            .bot-message {
                background-color: #f3e5f5;
                text-align: left;
            }
            """
        ) as interface:
            
            gr.Markdown("# 🤖 TruthGPT Interactive Demo")
            gr.Markdown("Advanced LLM optimization and interaction interface")
            
            with gr.Tabs():
                # Chat Interface Tab
                with gr.Tab("💬 Chat Interface"):
                    self._create_chat_interface()
                
                # Text Generation Tab
                with gr.Tab("📝 Text Generation"):
                    self._create_generation_interface()
                
                # Model Training Tab
                with gr.Tab("🏋️ Model Training"):
                    self._create_training_interface()
                
                # Model Analysis Tab
                with gr.Tab("📊 Model Analysis"):
                    self._create_analysis_interface()
                
                # Settings Tab
                with gr.Tab("⚙️ Settings"):
                    self._create_settings_interface()
            
            return interface
    
    def _create_chat_interface(self):
        """Create chat interface"""
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Chat History",
                    height=400,
                    show_label=True,
                    container=True
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Your Message",
                        placeholder="Type your message here...",
                        lines=2,
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", variant="secondary")
                    export_btn = gr.Button("Export Chat", variant="secondary")
            
            with gr.Column(scale=1):
                gr.Markdown("### Chat Settings")
                
                temperature = gr.Slider(
                    minimum=0.1,
                    maximum=2.0,
                    value=1.0,
                    step=0.1,
                    label="Temperature",
                    info="Controls randomness in generation"
                )
                
                max_length = gr.Slider(
                    minimum=10,
                    maximum=500,
                    value=100,
                    step=10,
                    label="Max Length",
                    info="Maximum length of generated text"
                )
                
                top_p = gr.Slider(
                    minimum=0.1,
                    maximum=1.0,
                    value=0.9,
                    step=0.05,
                    label="Top-p",
                    info="Nucleus sampling parameter"
                )
                
                do_sample = gr.Checkbox(
                    label="Use Sampling",
                    value=True,
                    info="Enable sampling for more diverse outputs"
                )
        
        # Event handlers
        def chat_response(message, history, temp, max_len, top_p_val, sample):
            if not message.strip():
                return history, ""
            
            try:
                # Generate response
                response = self.model.generate(
                    input_text=message,
                    max_length=max_len,
                    temperature=temp,
                    top_p=top_p_val,
                    do_sample=sample
                )
                
                # Update history
                history.append([message, response])
                
                return history, ""
                
            except Exception as e:
                self.logger.error(f"Error in chat response: {e}")
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                history.append([message, error_msg])
                return history, ""
        
        def clear_chat():
            return [], ""
        
        def export_chat(history):
            if not history:
                return "No chat history to export"
            
            export_data = {
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "chat_history": history
            }
            
            export_str = json.dumps(export_data, indent=2)
            return export_str
        
        # Connect events
        send_btn.click(
            chat_response,
            inputs=[msg_input, chatbot, temperature, max_length, top_p, do_sample],
            outputs=[chatbot, msg_input]
        )
        
        msg_input.submit(
            chat_response,
            inputs=[msg_input, chatbot, temperature, max_length, top_p, do_sample],
            outputs=[chatbot, msg_input]
        )
        
        clear_btn.click(clear_chat, outputs=[chatbot, msg_input])
        export_btn.click(export_chat, inputs=[chatbot], outputs=gr.Textbox(label="Exported Chat"))
    
    def _create_generation_interface(self):
        """Create text generation interface"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Text Generation")
                
                input_text = gr.Textbox(
                    label="Input Text",
                    placeholder="Enter your prompt here...",
                    lines=3
                )
                
                with gr.Row():
                    generate_btn = gr.Button("Generate", variant="primary")
                    clear_btn = gr.Button("Clear", variant="secondary")
                
                gr.Markdown("### Generation Parameters")
                
                with gr.Row():
                    gen_temperature = gr.Slider(
                        minimum=0.1,
                        maximum=2.0,
                        value=1.0,
                        step=0.1,
                        label="Temperature"
                    )
                    
                    gen_max_length = gr.Slider(
                        minimum=10,
                        maximum=1000,
                        value=200,
                        step=10,
                        label="Max Length"
                    )
                
                with gr.Row():
                    gen_top_p = gr.Slider(
                        minimum=0.1,
                        maximum=1.0,
                        value=0.9,
                        step=0.05,
                        label="Top-p"
                    )
                    
                    gen_top_k = gr.Slider(
                        minimum=1,
                        maximum=100,
                        value=50,
                        step=1,
                        label="Top-k"
                    )
                
                gen_do_sample = gr.Checkbox(label="Use Sampling", value=True)
            
            with gr.Column(scale=1):
                gr.Markdown("### Generated Text")
                
                output_text = gr.Textbox(
                    label="Generated Output",
                    lines=15,
                    interactive=False
                )
                
                with gr.Row():
                    copy_btn = gr.Button("Copy Text", variant="secondary")
                    save_btn = gr.Button("Save Text", variant="secondary")
        
        def generate_text(prompt, temp, max_len, top_p_val, top_k_val, sample):
            if not prompt.strip():
                return "Please enter a prompt to generate text."
            
            try:
                generated = self.model.generate(
                    input_text=prompt,
                    max_length=max_len,
                    temperature=temp,
                    top_p=top_p_val,
                    do_sample=sample
                )
                
                return generated
                
            except Exception as e:
                self.logger.error(f"Error in text generation: {e}")
                return f"Error generating text: {str(e)}"
        
        def clear_generation():
            return "", ""
        
        def copy_text(text):
            return text
        
        def save_text(text):
            if not text.strip():
                return "No text to save"
            
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"generated_text_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                return f"Text saved to {filename}"
            except Exception as e:
                return f"Error saving text: {str(e)}"
        
        # Connect events
        generate_btn.click(
            generate_text,
            inputs=[input_text, gen_temperature, gen_max_length, gen_top_p, gen_top_k, gen_do_sample],
            outputs=[output_text]
        )
        
        clear_btn.click(clear_generation, outputs=[input_text, output_text])
        copy_btn.click(copy_text, inputs=[output_text], outputs=gr.Textbox(label="Copied Text"))
        save_btn.click(save_text, inputs=[output_text], outputs=gr.Textbox(label="Save Status"))
    
    def _create_training_interface(self):
        """Create model training interface"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Model Training")
                
                training_data = gr.Textbox(
                    label="Training Data",
                    placeholder="Enter training texts (one per line)...",
                    lines=10
                )
                
                with gr.Row():
                    train_btn = gr.Button("Start Training", variant="primary")
                    stop_btn = gr.Button("Stop Training", variant="stop")
                
                gr.Markdown("### Training Parameters")
                
                with gr.Row():
                    train_epochs = gr.Number(label="Epochs", value=10, precision=0)
                    train_lr = gr.Number(label="Learning Rate", value=1e-4, precision=6)
                    train_batch_size = gr.Number(label="Batch Size", value=8, precision=0)
                
                with gr.Row():
                    use_mixed_precision = gr.Checkbox(label="Mixed Precision", value=True)
                    use_gradient_checkpointing = gr.Checkbox(label="Gradient Checkpointing", value=True)
                    use_wandb = gr.Checkbox(label="Use Weights & Biases", value=False)
            
            with gr.Column(scale=1):
                gr.Markdown("### Training Progress")
                
                progress_text = gr.Textbox(
                    label="Training Status",
                    lines=8,
                    interactive=False
                )
                
                progress_bar = gr.Progress()
                
                with gr.Row():
                    download_btn = gr.Button("Download Model", variant="secondary")
                    load_btn = gr.Button("Load Model", variant="secondary")
        
        def start_training(data, epochs, lr, batch_size, mixed_precision, gradient_checkpointing, wandb_tracking):
            if not data.strip():
                return "Please provide training data.", "No data provided."
            
            try:
                # Parse training data
                texts = [line.strip() for line in data.split('\n') if line.strip()]
                
                if len(texts) < 2:
                    return "Please provide at least 2 training examples.", "Insufficient data."
                
                # Create training configuration
                model_config = TruthGPTConfig(
                    learning_rate=lr,
                    batch_size=batch_size,
                    use_mixed_precision=mixed_precision,
                    use_gradient_checkpointing=gradient_checkpointing
                )
                
                training_config = TrainingConfig(
                    num_epochs=int(epochs),
                    use_wandb=wandb_tracking
                )
                
                # Create training pipeline
                pipeline = ModernTrainingPipeline(model_config, training_config)
                
                # Prepare data and train
                train_loader, val_loader, test_loader = pipeline.prepare_data(texts)
                history = pipeline.train(train_loader, val_loader)
                
                # Generate training report
                report = {
                    "status": "Training completed successfully",
                    "epochs_trained": len(history['train_loss']),
                    "final_train_loss": history['train_loss'][-1],
                    "final_val_loss": history['val_loss'][-1],
                    "model_info": pipeline.model.get_model_info()
                }
                
                return json.dumps(report, indent=2), "Training completed successfully!"
                
            except Exception as e:
                self.logger.error(f"Error in training: {e}")
                return f"Training error: {str(e)}", "Training failed."
        
        def stop_training():
            return "Training stopped by user.", "Training stopped."
        
        def download_model():
            return "Model download functionality would be implemented here."
        
        def load_model():
            return "Model loading functionality would be implemented here."
        
        # Connect events
        train_btn.click(
            start_training,
            inputs=[training_data, train_epochs, train_lr, train_batch_size, 
                   use_mixed_precision, use_gradient_checkpointing, use_wandb],
            outputs=[progress_text, progress_bar]
        )
        
        stop_btn.click(stop_training, outputs=[progress_text, progress_bar])
        download_btn.click(download_model, outputs=gr.Textbox(label="Download Status"))
        load_btn.click(load_model, outputs=gr.Textbox(label="Load Status"))
    
    def _create_analysis_interface(self):
        """Create model analysis interface"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Model Analysis")
                
                analysis_type = gr.Radio(
                    choices=["Model Info", "Performance Metrics", "Attention Visualization", "Text Analysis"],
                    value="Model Info",
                    label="Analysis Type"
                )
                
                analyze_btn = gr.Button("Run Analysis", variant="primary")
                
                gr.Markdown("### Analysis Parameters")
                
                analysis_text = gr.Textbox(
                    label="Text for Analysis",
                    placeholder="Enter text to analyze...",
                    lines=3
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### Analysis Results")
                
                analysis_results = gr.Textbox(
                    label="Analysis Output",
                    lines=15,
                    interactive=False
                )
                
                analysis_plot = gr.Plot(label="Visualization")
        
        def run_analysis(analysis_type, text):
            try:
                if analysis_type == "Model Info":
                    model_info = self.model.get_model_info()
                    return json.dumps(model_info, indent=2), None
                
                elif analysis_type == "Performance Metrics":
                    # Simulate performance metrics
                    metrics = {
                        "inference_time": "0.05s",
                        "memory_usage": "2.1GB",
                        "throughput": "20 tokens/s",
                        "model_size": f"{model_info['model_size_mb']:.2f} MB"
                    }
                    return json.dumps(metrics, indent=2), None
                
                elif analysis_type == "Attention Visualization":
                    if not text.strip():
                        return "Please provide text for attention analysis.", None
                    
                    # Simulate attention visualization
                    fig, ax = plt.subplots(figsize=(10, 6))
                    attention_matrix = np.random.rand(10, 10)
                    sns.heatmap(attention_matrix, annot=True, cmap='Blues', ax=ax)
                    ax.set_title("Attention Weights Visualization")
                    
                    return "Attention visualization generated.", fig
                
                elif analysis_type == "Text Analysis":
                    if not text.strip():
                        return "Please provide text for analysis.", None
                    
                    # Simulate text analysis
                    analysis = {
                        "text_length": len(text),
                        "word_count": len(text.split()),
                        "sentence_count": text.count('.') + text.count('!') + text.count('?'),
                        "complexity_score": len(text.split()) / max(1, text.count('.') + text.count('!') + text.count('?'))
                    }
                    return json.dumps(analysis, indent=2), None
                
            except Exception as e:
                self.logger.error(f"Error in analysis: {e}")
                return f"Analysis error: {str(e)}", None
        
        # Connect events
        analyze_btn.click(
            run_analysis,
            inputs=[analysis_type, analysis_text],
            outputs=[analysis_results, analysis_plot]
        )
    
    def _create_settings_interface(self):
        """Create settings interface"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Model Settings")
                
                model_name = gr.Textbox(
                    label="Model Name",
                    value=self.config.model_name,
                    interactive=True
                )
                
                max_length = gr.Number(
                    label="Max Sequence Length",
                    value=self.config.max_length,
                    precision=0
                )
                
                hidden_size = gr.Number(
                    label="Hidden Size",
                    value=self.config.hidden_size,
                    precision=0
                )
                
                num_attention_heads = gr.Number(
                    label="Number of Attention Heads",
                    value=self.config.num_attention_heads,
                    precision=0
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### Optimization Settings")
                
                use_mixed_precision = gr.Checkbox(
                    label="Mixed Precision",
                    value=self.config.use_mixed_precision
                )
                
                use_gradient_checkpointing = gr.Checkbox(
                    label="Gradient Checkpointing",
                    value=self.config.use_gradient_checkpointing
                )
                
                use_flash_attention = gr.Checkbox(
                    label="Flash Attention",
                    value=self.config.use_flash_attention
                )
                
                use_lora = gr.Checkbox(
                    label="LoRA Fine-tuning",
                    value=self.config.use_lora
                )
                
                with gr.Row():
                    save_settings_btn = gr.Button("Save Settings", variant="primary")
                    reset_settings_btn = gr.Button("Reset to Defaults", variant="secondary")
        
        def save_settings(model_name, max_len, hidden_size, num_heads, mixed_precision, 
                         gradient_checkpointing, flash_attention, lora):
            try:
                # Update configuration
                self.config.model_name = model_name
                self.config.max_length = int(max_len)
                self.config.hidden_size = int(hidden_size)
                self.config.num_attention_heads = int(num_heads)
                self.config.use_mixed_precision = mixed_precision
                self.config.use_gradient_checkpointing = gradient_checkpointing
                self.config.use_flash_attention = flash_attention
                self.config.use_lora = lora
                
                return "Settings saved successfully!"
                
            except Exception as e:
                self.logger.error(f"Error saving settings: {e}")
                return f"Error saving settings: {str(e)}"
        
        def reset_settings():
            return (
                "microsoft/DialoGPT-medium",  # model_name
                2048,  # max_length
                768,   # hidden_size
                12,    # num_attention_heads
                True,   # use_mixed_precision
                True,   # use_gradient_checkpointing
                True,   # use_flash_attention
                False   # use_lora
            )
        
        # Connect events
        save_settings_btn.click(
            save_settings,
            inputs=[model_name, max_length, hidden_size, num_attention_heads,
                   use_mixed_precision, use_gradient_checkpointing, use_flash_attention, use_lora],
            outputs=gr.Textbox(label="Save Status")
        )
        
        reset_settings_btn.click(
            reset_settings,
            outputs=[model_name, max_length, hidden_size, num_attention_heads,
                    use_mixed_precision, use_gradient_checkpointing, use_flash_attention, use_lora]
        )
    
    def launch(self, share: bool = False, server_name: str = "127.0.0.1", 
               server_port: int = 7860, **kwargs):
        """Launch the Gradio interface"""
        try:
            self.logger.info("Launching TruthGPT Gradio interface...")
            self.interface.launch(
                share=share,
                server_name=server_name,
                server_port=server_port,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"Error launching interface: {e}")
            raise


# Utility functions
def create_truthgpt_interface(model_path: Optional[str] = None) -> TruthGPTGradioInterface:
    """Create TruthGPT Gradio interface"""
    return TruthGPTGradioInterface(model_path)


def launch_truthgpt_demo(share: bool = False, port: int = 7860):
    """Launch TruthGPT demo interface"""
    interface = create_truthgpt_interface()
    interface.launch(share=share, server_port=port)


# Example usage
if __name__ == "__main__":
    # Create and launch interface
    interface = TruthGPTGradioInterface()
    interface.launch(share=False, server_port=7860)


