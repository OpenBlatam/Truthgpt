TruthGPT has been improved to v7 (saved at `/workspace/truthgpt_unified_v7.py`). New features and improvements over v6 include:

1. **Self-RAG (arXiv:2310.11511)**: Enriches the prompt with retrieved context when `use_rag=True` and a `rag_source` is provided.
2. **Chain-of-Verification (arXiv:2309.11495)**: Iteratively refines the output using a verifier function to correct logical inconsistencies.
3. **Semantic Entropy (arXiv:2306.04786)**: Measures uncertainty by clustering generations; if entropy exceeds a threshold, appends a note.
4. **DPO-inspired Reranking (arXiv:2305.18290)**: When multiple candidates exist, reranks them using a preference model and selects the best.
5. **Self-Consistency (arXiv:2203.11171)**: Generates multiple responses and returns the most consistent one via sequence matching.
6. **Small LM Hallucination Detection (arXiv:2506.22486)**: Detects contradictory phrases in the output.
7. **Probabilistic Distance Detection (arXiv:2506.09886)**: Uses bigram probabilities with Laplace smoothing to compute hallucination risk – now more robust.
8. **REFIND RAG verification (arXiv:2502.13622)**: Checks for numeric plausibility and flags extreme numbers without qualifiers.
9. **Pipeline architecture**: All techniques are applied sequentially, and post-processing steps (verification, entropy, detection, reranking) are configurable via JSON config.
10. **Improved CLI**: Supports `--techniques`, `--config`, `--interactive` modes, and proper argument parsing.

To use: `python /workspace/truthgpt_unified_v7.py "your prompt" --techniques dola cai` or `--interactive` for REPL.