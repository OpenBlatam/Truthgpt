# 🚀 TruthGPT Optimization Core - Modular LLM Training System

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.1+-orange)
![CUDA](https://img.shields.io/badge/CUDA-11.8%2F12.x-green)
![Status](https://img.shields.io/badge/Status-Production--ready-success)

Sistema modular de entrenamiento LLM con arquitectura extensible vía registries, configuración YAML unificada, y optimizaciones de performance listas para producción.

## 🎯 Características Principales

✅ **Arquitectura Modular**
- Registries intercambiables (attention, optimizer, datasets, callbacks, etc.)
- Todo configurable vía YAML sin tocar código
- Fallbacks automáticos y componentes opcionales

✅ **Performance Optimizations**
- TF32 acceleration (Ampere+ GPUs)
- torch.compile support
- Fused AdamW optimizer
- SDPA/Flash attention backends
- Dynamic padding + length bucketing
- Prefetch + persistent workers

✅ **Estabilidad & Robustez**
- EMA weights para evaluación
- Gradient clipping + NaN detection
- Periodic checkpointing con pruning
- Auto-resume desde último checkpoint
- Early stopping por métrica configurable

✅ **Observabilidad**
- W&B y TensorBoard integration
- Tokens/sec tracking en tiempo real
- Perplexity reporting
- Custom metrics registry

## 🚀 Quick Start

### Instalación de Dependencias

**Instalación básica:**
```bash
pip install -r requirements_advanced.txt
```

**Instalación de dependencias opcionales:**
```bash
# Ver opciones disponibles
python install_extras.py --list

# Instalar W&B
python install_extras.py wandb

# Instalar todas las opcionales
python install_extras.py all

# Verificar qué está instalado
python install_extras.py --check
```

### Instalación Automática

**Linux/Mac:**
```bash
cd optimization_core
chmod +x setup_dev.sh
./setup_dev.sh
```

**Windows (PowerShell):**
```powershell
cd optimization_core
.\setup_dev.ps1
```

**Manual:**
```bash
cd optimization_core
pip install -r requirements_advanced.txt
```

### Entrenamiento Básico

```bash
# Opción 1: Configuración por defecto
python train_llm.py --config configs/llm_default.yaml

# Opción 2: Usar preset (rápido)
python train_llm.py --config configs/presets/lora_fast.yaml

# Opción 3: Crear proyecto nuevo
python init_project.py mi_proyecto --preset lora_fast --model gpt2
python train_llm.py --config configs/mi_proyecto.yaml
```

### Personalización (solo YAML)

Edita `configs/llm_default.yaml`:

```yaml
model:
  name_or_path: gpt2  # Cambiar modelo aquí
  lora:
    enabled: true     # Activar LoRA

training:
  callbacks: [print, wandb]  # Activar logging
  allow_tf32: true
  torch_compile: true

optimizer:
  type: adamw  # adamw|lion|adafactor

data:
  source: hf  # hf|jsonl|webdataset
  streaming: false
  bucket_by_length: true
```

## 📁 Estructura del Proyecto

```
optimization_core/
├── configs/
│   └── llm_default.yaml          # Configuración unificada
├── factories/
│   ├── registry.py                # Sistema base de registries
│   ├── attention.py               # Backends: sdpa|flash|triton
│   ├── kv_cache.py                # none|paged
│   ├── memory.py                  # adaptive|static
│   ├── optimizer.py               # adamw|lion|adafactor
│   ├── callbacks.py               # print|wandb|tensorboard
│   ├── datasets.py                # hf|jsonl|webdataset
│   ├── collate.py                 # lm|cv (dynamic padding)
│   └── metrics.py                 # loss|ppl
├── trainers/
│   ├── trainer.py                 # GenericTrainer principal
│   └── callbacks.py               # Sistema de callbacks
├── modules/
│   ├── attention/
│   │   ├── ultra_efficient_kv_cache.py
│   │   └── attn_autotune.py
│   └── memory/
│       └── advanced_memory_manager.py
├── build.py                       # Construcción de componentes
├── build_trainer.py               # Builder principal
├── train_llm.py                   # CLI de entrenamiento
├── demo_gradio_llm.py             # Demo interactiva
└── examples/
    ├── benchmark_tokens_per_sec.py
    ├── train_with_datasets.py
    └── switch_attention_backend.py
```

## 📋 Configuración YAML Completa

### Estructura Básica

```yaml
seed: 42
run_name: llm_baseline
output_dir: runs/llm_baseline

model:
  name_or_path: gpt2
  gradient_checkpointing: true
  attention:
    backend: sdpa  # sdpa|flash|triton
  kv_cache:
    type: paged  # none|paged
    block_size: 128
  memory:
    policy: adaptive  # adaptive|static
  lora:
    enabled: false
    r: 16
    alpha: 32
    dropout: 0.05

training:
  epochs: 3
  train_batch_size: 8
  eval_batch_size: 8
  grad_accum_steps: 2
  learning_rate: 5.0e-5
  weight_decay: 0.01
  warmup_ratio: 0.06
  scheduler: cosine
  mixed_precision: bf16  # bf16|fp16|none
  early_stopping_patience: 2
  allow_tf32: true
  torch_compile: false
  compile_mode: default
  fused_adamw: true
  detect_anomaly: false
  save_safetensors: true
  callbacks:
    - print
    # - wandb
    # - tensorboard

optimizer:
  type: adamw  # adamw|lion|adafactor
  fused: true

data:
  source: hf  # hf|jsonl|webdataset
  dataset: wikitext
  subset: wikitext-2-raw-v1
  text_field: text
  streaming: false
  collate: lm  # lm|cv
  max_seq_len: 512
  bucket_by_length: false
  bucket_bins: [64, 128, 256, 512]
  num_workers: 4
  prefetch_factor: 2
  persistent_workers: true

checkpoint:
  interval_steps: 1000
  keep_last: 3

ema:
  enabled: true
  decay: 0.999

resume:
  enabled: false
  checkpoint_dir: null

eval:
  metrics: [ppl]
  select_best_by: ppl  # ppl|loss

logging:
  project: truthgpt
  run_name: llm_baseline
  dir: runs

hardware:
  device: auto  # auto|cuda|cpu|mps
```

## 🛠️ Comandos Útiles (Makefile)

```bash
make help        # Ver todos los comandos disponibles
make install     # Instalar dependencias
make validate    # Validar configuración YAML
make train       # Entrenar en GPU
make train-cpu   # Entrenar en CPU
make benchmark   # Benchmark de tokens/s
make demo        # Demo interactiva Gradio
make test        # Ejecutar tests básicos
make clean       # Limpiar checkpoints y caché
```

## 🎯 Configuraciones Predefinidas (Presets)

Configuraciones optimizadas para casos de uso comunes:

### `configs/presets/lora_fast.yaml`
**LoRA Fast Training** - Entrenamiento rápido y eficiente en memoria
- LoRA activado (rank 8)
- Secuencias cortas (256 tokens)
- Bucketing activado
- Ideal para pruebas rápidas

```bash
python train_llm.py --config configs/presets/lora_fast.yaml
```

### `configs/presets/performance_max.yaml`
**Maximum Performance** - Máxima velocidad en GPU
- torch.compile con max-autotune
- TF32 activado
- Bucketing optimizado
- Workers y prefetch maximizados
- EMA activado

```bash
python train_llm.py --config configs/presets/performance_max.yaml
```

### `configs/presets/debug.yaml`
**Debug Mode** - Para debugging y desarrollo
- Detección de anomalías activada
- Mixed precision desactivado
- Logging muy detallado
- Single-threaded
- Ideal para encontrar bugs

```bash
python train_llm.py --config configs/presets/debug.yaml
```

### Crear Proyecto desde Preset

```bash
# Crear proyecto nuevo basado en preset
python init_project.py mi_experimento --preset lora_fast --model gpt2

# Esto crea: configs/mi_experimento.yaml
# Luego entrena con:
python train_llm.py --config configs/mi_experimento.yaml
```

## 🔧 Ejemplos de Uso

### 1. Entrenamiento con LoRA

```yaml
model:
  name_or_path: gpt2
  lora:
    enabled: true
    r: 16
    alpha: 32
training:
  mixed_precision: bf16
```

### 2. Activar W&B Logging

```yaml
training:
  callbacks: [print, wandb]
logging:
  project: my-project
  run_name: experiment-1
```

### 3. Usar Datasets en Streaming

```yaml
data:
  source: hf
  dataset: wikitext
  streaming: true
  collate: lm
```

### 4. Optimizar Performance

```yaml
training:
  allow_tf32: true
  torch_compile: true
  compile_mode: max-autotune
  fused_adamw: true
data:
  bucket_by_length: true
  bucket_bins: [64, 128, 256, 512]
```

### 5. Auto-resume desde Checkpoint

```yaml
resume:
  enabled: true
  checkpoint_dir: null  # Usa output_dir si null
checkpoint:
  interval_steps: 1000
  keep_last: 3
```

## 🔧 Utilidades Adicionales

### Health Check

```bash
# Verificar que todo esté configurado correctamente
python utils/health_check.py
# o
make health
```

Verifica:
- Versión de Python
- Paquetes instalados (torch, transformers, etc.)
- Disponibilidad de CUDA
- Archivos de configuración
- Módulos core importables

### Monitoreo en Tiempo Real

```bash
# Monitorear un directorio de run
python utils/monitor_training.py runs/mi_run

# Monitorear con intervalo personalizado
python utils/monitor_training.py runs/mi_run --interval 2.0

# Monitorear archivo de log
python utils/monitor_training.py logs/training.log --file
# o
make monitor
```

Muestra:
- Nuevos checkpoints en tiempo real
- Uso de CPU/RAM
- Uso de GPU y memoria
- Métricas de entrenamiento (si está en el log)

### Visualizar Resultados

```bash
# Resumen de un run
python utils/visualize_training.py runs/mi_run --summary

# Listar checkpoints
python utils/visualize_training.py runs/mi_run --checkpoints

# Comparar múltiples runs
python utils/compare_runs.py --runs-dir runs
# o
make compare
```

### Limpiar Runs Antiguos

```bash
# Dry run (ver qué se eliminaría)
python utils/cleanup_runs.py --days 30 --old-runs

# Limpiar runs más antiguos de 30 días
python utils/cleanup_runs.py --days 30 --old-runs --execute

# Limpiar checkpoints antiguos (mantener últimos 3)
python utils/cleanup_runs.py --keep-checkpoints 3 --checkpoints --execute
```

### Exportar Configuración

```bash
# Exportar config desde un checkpoint
python utils/export_config.py runs/mi_run/best.pt --output configs/reproduce.yaml

# Exportar desde un run completo
python utils/export_config.py runs/mi_run --output configs/reproduce.yaml
```

## 📊 Benchmark de Performance

```bash
python examples/benchmark_tokens_per_sec.py \
  --model gpt2 \
  --dtype bf16 \
  --max_new_tokens 128
```

Compara tokens/s con diferentes configuraciones (TF32 on/off, torch.compile on/off).

## 🧪 Tests y Validación

```bash
# Validar configuración YAML
python validate_config.py configs/llm_default.yaml
# o
make validate

# Ejecutar tests unitarios
pytest tests/test_basic.py -v
# o
make test

# Test básico de importación
python -c "from trainers.trainer import GenericTrainer; print('✅ OK')"
```

### Workflow Completo

Ver todas las variantes de configuración:
```bash
python examples/complete_workflow.py
```

Esto demuestra 6 configuraciones diferentes (basic, LoRA, performance, W&B, streaming, EMA+resume).

## 🐛 Troubleshooting

### CUDA Out of Memory
- Reduce `train_batch_size` o `max_seq_len`
- Activa `gradient_checkpointing: true`
- Usa `mixed_precision: bf16`
- Aumenta `grad_accum_steps`

### Entrenamiento Lento
- Activa `allow_tf32: true` (Ampere+)
- Prueba `torch_compile: true`
- Aumenta `num_workers` y `prefetch_factor`
- Activa `bucket_by_length: true`

### Logging No Funciona
- Verifica instalación: `pip install wandb` o `pip install tensorboard`
- Revisa `logging.project` y `logging.run_name` en YAML
- Asegura que `training.callbacks` incluye el callback deseado

## 🔗 Referencias

- [PyTorch Performance Tuning](https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [W&B Documentation](https://docs.wandb.ai)
- [TensorBoard Guide](https://www.tensorflow.org/tensorboard)

## 📝 Changelog

### v2.1.0 - Enhanced Optimizer Architecture
- ✅ Strategy pattern for optimization techniques
- ✅ Chain of Responsibility pipeline system
- ✅ Improved metrics calculation
- ✅ 75% code reduction (eliminated 15+ repetitive methods per optimizer)
- ✅ Modular, extensible architecture
- ✅ See `REFACTORING_FINAL_SUMMARY.md` for details

### v2.0.0 - Optimizer Refactoring
- ✅ Unified optimizer system (eliminated 14+ duplicate files)
- ✅ Backward compatibility shims for old optimizer classes
- ✅ Component-based architecture for reusable optimizers
- ✅ See `REFACTORING_OPTIMIZERS.md` for migration guide

### v1.0.0 - Modular System Release
- ✅ Sistema de registries completo
- ✅ GenericTrainer con todas las optimizaciones
- ✅ Auto-resume desde checkpoint
- ✅ W&B y TensorBoard integration
- ✅ Datasets modulares (HF, JSONL, WebDataset)
- ✅ EMA weights, periodic checkpointing
- ✅ Dynamic padding + length bucketing
- ✅ Configuración unificada vía YAML

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Ver LICENSE file para detalles.

---

**¡Happy Training! 🚀**
# Truthgpt
