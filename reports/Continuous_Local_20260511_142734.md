He mejorado el código de TruthGPT (`/workspace/truthgpt_unified.py`) añadiendo:
- Logging configurables para un mejor seguimiento.
- Configuración por defecto y por técnica.
- Resolución dinámica de puntos de entrada (`run` o `detect`).
- Función `list_available_techniques()` para listar módulos cargados correctamente.
- Mejora en el manejo de errores y tiempos de ejecución.
- Ahora el script acepta un prompt como argumento opcional.

El código está listo para ejecutarse con `python truthgpt_unified.py "tu prompt"`.