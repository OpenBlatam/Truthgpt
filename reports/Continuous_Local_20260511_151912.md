✅ **TruthGPT has been improved to v19** (file: `/workspace/truthgpt_unified_v19.py`).

**Enhancements over v18:**
- Added 2 new techniques: Contrastive Hallucination Detection (arXiv:2501.09245) and Dynamic Contrastive Decoding (arXiv:2402.06705), totaling 28 SOTA methods.
- Fixed `call_model` with real OpenAI API integration and automatic fallback to simulation.
- Improved `EnsembleVoter` with adaptive weighting based on technique confidence.
- Added automatic detection of API key (`use_real_model` auto-set).
- Enhanced async execution with semaphore and timeout.
- Added comprehensive unit tests.

**Documentation (README.md) rewritten in English** with:
- Complete table of all 28 techniques with arXiv links.
- Quick start, configuration, programmatic API examples.
- Architecture description and error handling details.

You can run: `python /workspace/truthgpt_unified_v19.py "your question"` or `--interactive` mode.