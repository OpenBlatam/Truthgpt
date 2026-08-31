# 📚 TruthGPT Optimization Core - Documentation Index

Quick index to find the exact documentation or technical guide you need.

## 🌐 Enterprise Documentation Portal & Local Server

The complete, interactive documentation portal is located in `docs/`:

- **Interactive Local Docs Server**: `python docs/serve_docs.py` (Browse at `http://localhost:8000`)
- **[Documentation Hub](docs/index.md)** - Master Portal & Navigation Matrix
- **[Getting Started](docs/getting_started/index.md)** - Installation, Quickstarts & Diagnostics
- **[Architecture & Design](docs/architecture/index.md)** - Stratified System Design, PiMoE & Polyglot
- **[Engineering Guides](docs/guides/index.md)** - Performance Tuning, Distributed & Custom Kernels
- **[Tutorials](docs/tutorials/index.md)** - Step-by-Step LoRA, Serving & Research Tutorials
- **[API Reference](docs/api/index.md)** - Programmatic API Catalog
- **[Examples & Recipes](docs/examples/index.md)** - Runnable End-to-End Recipes
- **[Suite en Español](docs/spanish/index.md)** - Documentación completa y guías en español
- **[Historical Archive](docs/archive/index.md)** - Evolution, Refactoring Logs & Proposals

---

## 🚀 Root Files & Quick Reference

- **Quick Start Guide** → [`README.md`](README.md)
- **Fast Commands Reference** → [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md)
- **System Architecture Summary** → [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **Contribution Guidelines** → [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Changelog & Releases** → [`CHANGELOG.md`](CHANGELOG.md)


## 🔧 Herramientas

| Herramienta | Descripción | Uso |
|-------------|-------------|-----|
| `validate_config.py` | Valida configuración YAML | Antes de entrenar |
| `init_project.py` | Crea proyecto nuevo | Nuevo experimento |
| `Makefile` | Comandos comunes | `make help` para ver todos |
| `setup_dev.sh/.ps1` | Setup automático | Primera instalación |

## 📁 Configuraciones

| Archivo | Descripción |
|---------|-------------|
| `configs/llm_default.yaml` | Configuración por defecto completa |
| `configs/presets/lora_fast.yaml` | LoRA rápido y eficiente |
| `configs/presets/performance_max.yaml` | Máxima performance en GPU |
| `configs/presets/debug.yaml` | Modo debug para desarrollo |

## 💻 Scripts y Ejemplos

| Script | Descripción |
|--------|-------------|
| `train_llm.py` | CLI principal de entrenamiento |
| `demo_gradio_llm.py` | Demo interactiva Gradio |
| `examples/benchmark_tokens_per_sec.py` | Benchmark de performance |
| `examples/train_with_datasets.py` | Uso de datasets modulares |
| `examples/switch_attention_backend.py` | Cambio de backends |
| `examples/complete_workflow.py` | Demo completo con 6 configuraciones |

## 🏗️ Código Core

| Módulo | Descripción |
|--------|-------------|
| `trainers/trainer.py` | GenericTrainer principal |
| `build_trainer.py` | Builder que ensambla componentes |
| `build.py` | Construcción modular de componentes |
| `factories/*.py` | 8 registries modulares |

## 🧪 Tests

| Test | Descripción |
|------|-------------|
| `tests/test_basic.py` | Tests unitarios básicos |

## 🎯 Casos de Uso Comunes

### "Quiero entrenar rápido con LoRA"
1. `make train-lora` o
2. `python train_llm.py --config configs/presets/lora_fast.yaml`

### "Quiero máxima performance"
1. `make train-perf` o
2. `python train_llm.py --config configs/presets/performance_max.yaml`

### "Quiero debuggear un problema"
1. `make train-debug` o
2. `python train_llm.py --config configs/presets/debug.yaml`

### "Quiero crear un nuevo proyecto"
```bash
python init_project.py mi_proyecto --preset lora_fast --model gpt2
python train_llm.py --config configs/mi_proyecto.yaml
```

### "Quiero validar mi config antes de entrenar"
```bash
python validate_config.py configs/mi_config.yaml
# o
make validate
```

### "Quiero hacer benchmark"
```bash
make benchmark
# o
python examples/benchmark_tokens_per_sec.py --model gpt2 --dtype bf16
```

## 🔍 Búsqueda Rápida

- **Configuración YAML**: Ver `README.md` sección "Configuración YAML Completa"
- **Registries disponibles**: Ver `ARCHITECTURE.md` sección "Componentes Modulares"
- **Troubleshooting**: Ver `README.md` sección "Troubleshooting"
- **Cómo contribuir**: Ver `CONTRIBUTING.md`
- **Comandos Make**: `make help` o ver `QUICK_REFERENCE.md`

## 📞 Ayuda

- Revisa `README.md` primero
- Consulta `QUICK_REFERENCE.md` para comandos
- Ver `ARCHITECTURE.md` para entender el diseño
- Abre un issue en el repositorio para bugs/features

---

**Última actualización**: v1.0.0 - Sistema Modular Completo


