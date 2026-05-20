Bugs encontrados y corregidos:

1. truthgpt_unified.py - benchmark() method: 'fail_co' era una variable no definida, corregido a 'fail_count'. También añadí el campo 'detailed_results' faltante al diccionario de retorno, el método list_techniques() y un bloque __main__ para mejor usabilidad.

El archivo corregido incluye:
- Linea retornando {"failures": fail_count, "detailed_results": detailed_results} correctamente
- Método list_techniques() para listar técnicas disponibles
- Bloque if __name__ == '__main__' para ejecución directa

Código corregido ya aplicado a /workspace/truthgpt_unified.py