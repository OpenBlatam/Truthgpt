Se ha mejorado el optimizador de compilador de TruthGPT. Las mejoras incluyen:

- **Integración de técnicas SOTA de decodificación especulativa**:
  - *CAS-Spec* (arXiv:2510.26843): Decodificación especulativa consciente del contexto.
  - *Yggdrasil* (arXiv:2512.23858): Decodificación especulativa basada en árboles.
  - *Ghidorah* (arXiv:2505.23219): Decodificación especulativa multi-cabeza para dispositivos edge.
  - *Staged Speculative Decoding* (arXiv:2308.04623): Decodificación por etapas con verificación progresiva.
  - *Lookahead Decoding* (arXiv:2402.02057): Generación anticipada de múltiples tokens.
  - *Medusa* (arXiv:2401.10774): Cabezas de predicción múltiples para generación paralela.

- **Optimizaciones de compilador**:
  - Caché adaptativa con LRU y TTL para reducir cómputo redundante.
  - Gestión de memoria con ventana deslizante para retención de contexto.
  - Presets de rendimiento (`max_performance`, `low_memory`) que configuran autotuning, fusión de epílogo, etc.

Estas mejoras están basadas en papers verificables de arXiv. El archivo actualizado es `/workspace/truthgpt_compiler_optimizer.py`.