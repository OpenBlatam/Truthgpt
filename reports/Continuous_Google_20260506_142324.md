The RuntimeWarning indicates that the `duckduckgo_search` package has been renamed to `ddgs`. To suppress this warning, please:
1. Run `pip install ddgs`
2. In `tools.py` line 140 (and any other occurrence), change `from duckduckgo_search import DDGS` to `from ddgs import DDGS`
3. Optionally uninstall the old package with `pip uninstall duckduckgo_search`

The rest of the log shows normal HTTP responses (200 OK) and successful model inference calls (DeepSeek, GPT-4o). No other issues detected. If you need further assistance (e.g., running a system optimization or health check), let me know.