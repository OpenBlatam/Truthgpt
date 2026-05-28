import inspect
import json
import time
from typing import Dict, List, Optional, Type, Union, Any

from loguru import logger

from .engine_config import _load_api_keys_from_prefs, _normalize_engine_key, _get_user_prefs
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
from .engine_benchmark import _record_benchmark_run
from .ensemble import ALL_ENSEMBLE_MODES, run_ensemble


class EngineRegistry:
    """Refactored Singleton Registry for LLM Providers."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._providers: Dict[str, BaseProvider] = {}
            # Defaults are registered as classes for lazy instantiation
            inst._default_providers = {
                "deepseek": DeepSeekProvider,
                "google": GoogleGeminiProvider,
                "chatgpt": OpenAIProvider,
                "openai": OpenAIProvider,
                "claude": AnthropicProvider,
                "anthropic": AnthropicProvider,
                "openrouter": OpenRouterProvider
            }
            cls._instance = inst
        return cls._instance

    def register(self, name: str, provider: Union[BaseProvider, Type[BaseProvider]]):
        self._providers[name] = provider
        if not inspect.isclass(provider):
            logger.info(f"LLM Provider registered: {name}")

    def _refresh_stale_providers(self):
        """Re-instantiate any cached providers that lack an API key (they may have been created before keys were loaded)."""
        for name, provider in list(self._providers.items()):
            if isinstance(provider, BaseProvider) and not provider.api_key:
                if name in self._default_providers:
                    fresh = self._default_providers[name]()
                    if fresh.api_key:
                        self._providers[name] = fresh
                        logger.info(f"Refreshed stale provider: {name}")

    def list_engines(self) -> List[str]:
        """Returns list of registered and default engine names."""
        names = set(self._default_providers.keys()) | set(self._providers.keys())
        return sorted(list(names))

    def _resolve_provider(self, name: Optional[str]) -> tuple[Optional[BaseProvider], str]:
        """Resolve a provider instance and canonical engine key."""
        _load_api_keys_from_prefs()
        self._refresh_stale_providers()

        fallback_order = ["deepseek", "claude", "anthropic", "openai", "chatgpt", "google", "openrouter"]
        resolved_name = name or ""
        if "," in resolved_name:
            resolved_name = resolved_name.split(",")[0].strip()
        base_provider = resolved_name.split(":")[0] if ":" in resolved_name else resolved_name
        base_provider = _normalize_engine_key(base_provider)

        if not resolved_name or base_provider not in self._default_providers:
            for f_name in fallback_order:
                norm = _normalize_engine_key(f_name)
                if norm in self._default_providers:
                    p_inst = self._default_providers[norm]()
                    if p_inst.api_key:
                        resolved_name = norm
                        break
            if not resolved_name:
                resolved_name = "claude"

        resolved_name = _normalize_engine_key(resolved_name.split(":")[0] if ":" in resolved_name else resolved_name)

        if resolved_name in self._default_providers and resolved_name not in self._providers:
            provider_cls = self._default_providers[resolved_name]
            self.register(resolved_name, provider_cls())

        provider = self._providers.get(resolved_name)
        if not provider and name and ":" in name:
            p_name, _, m_name = name.partition(":")
            p_name = _normalize_engine_key(p_name)
            if p_name == "google":
                self.register(name, GoogleGeminiProvider(model=m_name))
            elif p_name == "deepseek":
                self.register(name, DeepSeekProvider(model=m_name))
            elif p_name in ["chatgpt", "openai"]:
                self.register(name, OpenAIProvider(model=m_name))
            elif p_name in ["claude", "anthropic"]:
                self.register(name, AnthropicProvider(model=m_name))
            elif p_name == "openrouter":
                self.register(name, OpenRouterProvider(model=m_name))
            provider = self._providers.get(name)

        if provider and not provider.api_key:
            for f_name in fallback_order:
                norm = _normalize_engine_key(f_name)
                if norm == resolved_name:
                    continue
                if norm in self._default_providers and norm not in self._providers:
                    self._providers[norm] = self._default_providers[norm]()
                f_provider = self._providers.get(norm)
                if f_provider and f_provider.api_key:
                    logger.warning(
                        f"Preferred engine '{resolved_name}' lacks API key. Falling back to '{norm}'"
                    )
                    provider = f_provider
                    resolved_name = norm
                    break

        if not provider:
            for f_name in fallback_order:
                norm = _normalize_engine_key(f_name)
                if norm in self._default_providers and norm not in self._providers:
                    self._providers[norm] = self._default_providers[norm]()
                f_provider = self._providers.get(norm)
                if f_provider and f_provider.api_key:
                    provider = f_provider
                    resolved_name = norm
                    break

        return provider, resolved_name

    def get_active_engines(self) -> List[Dict[str, str]]:
        """Engines listed in preferred_engine that currently have an API key."""
        prefs = _get_user_prefs()
        preferred_raw = prefs.get("preferred_engine", "deepseek")
        keys = [_normalize_engine_key(x) for x in preferred_raw.split(",") if x.strip()]
        if not keys:
            keys = ["deepseek"]

        active: List[Dict[str, str]] = []
        seen: set[str] = set()
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            provider, resolved = self._resolve_provider(key)
            if provider and provider.api_key:
                active.append({
                    "key": resolved,
                    "label": key,
                    "model": provider.model,
                })
        if not active:
            provider, resolved = self._resolve_provider(None)
            if provider and provider.api_key:
                active.append({
                    "key": resolved,
                    "label": resolved,
                    "model": provider.model,
                })
        return active

    def _get_single_engine_callable(self, name: Optional[str]) -> Optional[AsyncLLMEngine]:
        """Single-provider callable (no ensemble wrapper)."""
        provider, resolved_name = self._resolve_provider(name)
        if not provider:
            return None

        async def _call(prompt: str, **kwargs) -> str:
            return await provider.generate(prompt, **kwargs)

        _call.model_name = provider.model
        _call.provider_name = resolved_name
        _call.is_ensemble = False
        return _call

    def _build_ensemble_engine(
        self, active: List[Dict[str, str]], mode: str
    ) -> AsyncLLMEngine:
        """Run all active engines and merge outputs (consensus, parallel, etc.)."""
        registry = self
        mode = (mode or "consensus").lower().strip()

        async def _run_engine_key(
            key: str, eng: Dict[str, str], prompt: str, **kw
        ) -> tuple:
            sub = registry._get_single_engine_callable(key)
            if not sub:
                return key, eng["model"], "", 0.0, 0
            t0 = time.time()
            try:
                text = await sub(prompt, **kw)
            except Exception as exc:
                logger.error(f"Ensemble engine '{key}' failed: {exc}")
                text = json.dumps({
                    "thought": f"[{key}] inference error",
                    "final_answer": f"Error ({key}): {type(exc).__name__}: {str(exc)[:200]}",
                })
            elapsed = time.time() - t0
            tokens = max(1, len(str(text)) // 4)
            model = getattr(sub, "model_name", None) or eng["model"]
            return key, model, text, elapsed, tokens

        async def _ensemble_call(prompt: str, **kwargs) -> str:
            def _record(key: str, model: str, elapsed: float, tokens: int) -> None:
                _record_benchmark_run(key, model, elapsed, tokens)

            return await run_ensemble(
                mode,
                active,
                prompt,
                _run_engine_key,
                record_run=_record if mode != "race" else _record,
                **kwargs,
            )

        _ensemble_call.is_ensemble = True
        _ensemble_call.ensemble_mode = mode
        _ensemble_call.model_name = " + ".join(e["model"] for e in active)
        _ensemble_call.provider_name = ",".join(e["key"] for e in active)
        return _ensemble_call

    def get_engine(self, name: Optional[str] = None) -> Optional[AsyncLLMEngine]:
        """Returns a callable; uses ensemble when multiple engines are configured."""
        prefs = _get_user_prefs()
        ensemble_mode = str(prefs.get("ensemble_mode", "race")).lower()
        if ensemble_mode not in ALL_ENSEMBLE_MODES:
            ensemble_mode = "consensus"
        active = self.get_active_engines()

        if len(active) > 1:
            logger.info(
                f"Ensemble [{ensemble_mode}]: {[e['key'] for e in active]}"
            )
            return self._build_ensemble_engine(active, ensemble_mode)

        single_name = name
        if single_name and "," in single_name:
            single_name = single_name.split(",")[0].strip()
        elif not single_name and active:
            single_name = active[0]["key"]

        engine = self._get_single_engine_callable(single_name)
        if not engine:
            logger.error(
                "ENGINE RESOLUTION FAILED: No LLM provider has a valid API key. "
                "Configure at least one of: DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, "
                "OPENAI_API_KEY, GOOGLE_API_KEY, OPENROUTER_API_KEY. "
                "Falling back to DummyAsyncLLM."
            )
            return DummyAsyncLLM()

        provider, resolved = self._resolve_provider(single_name)
        if provider and provider.api_key:
            logger.info(
                f"Engine resolved: {provider.__class__.__name__} (model={provider.model})"
            )
        return engine

engine_registry = EngineRegistry()
