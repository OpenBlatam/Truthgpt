# TruthGPT - Guía de Inicio Rápido

¡Bienvenido a TruthGPT! Esta guía te ayudará a empezar rápidamente con el framework de optimización más avanzado para modelos de lenguaje.

## 🚀 Inicio en 5 Minutos

### Paso 1: Instalación Rápida

```bash
# Instalar dependencias
pip install torch transformers accelerate
pip install -r requirements_modern.txt

# Verificar instalación
python -c "from optimization_core import *; print('TruthGPT instalado correctamente')"
```

### Paso 2: Primer Uso

```python
from optimization_core import ModernTruthGPTOptimizer, TruthGPTConfig

# Configuración básica
config = TruthGPTConfig(
    model_name="microsoft/DialoGPT-medium",
    use_mixed_precision=True
)

# Crear optimizador
optimizer = ModernTruthGPTOptimizer(config)

# Generar texto
text = optimizer.generate(
    input_text="Hola, ¿cómo estás?",
    max_length=100,
    temperature=0.7
)

print(f"Generated: {text}")
```

### Paso 3: Optimización Básica

```python
from optimization_core import create_memory_optimizer

# Optimizar memoria
memory_config = {
    "use_gradient_checkpointing": True,
    "use_activation_checkpointing": True
}

memory_optimizer = create_memory_optimizer(memory_config)
optimized_optimizer = memory_optimizer.optimize(optimizer)

# Usar optimizador optimizado
text = optimized_optimizer.generate(
    input_text="Explica la inteligencia artificial",
    max_length=200,
    temperature=0.7
)

print(f"Optimized generation: {text}")
```

## 📚 Documentación Completa

### 🎯 Guías Principales
- **[Guía de Uso](guides/truthgpt_usage_guide.md)** - Cómo usar TruthGPT
- **[Creación de Modelos](guides/model_creation_guide.md)** - Crear modelos personalizados
- **[Adaptación de Modelos](guides/truthgpt_adaptation_guide.md)** - Adaptar modelos existentes
- **[Optimización Avanzada](guides/advanced_optimization_guide.md)** - Técnicas avanzadas

### 🎓 Tutoriales
- **[Tutorial Básico](tutorials/basic_tutorial.md)** - Primeros pasos
- **[Tutorial Avanzado](tutorials/advanced_tutorial.md)** - Casos avanzados y optimización

### 💡 Ejemplos
- **[Ejemplos Básicos](examples/basic_examples.md)** - Casos de uso simples
- **[Ejemplos Avanzados](examples/advanced_examples.md)** - Casos de uso complejos
- **[Ejemplos de Rendimiento](examples/performance_examples.md)** - Optimización de rendimiento
- **[Ejemplos de Integración](examples/integration_examples.md)** - Integración con sistemas
- **[Ejemplos del Mundo Real](examples/real_world_examples.md)** - Casos de uso reales
- **[Ejemplos Empresariales](examples/enterprise_examples.md)** - Implementación empresarial
- **[Ejemplos de Benchmarks](examples/benchmark_examples.md)** - Pruebas comparativas

## 🎯 Casos de Uso Comunes

### 1. Chat Bot Simple

```python
class SimpleChatBot:
    def __init__(self):
        config = TruthGPTConfig(
            model_name="microsoft/DialoGPT-medium",
            use_mixed_precision=True
        )
        self.optimizer = ModernTruthGPTOptimizer(config)
    
    def chat(self, message):
        response = self.optimizer.generate(
            input_text=message,
            max_length=150,
            temperature=0.7
        )
        return response

# Usar chatbot
bot = SimpleChatBot()
response = bot.chat("Hola, ¿cómo estás?")
print(f"Bot: {response}")
```

### 2. Generador de Código

```python
class CodeGenerator:
    def __init__(self):
        config = TruthGPTConfig(
            model_name="microsoft/DialoGPT-medium",
            use_mixed_precision=True
        )
        self.optimizer = ModernTruthGPTOptimizer(config)
    
    def generate_function(self, description):
        prompt = f"Escribe una función Python que: {description}"
        code = self.optimizer.generate(
            input_text=prompt,
            max_length=300,
            temperature=0.3
        )
        return code

# Usar generador de código
generator = CodeGenerator()
code = generator.generate_function("calcule el factorial de un número")
print(f"Código generado: {code}")
```

### 3. Asistente de Escritura

```python
class WritingAssistant:
    def __init__(self):
        config = TruthGPTConfig(
            model_name="microsoft/DialoGPT-medium",
            use_mixed_precision=True
        )
        self.optimizer = ModernTruthGPTOptimizer(config)
    
    def improve_text(self, text):
        prompt = f"Mejora este texto: {text}"
        improved = self.optimizer.generate(
            input_text=prompt,
            max_length=400,
            temperature=0.5
        )
        return improved

# Usar asistente de escritura
assistant = WritingAssistant()
improved_text = assistant.improve_text("Este es un texto de ejemplo")
print(f"Texto mejorado: {improved_text}")
```

## ⚡ Optimizaciones Rápidas

### 1. Optimización de Memoria

```python
from optimization_core import create_memory_optimizer

# Configuración de memoria
memory_config = {
    "use_gradient_checkpointing": True,
    "use_activation_checkpointing": True,
    "use_memory_efficient_attention": True
}

# Aplicar optimización
memory_optimizer = create_memory_optimizer(memory_config)
optimized_optimizer = memory_optimizer.optimize(optimizer)
```

