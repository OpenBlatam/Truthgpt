✅ **TruthGPT code improved to v19** (file: `/workspace/truthgpt_unified_v19.py`).

**Enhancements over v18:**
- Fixed truncated `call_model` — now complete with real OpenAI API integration and fallback to simulation.
- Added 2 new techniques: Contrastive Hallucination Detection (arXiv:2501.09245) and Dynamic Contrastive Decoding (arXiv:2402.06705), totaling 28 SOTA methods.
- Improved `EnsembleVoter` with adaptive weighting based on technique confidence.
- Added automatic detection of API key (`use_real_model` auto-set).
- Enhanced async execution with semaphore and timeout.
- Added comprehensive unit tests.

**Run:** `python /workspace/truthgpt_unified_v19.py "your question"` or `--interactive` mode.