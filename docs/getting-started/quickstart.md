# Quick Start Guide

Get up and running with model training, high-throughput inference serving, and autonomous agent swarms in under 5 minutes.

---

## 📋 1. Prerequisites Check

Verify your Python environment and hardware setup:

```bash
# Ensure Python 3.10+ is available
python --version

# Run the TruthGPT environment diagnostic check
python utils/health_check.py
```

Expected output:
```text
[✓] Python Environment: 3.11.x
[✓] PyTorch Version: 2.3.0+cu121
[✓] CUDA Device: NVIDIA RTX 4090 / A100 (Compute Capability 8.9 / 8.0)
[✓] Memory Available: 24.0 GB VRAM / 64.0 GB Host RAM
[✓] Triton Compiler: Available
[✓] Environment Status: READY FOR HIGH-PERFORMANCE WORKLOADS
```

---

## 🏋️ 2. Training Your First Model

### Option A: CLI Training with Preset Configurations (Fastest)

TruthGPT includes production-tested YAML presets for standard hardware targets:

```bash
# Launch training using an optimized 1B parameter preset
python train_llm.py --preset configs/presets/transformer_1b_sota.yaml

# Override parameters on the fly via CLI
python train_llm.py --preset configs/presets/transformer_1b_sota.yaml \
    --batch-size 64 \
    --optimizer soap \
    --compile \
    --amp bf16
```

### Option B: Python SDK Training

```python
from trainers.config import TrainerConfig
from trainers.trainer import GenericTrainer
from models.transformer import TransformerModel
from data.pipeline import DynamicBucketingDataset

# 1. Initialize strongly-typed trainer configuration
config = TrainerConfig(
    model_name="quickstart-model",
    batch_size=32,
    learning_rate=3e-4,
    optimizer_type="soap",       # 2nd-order SOTA optimizer
    use_amp=True,                # Mixed precision (BF16/FP16)
    use_flash_attention=True,    # O(N) memory complexity
    compile_model=True,          # PyTorch 2.x TorchInductor JIT
    max_epochs=5,
    save_checkpoint_freq=1
)

# 2. Instantiate Model and Dataset
model = TransformerModel(vocab_size=32000, d_model=768, n_heads=12, n_layers=12)
dataset = DynamicBucketingDataset.from_jsonl("data/sample_dataset.jsonl", max_seq_len=1024)

# 3. Fit model
trainer = GenericTrainer(model=model, config=config, train_dataset=dataset)
metrics = trainer.fit()

print(f"Training completed successfully. Final loss: {metrics['final_train_loss']:.4f}")
```

---

## 🔮 3. High-Throughput Inference Serving

TruthGPT provides a high-throughput inference engine with continuous batching and Paged KV-Cache:

### Starting the Serving Engine via CLI

```bash
# Start OpenAI-compatible REST server on port 8080 with Speculative Decoding
python cli.py serve --port 8080 --model-path checkpoints/best_model.pt --enable-speculative-decoding
```

### Streaming Completions in Python

```python
from inference.engine import InferenceEngine
from inference.config import GenerationConfig

# 1. Initialize engine with Paged KV-Cache
engine = InferenceEngine.from_pretrained("checkpoints/best_model.pt")

# 2. Configure generation parameters
gen_config = GenerationConfig(
    max_new_tokens=128,
    temperature=0.7,
    top_p=0.9,
    repetition_penalty=1.1
)

# 3. Stream generated tokens
prompt = "Explain quantum entanglement in simple terms:"
for token in engine.generate_stream(prompt, config=gen_config):
    print(token, end="", flush=True)
print()
```

---

## 🐝 4. OpenClaw Autonomous Agent Swarms

OpenClaw is TruthGPT's autonomous agent framework featuring ReAct reasoning loops, dynamic tool calling, reflection, and multi-agent coordination.

### Command Line Swarm Query

```bash
# Query the autonomous agent swarm
openclaw swarm ask "Analyze GPU memory bandwidth utilization during 4-bit quantized KV-Cache serving."

# Persistent session with user context memory
openclaw swarm ask "Generate a LoRA fine-tuning configuration for Llama-3" --user engineer_1
```

### Python SDK Multi-Agent Client

```python
import asyncio
from openclaw import AgentClient, AgentConfig

async def run_agent():
    # 1. Configure agent client with Swarm & Reflection
    config = AgentConfig(
        use_swarm=True,
        max_handoff_depth=4,
        use_reflexion=True,
        use_vector_memory=True,
        default_agent_name="ResearchAgent"
    )
    client = AgentClient(config=config)

    # 2. Run query through the multi-agent swarm
    response = await client.run(
        user_id="researcher_01",
        prompt="Synthesize the key architectural differences between Muon and SOAP optimizers.",
        return_response=True
    )

    print(f"Executing Agent: {response.agent_name}")
    print(f"Response:\n{response.content}")

if __name__ == "__main__":
    asyncio.run(run_agent())
```

---

## 📚 5. Next Steps

- Explore the [Installation Guide](installation.md) for full CUDA matrix and native compilation.
- Understand the [Configuration System](configuration.md) to customize hyperparameters and presets.
- Dive into the [Core Architecture](../core-architecture/overview.md) to understand system internals.
- Explore [Hardware Acceleration & Optimizers](../optimization/acceleration_guide.md) to supercharge training speeds.
