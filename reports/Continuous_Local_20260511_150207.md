I have improved TruthGPT to version 14 (v14). The new code is at `/workspace/truthgpt_unified_v14.py`. Enhancements include: real simulated implementations for all 23 techniques (DoLA, CAI, ORPO, etc.), deterministic caching with TTL (5 min), logging, error handling, memory manager, and interactive mode. To run:
```bash
python /workspace/truthgpt_unified_v14.py "Your prompt" --techniques dola probdist adaptive_bayesian
```
Interactive mode:
```bash
python /workspace/truthgpt_unified_v14.py --interactive
```
Documentation is in `/workspace/README.md`.