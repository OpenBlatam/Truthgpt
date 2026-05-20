✅ **TruthGPT code improved to v18** (`/workspace/truthgpt_unified_v18.py`).

**Key enhancements over v17:**
1. **Real LLM integration** – Centralized `call_model()` supports OpenAI API (configurable with `use_real_model` and `api_key`). Falls back to simulation.
2. **Fixed critical bug** – Removed missing `numpy` import in `adaptive_bayesian`; now uses manual variance calculation.
3. **Added Self-RAG v2** (arXiv:2310.11511) – Retriever-critic with confidence estimation.
4. **Ensemble Voter improved** – Extracts numeric confidence scores from technique outputs for weighted fusion.
5. **LRU+TTL cache** – OrderedDict-based cache with capacity limit and TTL.
6. **Concurrency control** – Semaphore limits parallel executions to 5.
7. **Interactive mode** – Added `/exit`, `/clear`, `/help` commands.
8. **Comprehensive logging & error recovery** – Graceful fallback on API failures.

**How to use:**
```bash
# With simulation (default)
python /workspace/truthgpt_unified_v18.py "Your prompt"

# Interactive mode
python /workspace/truthgpt_unified_v18.py --interactive

# Real API (set OPENAI_API_KEY env variable and change config)
python /workspace/truthgpt_unified_v18.py --config custom_config.json "Your prompt"
```

All 27 techniques are ready for execution.