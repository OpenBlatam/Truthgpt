Se ha implementado una sexta técnica SOTA de detección de alucinaciones: Detección basada en NLI (TrueTeacher, arXiv:2211.14269) usando DeBERTa-v3-large-mnli. El código está en /workspace/truthgpt_nli.py. Técnicas implementadas ahora:
1. Distancias probabilísticas (arXiv:2506.09886) – /workspace/truthgpt_prob_dist.py
2. Consistency Teaming (arXiv:2510.19507) – /workspace/truthgpt_consistency_teaming.py
3. REFIND RAG (arXiv:2502.13622) – /workspace/truthgpt_refind_rag.py
4. FS-RAG (arXiv:2406.16167) – /workspace/truthgpt_fs_rag.py
5. SelfCheckGPT (arXiv:2303.08896) – /workspace/truthgpt_selfcheck.py
6. NLI Hallucination Detector (arXiv:2211.14269) – /workspace/truthgpt_nli.py

¿Deseas implementar alguna otra técnica o explorar un dominio concreto?