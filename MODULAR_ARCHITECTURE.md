# 🏗️ Arquitectura Modular del Optimization Core

## 📐 Visión General

El código ha sido refactorizado siguiendo principios de **separación de responsabilidades** y **composición sobre herencia** para lograr una arquitectura más modular, testeable y mantenible.

## 🎯 Principios de Diseño

1. **Single Responsibility**: Cada clase tiene una responsabilidad única y bien definida
2. **Composition over Inheritance**: Uso de composición en lugar de herencia cuando es posible
3. **Dependency Injection**: Las dependencias se inyectan en lugar de crearse internamente
4. **Interface Segregation**: Interfaces pequeñas y específicas
5. **Open/Closed Principle**: Abierto para extensión, cerrado para modificación

## 📦 Estructura Modular

### 1. **Config Module** (`trainers/config.py`)

Configuración separada en dataclasses especializadas:

- `ModelConfig`: Configuración del modelo (LoRA, gradient checkpointing)
- `TrainingConfig`: Hiperparámetros de entrenamiento
- `HardwareConfig`: Configuración de hardware (GPU, compilación)
- `CheckpointConfig`: Configuración de checkpoints
- `EMAConfig`: Configuración de Exponential Moving Average
- `TrainerConfig`: Configuración completa usando composición

**Beneficios**:
- Type safety con dataclasses
- Validación de configuración
- Serialización/deserialización fácil
- Configuración por capas (composición)

### 2. **Model Manager** (`trainers/model_manager.py`)

Maneja toda la lógica relacionada con modelos:

- Carga de tokenizer y modelo
- Configuración de LoRA
- Detección automática de módulos LoRA por arquitectura
- Aplicación de torch.compile
- Inicialización de pesos
- Setup de multi-GPU (DataParallel/DDP)

**Beneficios**:
- Lógica de modelo aislada
- Fácil de testear independientemente
- Reutilizable en otros contextos

### 3. **Optimizer Manager** (`trainers/optimizer_manager.py`)

Maneja optimización y scheduling:

- Creación de optimizers via registry
- Setup de learning rate schedulers
- Gestión de GradScaler para mixed precision
- Operaciones de optimización (step, zero_grad)

**Beneficios**:
- Lógica de optimización encapsulada
- Fácil intercambio de optimizers
- Testing independiente

### 4. **Data Manager** (`trainers/data_manager.py`)

Maneja todo lo relacionado con datos:

- Creación de DataLoaders
- Dynamic padding y bucketing
- Configuración de workers y prefetching
- Manejo de datasets

**Beneficios**:
- Lógica de datos aislada
- Fácil cambiar estrategias de padding/bucketing
- Testing de pipelines de datos

### 5. **EMA Manager** (`trainers/ema_manager.py`)

Maneja Exponential Moving Average:

- Inicialización de shadow parameters
- Actualización de EMA
- Aplicación/restauración de pesos EMA

**Beneficios**:
- Lógica EMA encapsulada
- Reutilizable
- Testing independiente

### 6. **Evaluator** (`trainers/evaluator.py`)

Maneja evaluación del modelo:

- Evaluación en validation set
- Cálculo de métricas (loss, perplexity)
- Soporte para EMA weights durante evaluación

**Beneficios**:
- Lógica de evaluación separada
- Fácil agregar nuevas métricas
- Testing independiente

### 7. **Checkpoint Manager** (`trainers/checkpoint_manager.py`)

Maneja checkpoints:

- Guardado de checkpoints (best, last, periodic)
- Carga de checkpoints para resume
- Pruning de checkpoints antiguos
- Manejo de estado completo

**Beneficios**:
- Lógica de checkpointing encapsulada
- Fácil cambiar formato de checkpoint
- Testing independiente

## 🔄 Flujo de Datos Modular