### 2. Optimización de Velocidad

```python
from optimization_core import create_ultra_fast_optimizer

# Configuración de velocidad
speed_config = {
    "use_parallel_processing": True,
    "use_batch_optimization": True,
    "use_kernel_fusion": True
}

# Aplicar optimización
speed_optimizer = create_ultra_fast_optimizer(speed_config)
fast_optimizer = speed_optimizer.optimize(optimizer)
```

### 3. Optimización de GPU

```python
from optimization_core import create_gpu_accelerator

# Configuración GPU
gpu_config = {
    "cuda_device": 0,
    "use_mixed_precision": True,
    "use_tensor_cores": True
}

# Aplicar optimización
gpu_accelerator = create_gpu_accelerator(gpu_config)
gpu_optimizer = gpu_accelerator.optimize(optimizer)
```

## 🔧 Configuración Avanzada

### 1. Configuración Personalizada

```python
# Configuración avanzada
config = TruthGPTConfig(
    model_name="microsoft/DialoGPT-medium",
    use_mixed_precision=True,
    use_gradient_checkpointing=True,
    use_flash_attention=True,
    batch_size=4,
    learning_rate=5e-5,
    num_epochs=3
)

# Crear optimizador
optimizer = ModernTruthGPTOptimizer(config)
```

### 2. Entrenamiento Personalizado

```python
from optimization_core import create_training_pipeline

# Crear pipeline de entrenamiento
pipeline = create_training_pipeline(
    model_name="microsoft/DialoGPT-medium",
    experiment_name="mi_experimento",
    use_wandb=True
)

# Entrenar
results = pipeline.train(train_loader, val_loader)
```

### 3. Optimización Completa

```python
from optimization_core import create_ultra_optimization_core

# Configuración ultra
ultra_config = {
    "use_quantization": True,
    "use_kernel_fusion": True,
    "use_memory_pooling": True,
    "use_adaptive_precision": True
}

# Aplicar optimización ultra
ultra_optimizer = create_ultra_optimization_core(ultra_config)
ultra_optimized = ultra_optimizer.optimize(optimizer)
```

## 📊 Monitoreo y Debugging

### 1. Verificar Rendimiento

```python
import time

# Medir tiempo de generación
start_time = time.time()
text = optimizer.generate("Hola, ¿cómo estás?", max_length=100)
end_time = time.time()

print(f"Tiempo de generación: {end_time - start_time:.2f} segundos")
print(f"Texto generado: {text}")
```

### 2. Verificar Memoria

```python
import psutil

# Verificar uso de memoria
memory_before = psutil.Process().memory_info().rss
text = optimizer.generate("Hola, ¿cómo estás?", max_length=100)
memory_after = psutil.Process().memory_info().rss

print(f"Memoria usada: {(memory_after - memory_before) / 1024 / 1024:.2f} MB")
```

### 3. Verificar GPU

```python
import torch

# Verificar GPU
if torch.cuda.is_available():
    print(f"GPU disponible: {torch.cuda.get_device_name(0)}")
    print(f"Memoria GPU: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    print("GPU no disponible, usando CPU")
```

## 🎯 Próximos Pasos

### Para Principiantes:
1. **Completa** el [Tutorial Básico](tutorials/basic_tutorial.md)
2. **Explora** los [Ejemplos Básicos](examples/basic_examples.md)
3. **Experimenta** con diferentes modelos
4. **Optimiza** según tu hardware

### Para Usuarios Avanzados:
1. **Lee** la [Guía de Optimización Avanzada](guides/advanced_optimization_guide.md)
2. **Explora** los [Ejemplos Avanzados](examples/advanced_examples.md)
3. **Crea** tus propios modelos
4. **Integra** con sistemas existentes

### Para Desarrolladores:
1. **Estudia** la [Guía de Creación de Modelos](guides/model_creation_guide.md)
2. **Aprende** sobre [Adaptación de Modelos](guides/truthgpt_adaptation_guide.md)
3. **Implementa** optimizaciones personalizadas
4. **Contribuye** al proyecto

## 🆘 Soporte y Ayuda

### Documentación:
- **Guías**: Consulta las guías detalladas
- **Tutoriales**: Sigue los tutoriales paso a paso
- **Ejemplos**: Explora los ejemplos de código

### Comunidad:
- **Issues**: Reporta problemas en el repositorio
- **Discusiones**: Únete a las discusiones de la comunidad
- **Contribuciones**: Contribuye al desarrollo

### Recursos Adicionales:
- **Blog**: Artículos y tutoriales
- **Videos**: Tutoriales en video
- **Workshops**: Talleres y cursos

## 🎉 ¡Felicidades!

Has completado la guía de inicio rápido de TruthGPT. Ahora tienes:

- ✅ Entorno configurado
- ✅ Primer uso funcionando
- ✅ Optimizaciones básicas
- ✅ Casos de uso comunes
- ✅ Configuración avanzada

### ¿Qué sigue?

1. **Explora** la documentación completa
2. **Experimenta** con diferentes configuraciones
3. **Crea** tus propios casos de uso
4. **Optimiza** según tus necesidades
5. **Comparte** tus resultados con la comunidad

---

*¡Bienvenido al mundo de TruthGPT! ¡Disfruta creando modelos de IA optimizados!*


