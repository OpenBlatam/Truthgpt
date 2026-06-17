# TruthGPT Kernel Architecture

## Overview

El kernel de TruthGPT ha sido refactorizado desde un script monolítico hacia una arquitectura modular basada en servicios, eventos y plugins.

## Estructura

```
core/kernels/
├── __init__.py                  # Exports públicos del kernel
├── truthgpt_kernel.py           # Kernel principal (TruthGPTKernel)
├── KERNEL_ARCHITECTURE.md       # Esta documentación
└── services/
    ├── __init__.py              # Exports de servicios
    ├── base_service.py          # Contrato base (BaseService)
    ├── agent_service.py         # Gestión de agentes y swarm
    ├── model_service.py         # Gestión de modelos e inferencia
    ├── research_service.py      # Papers y base de conocimiento
    ├── optimization_service.py  # Optimización y métricas
    └── inference_service.py     # Motor de inferencia con caché
```

## Componentes Principales

### TruthGPTKernel
Orquestador central que gestiona el ciclo de vida de todos los subsistemas.

**Estados del ciclo de vida:**
```
INITIALIZING → STARTING → RUNNING → STOPPING → STOPPED
                                  ↘ ERROR
```

**Responsabilidades:**
- Inicialización y shutdown ordenado de servicios
- Sistema de eventos pub/sub
- Registro y descubrimiento de servicios
- Gestión de tareas asíncronas
- Carga de plugins

### BaseService
Contrato que todos los servicios deben implementar:

```python
class MyService(BaseService):
    async def _on_start(self) -> None:
        # Lógica de inicio
        pass

    async def _on_stop(self) -> None:
        # Lógica de parada
        pass

    async def _get_health_info(self) -> Dict[str, Any]:
        # Información de salud
        return {"custom_metric": 42}
```

### Servicios del Kernel

| Servicio | Responsabilidad |
|---|---|
| `AgentService` | Gestión de agentes IA y operaciones swarm |
| `ModelService` | Ciclo de vida de modelos y routing de inferencia |
| `ResearchService` | Papers, búsqueda y base de conocimiento |
| `OptimizationService` | Optimizadores y métricas de rendimiento |
| `InferenceService` | Motor de inferencia con batching y caché |

## Uso

### Inicio básico
```python
from core.kernels import get_kernel, KernelConfig

config = KernelConfig(
    log_level="INFO",
    enable_hot_reload=True,
    max_concurrent_tasks=1000,
)
kernel = get_kernel()
await kernel.run()
```

### Registrar un servicio personalizado
```python
from core.kernels import get_kernel
from core.kernels.services.base_service import BaseService

class MyCustomService(BaseService):
    async def _on_start(self): ...
    async def _on_stop(self): ...

kernel = get_kernel()
kernel.register_service("my_service", MyCustomService)
```

### Acceder a un servicio en ejecución
```python
kernel = get_kernel()
inference = kernel.get_service("inference")
result = await inference.infer("Hello, world!", model="deepseek")
```

### Escuchar eventos del kernel
```python
kernel = get_kernel()

@kernel.event_emitter.on("kernel.started")
async def on_started(event):
    print("Kernel started!")
```

## Ventajas sobre la arquitectura anterior

| Aspecto | Antes (monolítico) | Ahora (kernel modular) |
|---|---|---|
| Estructura | Scripts sueltos en raíz | Servicios organizados en `core/kernels/` |
| Inicio | Secuencial y bloqueante | Asíncrono con gestión de tareas |
| Servicios | Acoplados en `main.py` | Desacoplados con ciclo de vida propio |
| Eventos | Callbacks directos | Sistema pub/sub desacoplado |
| Plugins | No soportado | Plugin manager integrado |
| Health checks | Manual | Automático por servicio |
| Shutdown | Abrupto | Graceful con timeout configurable |
| Testing | Difícil (monolito) | Fácil (servicios aislados) |
