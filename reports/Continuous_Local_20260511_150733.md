TruthGPT has been improved to version 17 (v17) with the following enhancements:

1. **Integrated 2 new SOTA techniques**:
   - HIDE and Seek (arXiv:2506.17748): Decoupled representation hallucination detection.
   - AggTruth (arXiv:2506.18628): Contextual hallucination detection using aggregated attention scores.

2. **Added confidence-weighted ensemble voter** that combines outputs from all 25 techniques to produce a final fact-checked answer with confidence scores.

3. **Enhanced documentation** in `/workspace/README.md` updated to v15 with full technique table and usage examples.

4. **Production-ready code** at `/workspace/truthgpt_unified_v17.py` with:
   - Asynchronous parallel execution
   - Deterministic TTL caching
   - Sliding window memory manager
   - CLI and interactive modes

To run: `python /workspace/truthgpt_unified_v17.py "Your prompt" --techniques dola probdist aggtruth`
For interactive: `python /workspace/truthgpt_unified_v17.py --interactive`