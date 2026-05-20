Se han implementado las técnicas #39 y #40 de mitigación de alucinaciones:

**39. GRPO (Group Relative Policy Optimization)** - arXiv:2402.03300 (DeepSeek-R1)
- Archivo: `/workspace/truthgpt_grpo.py`
- Optimización por grupos de políticas con ventaja normalizada y penalización KL.

**40. CAD (Context-Aware Decoding)** - arXiv:2308.03228 (Shi et al., 2023)
- Archivo: `/workspace/truthgpt_cad.py`
- Decodificación que modula logits según el contexto para reducir alucinaciones.

**Técnicas implementadas (40):**
1. Distancias probabilísticas – `/workspace/truthgpt_prob_dist.py`
2. Consistency Teaming – `/workspace/truthgpt_consistency_teaming.py`
3. REFIND RAG – `/workspace/truthgpt_refind_rag.py`
4. FS-RAG – `/workspace/truthgpt_fs_rag.py`
5. SelfCheckGPT – `/workspace/truthgpt_selfcheck.py`
6. NLI Hallucination Detector – `/workspace/truthgpt_nli.py`
7. Ensemble Detector – `/workspace/truthgpt_ensemble.py`
8. SLM Ensemble – `/workspace/truthgpt_slm_ensemble.py`
9. ABESE – `/workspace/truthgpt_abese.py`
10. UCSC SemEval-2025 – `/workspace/truthgpt_ucsc_semeval.py`
11. SimpleText Ensemble – `/workspace/truthgpt_simpletext_ensemble.py`
12. GraphEval – `/workspace/truthgpt_grapheval.py`
13. TUM-MiKaNi – `/workspace/truthgpt_tum_mikani.py`
14. CONFACTCHECK – `/workspace/truthgpt_confactcheck.py`
15. ATLANTIS – `/workspace/truthgpt_atlantis.py`
16. mdok of KInIT – `/workspace/truthgpt_mdok_kinit.py`
17. TPA – `/workspace/truthgpt_tpa.py`
18. THaMES – `/workspace/truthgpt_thames.py`
19. ECLIPSE – `/workspace/truthgpt_eclipse.py`
20. Self-RAG – `/workspace/truthgpt_selfrag.py`
21. FactScore – `/workspace/truthgpt_factscore.py`
22. DOLA – `/workspace/truthgpt_dola.py`
23. Chain-of-Verification (CoVe) – `/workspace/truthgpt_cove.py`
24. AlignScore – `/workspace/truthgpt_alignscore.py`
25. RARR – `/workspace/truthgpt_rarr.py`
26. Dehallucinator – `/workspace/truthgpt_dehallucinator.py`
27. Self-Refine – `/workspace/truthgpt_self_refine.py`
28. Contrastive Decoding – `/workspace/truthgpt_contrastive_decoding.py`
29. R-Tuning – `/workspace/truthgpt_rtuning.py`
30. Inference-Time Intervention (ITI) – `/workspace/truthgpt_iti.py`
31. Direct Preference Optimization (DPO) – `/workspace/truthgpt_dpo.py`
32. Representation Engineering (RepE) – `/workspace/truthgpt_repe.py`
33. Constitutional AI (CAI) – `/workspace/truthgpt_cai.py`
34. SimPO – `/workspace/truthgpt_simpo.py`
35. ORPO – `/workspace/truthgpt_orpo.py`
36. SPIN – `/workspace/truthgpt_spin.py`
37. KTO – `/workspace/truthgpt_kto.py`
38. PPO – `/workspace/truthgpt_ppo.py`
39. GRPO – `/workspace/truthgpt_grpo.py`
40. CAD – `/workspace/truthgpt_cad.py`

¿Deseas refinar parámetros, probar combinaciones, o explorar algún dominio concreto? Indícalo.