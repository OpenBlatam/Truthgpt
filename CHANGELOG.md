# Changelog

Todas las mejoras notables de este proyecto serán documentadas en este archivo.

## [1.0.0] - 2025-01-XX

### ✨ Added - Sistema Modular Completo

#### Arquitectura
- Sistema de registries modular (`factories/registry.py`)
- 8 registries implementadas:
  - Attention backends (sdpa|flash|triton)
  - KV cache (none|paged)
  - Memory management (adaptive|static)
  - Optimizers (adamw|lion|adafactor)
  - Callbacks (print|wandb|tensorboard)
  - Datasets (hf|jsonl|webdataset)
  - Collate functions (lm|cv)
  - Metrics (loss|ppl)

#### GenericTrainer
- Mixed precision training (bf16/fp16)
- TF32 acceleration support
- torch.compile integration
- Fused AdamW optimizer
- EMA weights para evaluación
- Gradient clipping + NaN detection
- Periodic checkpointing con pruning
- Auto-resume desde último checkpoint
- Dynamic padding + length bucketing
- Tokens/sec tracking en tiempo real
- Perplexity calculation
- Early stopping configurable por métrica

#### Performance Optimizations
- TF32 para matmul en GPUs Ampere+
- torch.compile con modos: default|reduce-overhead|max-autotune
- SDPA/Flash attention backends
- Dynamic padding optimizado
- Length bucketing para batches homogéneos
- Prefetch factor + persistent workers
- Non-blocking data loading

#### Datasets & Data Loading
- HuggingFace datasets con streaming opcional
- JSONL file support
- WebDataset stub (preparado para futuro)
- Dynamic collate functions
- Length-based bucketing

#### Observabilidad
- Weights & Biases integration
- TensorBoard integration
- Print logger básico
- Tokens/sec tracking
- Perplexity reporting
- Custom metrics registry

#### Configuración
- Configuración unificada vía YAML
- Validador de configuración (`validate_config.py`)
- Builder modular (`build_trainer.py`)
- Ejemplos de configuración múltiples

#### Herramientas de Desarrollo
- Makefile con comandos comunes
- Scripts de setup automático (Linux/Windows)
- Tests unitarios básicos
- Script de validación de config
- Ejemplos prácticos

#### Documentación
- README.md completo
- QUICK_REFERENCE.md para comandos rápidos
- ARCHITECTURE.md con diseño del sistema
- CONTRIBUTING.md para contribuidores
- Ejemplos en `examples/`

### 🔧 Fixed
- NaN detection y step skipping
- Memory management mejorado
- Error handling en registries

### 📝 Changed
- Arquitectura completamente modular
- Todo configurable vía YAML sin código
- Fallbacks automáticos para componentes opcionales

---

## [Unreleased]

### Planned
- Schedulers modulares (cosine/linear/one-cycle)
- Distributed training (accelerate/DeepSpeed/FSDP)
- Inference backends (vLLM/TensorRT-LLM)
- Decoding strategies (greedy/top-k/nucleus/contrastive)
- Más métricas de evaluación (BLEU, ROUGE)
- Quantization support (int8/int4)
- Model distillation pipelines

---

## Formato

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

### Tipos de Cambios
- **Added** para nuevas funcionalidades
- **Changed** para cambios en funcionalidades existentes
- **Deprecated** para funcionalidades próximas a ser eliminadas
- **Removed** para funcionalidades eliminadas
- **Fixed** para corrección de bugs
- **Security** para vulnerabilidades


