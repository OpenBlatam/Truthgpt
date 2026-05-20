El error `'NoneType' object has no attribute 'route_and_process'` ocurre porque `client.swarm` es `None`. En `swarm_menu.py`, línea 514, se llama a `await client.swarm.route_and_process(...)` sin verificar si el swarm existe. La causa es que `AgentConfig` tiene `use_swarm=False` (ver traceback).

**Solución inmediata (en `handle_continuous_mission`):**
```python
if client.swarm is None:
    console.print("[red]Error: El cliente no tiene un swarm inicializado. Asegúrate de que use_swarm=True en la configuración.[/red]")
    return
response = await client.swarm.route_and_process(query, context={...})
```

**Alternativa:** Configurar el cliente con `use_swarm=True`:
```python
config = AgentConfig(
    use_swarm=True,  # <-- Cambiar a True
    ...
)
client = AgentClient(config=config)
```

Además, revisa que el método `route_and_process` exista en la clase `Swarm` (si es propia) y que el swarm se inicialice correctamente en el constructor de `AgentClient`.