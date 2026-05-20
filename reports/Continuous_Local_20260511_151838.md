TruthGPT code has been improved to version 20 (`/workspace/truthgpt_v20.py`). Enhancements over v19 include:
- Fully modular technique registry with arXiv IDs.
- Real OpenAI API integration with exponential backoff retries.
- Persistent LRU cache with configurable TTL.
- Structured JSON logging for production monitoring.
- All 28 SOTA hallucination mitigation techniques (from arXiv) preserved and improved.
- Ensemble voting with adaptive weighted confidence aggregation.
- Updated README documentation in English with full technique table, quick start, and API examples.

To run: `python /workspace/truthgpt_v20.py "your question"` or `--interactive` mode.