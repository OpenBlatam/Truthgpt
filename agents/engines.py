"""
System 5.9 Platinum — LLM Engine Provider Registry (Facade).
Refactored for modularity. This file now acts as an exporter for the sub-modules
to maintain backwards compatibility across the application.
"""

import json
import time
import traceback
from typing import Optional
from loguru import logger

from .ssl_context import ssl_error_hint

# --- Exporters ---
from .engine_config import _resolve_api_key, _load_api_keys_from_prefs, _get_user_prefs, _normalize_engine_key
from .engine_providers import (
    BaseProvider, 
    DeepSeekProvider, 
    GoogleGeminiProvider, 
    OpenAIProvider, 
    AnthropicProvider, 
    OpenRouterProvider, 
    AsyncLLMEngine, 
    DummyAsyncLLM
)
from .engine_registry import EngineRegistry, engine_registry
from .engine_benchmark import (
    _benchmark_run_stats, 
    _record_benchmark_run, 
    _compute_benchmark_metrics, 
    _render_engine_benchmark_block, 
    _display_truthgpt_benchmark
)

try:
    from interface.cc_style import CC_AVAILABLE, cc_spinner, cc_result, _fmt_elapsed, _fmt_tokens
except ImportError:
    CC_AVAILABLE = False

async def safe_llm_call(engine: AsyncLLMEngine, prompt: str, trace_id: Optional[str] = None, **kwargs) -> str:
    """High-fidelity wrapper for LLM calls with TUI integration and per-call tracing."""
    if engine is None:
        logger.warning("safe_llm_call received None engine. Resolving from registry...")
        engine = engine_registry.get_engine()

    t0 = time.time()
    label = "LLM_INFERENCE"

    # Try to extract model name and provider key from engine callable
    model_name = getattr(engine, "model_name", None)
    engine_key = getattr(engine, "provider_name", None)
    if not model_name:
        model_name = getattr(engine, "model", None)
    if not model_name:
        self_obj = getattr(engine, "__self__", None)
        if self_obj:
            model_name = getattr(self_obj, "model", None) or getattr(self_obj, "model_name", None)
    is_ensemble = getattr(engine, "is_ensemble", False)

    # --- Open a tracing span for this LLM call so traces_history.json shows
    # individual llm_inference children again (recent traces had only the root).
    llm_span = None
    if trace_id:
        try:
            from agents.observability import global_tracer
            llm_span = global_tracer.start_span(
                trace_id=trace_id,
                name="llm_inference",
                kind="llm_call",
                input_data=prompt,
                metadata={
                    "model": model_name or "",
                    "engine": engine_key or "",
                    "ensemble": is_ensemble,
                    "prompt_chars": len(prompt),
                },
            )
        except Exception:
            llm_span = None  # tracing must never break inference

    def _finish_span(output: str, status: str, elapsed: float, tokens: int) -> None:
        if llm_span is None:
            return
        try:
            llm_span.finish(
                output=output,
                status=status,
                metadata={
                    "elapsed_ms": round(elapsed * 1000, 2),
                    "approx_tokens": tokens,
                },
            )
        except Exception:
            pass

    async def _run_and_record() -> str:
        nonlocal model_name, engine_key
        try:
            result = await engine(prompt, **kwargs)
            elapsed = time.time() - t0
            tokens = max(1, len(str(result)) // 4)
            if engine_key and not is_ensemble:
                _record_benchmark_run(engine_key, model_name or "", elapsed, tokens)
            _finish_span(str(result), "ok", elapsed, tokens)
            return result
        except Exception as primary_error:
            logger.warning(f"Primary engine '{engine_key or 'unknown'}' failed: {primary_error}. Attempting fallback cascade...")
            # Fetch fallback engines
            fallback_engines = []
            exclude_providers = set()
            if engine_key:
                exclude_providers.update([k.strip() for k in engine_key.split(",")])
            for name in ["deepseek", "claude", "openai", "google", "openrouter"]:
                try:
                    provider, resolved = engine_registry._resolve_provider(name)
                    if provider and provider.api_key and resolved not in exclude_providers:
                        callable_engine = engine_registry._get_single_engine_callable(resolved)
                        if callable_engine:
                            fallback_engines.append((resolved, provider.model, callable_engine))
                except Exception:
                    pass
            
            for fb_key, fb_model, fb_engine in fallback_engines:
                try:
                    logger.info(f"Fallback cascade: attempting {fb_key} ({fb_model})...")
                    result = await fb_engine(prompt, **kwargs)
                    elapsed = time.time() - t0
                    tokens = max(1, len(str(result)) // 4)
                    _record_benchmark_run(fb_key, fb_model, elapsed, tokens)
                    _finish_span(str(result), "ok", elapsed, tokens)
                    # Modify model_name and engine_key dynamically so metrics show the fallback
                    model_name = fb_model
                    engine_key = fb_key
                    return result
                except Exception as fb_error:
                    logger.warning(f"Fallback engine '{fb_key}' failed: {fb_error}")
            
            # If all fallbacks fail, try DummyAsyncLLM
            logger.error("All fallback engines failed. Executing DummyAsyncLLM fallback.")
            dummy = DummyAsyncLLM()
            result = await dummy(prompt, **kwargs)
            elapsed = time.time() - t0
            model_name = dummy.model_name
            engine_key = dummy.provider_name
            _finish_span(str(result), "dummy_fallback", elapsed, len(str(result)) // 4)
            return result

    if CC_AVAILABLE:
        from interface import cc_style
        with cc_spinner(label) as sp:
            try:
                result = await _run_and_record()
                elapsed = time.time() - t0
                tokens = len(str(result)) // 4
                if not getattr(cc_style, "SUPPRESS_SPINNERS", False):
                    sp.add_tokens(tokens)
                    note = f"{_fmt_elapsed(elapsed)} · ~{_fmt_tokens(tokens)} tkn"
                    if is_ensemble:
                        mode = getattr(engine, "ensemble_mode", "ensemble")
                        note += f" · {mode}"
                    cc_result(label, note=note)
                    await _display_truthgpt_benchmark(
                        elapsed,
                        model_name,
                        tokens,
                        engine_key=None if is_ensemble else engine_key,
                    )
                if getattr(cc_style, "REASONING_CALLBACK", None):
                    cc_style.REASONING_CALLBACK(f"LLM_INFERENCE completed in {_fmt_elapsed(elapsed)} (~{_fmt_tokens(tokens)} tkn)")
                return result
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Inference crash [{type(e).__name__}]: {e}\n{tb}")
                hint = ssl_error_hint(e)
                extra = f" {hint}" if hint else " Check API key validity and network connectivity."
                _finish_span(f"{type(e).__name__}: {str(e)[:200]}", "error", time.time() - t0, 0)
                return json.dumps({
                    "thought": f"LLM inference failed: [{type(e).__name__}] {str(e)[:300]}",
                    "final_answer": f"Inference error: {type(e).__name__}: {str(e)[:200]}.{extra}"
                })
    else:
        try:
            return await _run_and_record()
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Inference crash [{type(e).__name__}]: {e}\n{tb}")
            hint = ssl_error_hint(e)
            extra = f" {hint}" if hint else " Check API key validity and network connectivity."
            _finish_span(f"{type(e).__name__}: {str(e)[:200]}", "error", time.time() - t0, 0)
            return json.dumps({
                "thought": f"LLM inference failed: [{type(e).__name__}] {str(e)[:300]}",
                "final_answer": f"Inference error: {type(e).__name__}: {str(e)[:200]}.{extra}"
            })
