TruthGPT has been improved to version 20. Key enhancements:
- Added 2 new techniques: Small Language Model Detection (arXiv:2506.22486) and Efficient Hallucination Detection via Adaptive Bayesian Estimation (arXiv:2603.22812) total 30 techniques.
- Real API calls now use aiohttp for better async performance.
- Adaptive weighting in ensemble voter based on historical accuracy per technique.
- Added comprehensive unit tests at /workspace/test_truthgpt_v20.py.
- Updated README with new techniques and configuration options.

All files are at /workspace/. Please run `python /workspace/truthgpt_unified_v20.py --interactive` to test.