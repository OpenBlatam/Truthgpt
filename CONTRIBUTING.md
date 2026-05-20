# 🤝 Guía de Contribución - TruthGPT Optimization Core

## 🚀 Cómo Contribuir

### 1. Agregar un Nuevo Componente

#### Ejemplo: Agregar nuevo backend de atención

```python
# En factories/attention.py
from factories.registry import ATTENTION_BACKENDS

@ATTENTION_BACKENDS.register("mi_atencion")
def build_mi_atencion():
    def mi_attention_fn(q, k, v, attn_mask=None, is_causal=True):
        # Tu implementación aquí
        return torch.nn.functional.scaled_dot_product_attention(
            q, k, v, attn_mask=attn_mask, is_causal=is_causal
        )
    return mi_attention_fn
```

Luego en YAML:
```yaml
model:
  attention:
    backend: mi_atencion
```

#### Ejemplo: Agregar nuevo callback

```python
# En factories/callbacks.py
from factories.callbacks import CALLBACKS
from trainers.callbacks import Callback

class MiCallback(Callback):
    def on_log(self, state):
        # Tu lógica aquí
        pass

@CALLBACKS.register("mi_callback")
def build_mi_callback(**kwargs):
    return MiCallback(**kwargs)
```

### 2. Mejorar Performance

- Agregar kernels Triton optimizados en `optimizers/triton_optimizations.py`
- Implementar flash-attn nativo si está disponible
- Optimizar collate functions para tu caso de uso

### 3. Agregar Tests

```python
# En tests/test_basic.py o crear tests/test_new_feature.py
def test_mi_componente():
    from factories.mi_modulo import MI_REGISTRY
    assert "mi_item" in MI_REGISTRY._items
    # Más tests...
```

### 4. Documentar Cambios

- Actualiza `README.md` si agregas features principales
- Agrega ejemplos en `examples/` si es un caso de uso común
- Actualiza `QUICK_REFERENCE.md` si cambias comandos/config

## 📝 Estilo de Código

- **PEP 8**: Sigue las convenciones de Python
- **Type hints**: Usa type hints cuando sea posible
- **Docstrings**: Documenta funciones y clases principales
- **Nombres descriptivos**: Variables y funciones con nombres claros

Ejemplo:
```python
def build_trainer(
    cfg: TrainerConfig,
    raw_cfg: Dict[str, Any],
    train_texts: List[str],
    val_texts: List[str],
    max_seq_len: int
) -> GenericTrainer:
    """
    Build a trainer from configuration.
    
    Args:
        cfg: Trainer configuration dataclass
        raw_cfg: Raw YAML configuration dict
        train_texts: Training texts
        val_texts: Validation texts
        max_seq_len: Maximum sequence length
        
    Returns:
        Configured GenericTrainer instance
    """
    # Implementation...
```

## 🧪 Testing

Antes de hacer PR:

1. **Ejecuta tests existentes:**
   ```bash
   pytest tests/test_basic.py -v
   ```

2. **Valida tu configuración:**
   ```bash
   python validate_config.py configs/llm_default.yaml
   ```

3. **Prueba imports:**
   ```bash
   python -c "from trainers.trainer import GenericTrainer; print('OK')"
   ```

## 🔄 Proceso de PR

1. Fork el repositorio
2. Crea branch: `git checkout -b feature/mi-feature`
3. Commit: `git commit -m 'Add: mi feature description'`
4. Push: `git push origin feature/mi-feature`
5. Abre Pull Request con descripción clara

## ✅ Checklist para PRs

- [ ] Código sigue PEP 8
- [ ] Tests agregados/actualizados
- [ ] Documentación actualizada
- [ ] Config YAML validado
- [ ] No rompe compatibilidad existente
- [ ] Ejemplos funcionando si aplica

## 🐛 Reportar Bugs

Abre un issue con:
- Descripción clara del problema
- Pasos para reproducir
- Config YAML usado (si aplica)
- Logs/errores relevantes
- Versiones de Python/PyTorch/CUDA

## 💡 Sugerencias

Para sugerencias de features:
- Abre un issue con label "enhancement"
- Describe el caso de uso
- Menciona beneficios esperados

## 📚 Recursos

- Ver `ARCHITECTURE.md` para entender el diseño
- Ver `README.md` para uso y ejemplos
- Ver `QUICK_REFERENCE.md` para comandos rápidos

---

¡Gracias por contribuir! 🎉


