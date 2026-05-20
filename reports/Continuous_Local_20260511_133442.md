He mejorado TruthGPT creando un orquestador unificado en `/workspace/truthgpt_unified.py` que integra las 34+ técnicas SOTA para detección y mitigación de alucinaciones. Este script proporciona una interfaz simple para ejecutar cualquier técnica con manejo de errores, tiempos de ejecución y reportes detallados. También incluye un modo de benchmark para medir rendimiento. Las técnicas se cargan dinámicamente desde los módulos existentes. Para usarlo:

```python
from truthgpt_unified import TruthGPTUnified
tgpt = TruthGPTUnified()
results = tgpt.run_all('¿Capital de Francia?', techniques=['DoLA','AdaptiveBayesian','TUM_MiKaNi'])
```

Ahora puedes añadir nuevas técnicas simplemente registrándolas en el diccionario `TECHNIQUE_MODULES`.