```
TrainerConfig (composición de configs especializadas)
    ↓
┌─────────────────────────────────────┐
│  GenericTrainer (Orquestador)      │
│                                     │
│  ┌──────────────┐  ┌─────────────┐│
│  │ ModelManager │  │ DataManager ││
│  └──────────────┘  └─────────────┘│
│                                     │
│  ┌──────────────┐  ┌─────────────┐│
│  │OptimizerMgr  │  │ Evaluator   ││
│  └──────────────┘  └─────────────┘│
│                                     │
│  ┌──────────────┐  ┌─────────────┐│
│  │  EMAManager  │  │CheckpointMgr││
│  └──────────────┘  └─────────────┘│
└─────────────────────────────────────┘
```

## ✅ Ventajas de la Arquitectura Modular

### 1. **Testabilidad**
- Cada módulo puede testearse independientemente
- Mocking de dependencias más fácil
- Tests unitarios más simples

### 2. **Mantenibilidad**
- Código más fácil de entender (menos líneas por archivo)
- Cambios localizados (no afectan otros módulos)
- Debugging más simple

### 3. **Extensibilidad**
- Agregar nuevas funcionalidades sin modificar código existente
- Intercambiar implementaciones fácilmente
- Plugins/extensions más simples

### 4. **Reutilización**
- Los managers pueden usarse en otros contextos
- Composición flexible de componentes
- Compartir lógica entre proyectos

### 5. **Colaboración**
- Múltiples desarrolladores pueden trabajar en paralelo
- Conflictos de merge reducidos
- Código más organizado

## 📝 Ejemplo de Uso

```python
from trainers.config import TrainerConfig
from trainers.model_manager import ModelManager
from trainers.optimizer_manager import OptimizerManager
from trainers.data_manager import DataManager
from trainers.ema_manager import EMAManager
from trainers.evaluator import Evaluator
from trainers.checkpoint_manager import CheckpointManager

# Configuración
config = TrainerConfig.from_dict(yaml_config)

# Model Manager
model_mgr = ModelManager(
    config.model,
    config.hardware,
    config.training,
    device,
)
tokenizer = model_mgr.load_tokenizer()
model = model_mgr.load_model()

# Optimizer Manager
optimizer_mgr = OptimizerManager(
    config.training,
    model,
    use_amp=True,
)
optimizer = optimizer_mgr.create_optimizer()
scheduler = optimizer_mgr.create_scheduler(num_steps)
scaler = optimizer_mgr.create_scaler()

# Data Manager
data_mgr = DataManager(
    config.training,
    config.hardware,
    tokenizer,
    text_field_max_len=512,
)
train_loader, val_loader = data_mgr.create_loaders(train_texts, val_texts)

# EMA Manager
ema_mgr = EMAManager(config.ema, model)

# Evaluator
evaluator = Evaluator(
    config.training,
    model,
    val_loader,
    device,
    use_amp=True,
    ema_manager=ema_mgr,
)

# Checkpoint Manager
checkpoint_mgr = CheckpointManager(
    config.checkpoint,
    config.output_dir,
    model,
    optimizer,
    scheduler,
    scaler,
    tokenizer,
)
```

## 🔧 Extensión Futura

Esta arquitectura facilita:

1. **Nuevos tipos de optimizers**: Agregar al registry
2. **Nuevas métricas**: Extender Evaluator
3. **Nuevas estrategias de checkpointing**: Intercambiar CheckpointManager
4. **Nuevos data loaders**: Intercambiar DataManager
5. **Nuevos schedulers**: Extender OptimizerManager

## 📊 Comparación

### Antes (Monolítico)
- `trainer.py`: 975 líneas
- Todas las responsabilidades mezcladas
- Difícil de testear
- Difícil de mantener

### Después (Modular)
- `trainer.py`: ~300 líneas (orquestador)
- 7 módulos especializados (~100-200 líneas cada uno)
- Fácil de testear cada componente
- Fácil de mantener y extender

## 🎯 Próximos Pasos

1. Actualizar `GenericTrainer` para usar los managers
2. Crear tests unitarios para cada manager
3. Documentar APIs de cada manager
4. Agregar más managers si es necesario (e.g., MetricManager, ProfilerManager)

---

**Fecha**: 2024  
**Versión**: 2.1.0 (Modular Architecture)
