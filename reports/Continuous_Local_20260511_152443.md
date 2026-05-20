TruthGPT has been significantly improved to version 20 (`/workspace/truthgpt_v20.py`). The new code includes:

1. **30 state‑of‑the‑art hallucination mitigation techniques** (all from arXiv papers including Dynamic Contrastive Decoding, Small LM Detection, First Hallucination Token, etc.).
2. **Real OpenAI API integration** with exponential backoff and retries, plus simulation fallback.
3. **Persistent LRU + TTL cache** backed by a JSON file to avoid recomputation.
4. **Adaptive ensemble voting** that weights each technique based on historical accuracy (decaying history).
5. **Plugin system** to load external techniques from `/workspace/plugins/`.
6. **Memory manager** with sliding window for context.
7. **Command‑line and interactive modes**.
8. **Comprehensive error handling** per technique.

### How to use:
```bash
python /workspace/truthgpt_v20.py "What is the capital of France?"
python /workspace/truthgpt_v20.py --interactive
python /workspace/truthgpt_v20.py --config config.json --techniques dola self_rag "Query"
```

The updated code is now at `/workspace/truthgpt_v20.py`. If you need further enhancements (e.g., adding more techniques, web verification, semantic cache), let me know.