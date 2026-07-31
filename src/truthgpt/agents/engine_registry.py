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
try:
    from .ensemble import ALL_ENSEMBLE_MODES, run_ensemble
except ImportError:
    ALL_ENSEMBLE_MODES, run_ensemble = [], None


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
        self, active: List[Dict[str, str]], mode: str, callable_resolver=None
    ) -> AsyncLLMEngine:
        """Run all active engines and merge outputs (consensus, parallel, etc.).

        ``callable_resolver`` maps an engine key to its async callable. Defaults
        to standard single-engine resolution; tiered missions pass a resolver
        bound to pre-built, model-overridden providers.
        """
        registry = self
        mode = (mode or "consensus").lower().strip()
        resolver = callable_resolver or registry._get_single_engine_callable

        async def _run_engine_key(
            key: str, eng: Dict[str, str], prompt: str, **kw
        ) -> tuple:
            sub = resolver(key)
            if not sub:
                return key, eng["model"], "", 0.0, 0
            t0 = time.time()
            try:
                text = await sub(prompt, **kw)
            except Exception as exc:
                msg = str(exc)
                # Rate-limit / quota exhaustion (e.g. OpenAI 429) is an expected,
                # recoverable condition — log it as a warning, not an error.
                if any(s in msg.lower() for s in ("429", "quota", "rate limit", "ratelimit")):
                    logger.warning(f"Ensemble engine '{key}' skipped (rate limit/quota): {exc}")
                else:
                    logger.error(f"Ensemble engine '{key}' failed: {exc}")
                # Return empty text so this engine is EXCLUDED from the merge
                # (see ensemble_strategies._prepare_parsed). Otherwise the error
                # string would become a candidate answer in consensus/majority
                # voting and could be selected as the final answer.
                text = ""
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

    # ── Cost/quality tiers ────────────────────────────────────────
    # Maps a tier to the model variant used for each (normalized) provider.
    # Keys match _normalize_engine_key output: deepseek, google, chatgpt, claude.
    # Providers absent from a tier keep their default/preferred model.
    TIER_MODELS: Dict[str, Dict[str, str]] = {
        "economica": {
            "deepseek": "deepseek-v4-flash",
            "google": "gemini-2.0-flash-exp",
            "chatgpt": "gpt-4o-mini",
            "claude": "claude-haiku-4-5-20251001",
            "openrouter": "~anthropic/claude-haiku-latest",
        },
        "media": {
            "deepseek": "deepseek-v4-pro",
            "google": "gemini-2.0-flash-exp",
            "chatgpt": "gpt-4o",
            "claude": "claude-sonnet-4-6",
            "openrouter": "~anthropic/claude-sonnet-latest",
        },
        "alta": {
            "deepseek": "deepseek-reasoner",
            "google": "gemini-2.0-pro-exp-02-05",
            "chatgpt": "gpt-4o",
            "claude": "claude-opus-4-8",
            "openrouter": "~anthropic/claude-opus-latest",
        },
    }

    # Approx per-1M-token pricing (USD) for the concrete model IDs the tiers use.
    # Only used for savings analytics / budget tracking — values are estimates.
    MODEL_PRICING_USD: Dict[str, Dict[str, float]] = {
        "deepseek-v4-flash": {"input": 0.07, "output": 0.28},
        "deepseek-v4-pro": {"input": 0.55, "output": 2.19},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gemini-2.0-flash-exp": {"input": 0.075, "output": 0.30},
        "gemini-2.0-pro-exp-02-05": {"input": 1.25, "output": 5.00},
        "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
        "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
        "claude-opus-4-8": {"input": 15.00, "output": 75.00},
        "~anthropic/claude-haiku-latest": {"input": 1.00, "output": 5.00},
        "~anthropic/claude-sonnet-latest": {"input": 3.00, "output": 15.00},
        "~anthropic/claude-opus-latest": {"input": 15.00, "output": 75.00},
    }

    def build_tiered_engine(
        self, tier: str, name: Optional[str] = None, cost_optimized: bool = False,
        enable_cache: bool = True,
    ) -> Optional[AsyncLLMEngine]:
        """Build an engine that runs the configured engine set at a cost/quality tier.

        The tier ('economica' | 'media' | 'alta') selects the model variant for
        every provider in the active set, so an ensemble of N engines runs all N
        at the chosen tier. Falls back to standard resolution if no tiered engine
        has an API key.

        When ``cost_optimized`` is set, the engine instead runs a FrugalGPT
        cascade (cheap → tier-top) on the *primary* provider plus a shared
        semantic cache and prompt compression, so the best models are only paid
        for when a cheaper one is not confident enough. (Cascading and N-way
        ensembles pull in opposite cost directions, so the cost path is single
        primary provider by design.)

        ``enable_cache`` toggles the semantic response cache on the cost path.
        Leave it on for one-shot Q&A; turn it OFF for self-refining loops (e.g.
        the autonomous RLHF mission), where near-identical prompts across
        iterations would otherwise replay the first cached answer forever.
        """
        _load_api_keys_from_prefs()
        tier = (str(tier) or "media").lower().strip()
        tier_map = self.TIER_MODELS.get(tier, self.TIER_MODELS["media"])

        prefs = _get_user_prefs()
        preferred_raw = name or prefs.get("preferred_engine", "deepseek")
        base_keys: List[str] = []
        seen: set[str] = set()
        for raw in str(preferred_raw).split(","):
            raw = raw.strip()
            # Strip any "provider:model" suffix (e.g. "openrouter:google/gemini-3.5-pro")
            # so provider-qualified selections from the engine menu are honored instead
            # of being silently dropped (which collapsed the cascade to deepseek+claude).
            base = raw.split(":", 1)[0].strip() if ":" in raw else raw
            key = _normalize_engine_key(base)
            if key and key in self._default_providers and key not in seen:
                seen.add(key)
                base_keys.append(key)
        if not base_keys:
            base_keys = ["deepseek"]

        if cost_optimized:
            engine = self._build_cost_optimized_engine(tier, base_keys, enable_cache=enable_cache)
            if engine is not None:
                return engine
            logger.warning("Cost-optimized engine unavailable; using standard tier engine.")

        # Instantiate fresh providers with the tier-specific model override.
        instances: List[tuple[str, BaseProvider]] = []
        for base in base_keys:
            model = tier_map.get(base)
            provider_cls = self._default_providers[base]
            # force_model lets the tier model win over any stored engine_models pref.
            provider = provider_cls(model=model, force_model=True) if model else provider_cls()
            if provider.api_key:
                instances.append((base, provider))

        if not instances:
            logger.warning(
                "No tiered engine has an API key; falling back to default resolution."
            )
            return self.get_engine(name)

        if len(instances) == 1:
            base, provider = instances[0]
            logger.info(f"Tiered engine [{tier}]: {base} (model={provider.model})")
            return self._provider_callable(provider, base)

        callables = {
            base: self._provider_callable(provider, base)
            for base, provider in instances
        }
        active = [{"key": base, "model": provider.model} for base, provider in instances]
        ensemble_mode = str(prefs.get("ensemble_mode", "race")).lower()
        if ensemble_mode not in ALL_ENSEMBLE_MODES:
            ensemble_mode = "consensus"
        logger.info(
            f"Tiered ensemble [{tier}/{ensemble_mode}]: "
            f"{[(a['key'], a['model']) for a in active]}"
        )
        return self._build_ensemble_engine(
            active, ensemble_mode, callable_resolver=lambda key: callables.get(key)
        )

    def _provider_callable(self, provider: BaseProvider, key: str) -> AsyncLLMEngine:
        """Wrap a concrete provider instance as a single-engine async callable."""
        async def _call(prompt: str, **kwargs) -> str:
            return await provider.generate(prompt, **kwargs)

        _call.model_name = provider.model
        _call.provider_name = key
        _call.is_ensemble = False
        return _call

    def _cascade_ladder(self, base_key: str, tier: str) -> List[str]:
        """Cheap→tier-top model ladder for a provider, deduped by effective model.

        e.g. claude/alta → ['claude-haiku-4-5-20251001', 'claude-sonnet-4-6',
        'claude-opus-4-8']; deepseek/alta collapses flash→pro (reasoner == pro).
        """
        order = ["economica", "media", "alta"]
        if tier not in order:
            tier = "media"
        steps = order[: order.index(tier) + 1]
        provider_cls = self._default_providers[base_key]
        ladder: List[str] = []
        seen_effective: set[str] = set()
        for step in steps:
            raw = self.TIER_MODELS[step].get(base_key)
            if not raw:
                continue
            # Normalize via the provider so duplicates (e.g. reasoner→v4-pro) collapse.
            effective = provider_cls(model=raw, force_model=True).model
            if effective not in seen_effective:
                seen_effective.add(effective)
                ladder.append(raw)
        return ladder

    def _price_of(self, model_id: str) -> float:
        """Rough $/1M-token cost proxy (input + output) for cascade ordering.

        Unknown models sort last (treated as expensive) so they are only reached
        as a last resort.
        """
        rates = self.MODEL_PRICING_USD.get(model_id)
        if not rates:
            return float("inf")
        return rates.get("input", 0.0) + rates.get("output", 0.0)

    def _global_cascade_ladder(
        self, base_keys: List[str], tier: str
    ) -> tuple[List[str], Dict[str, type]]:
        """Cost-ascending cascade spanning *all* configured providers up to *tier*.

        Returns (ordered model_ids cheapest→priciest, {model_id: provider_cls}).
        Deduped by effective model so equivalent variants are not retried.
        """
        candidates: List[tuple[float, str]] = []
        provider_of: Dict[str, type] = {}
        seen_effective: set[str] = set()
        order = ["economica", "media", "alta"]
        if tier not in order:
            tier = "media"
        steps = order[: order.index(tier) + 1]

        for base in base_keys:
            provider_cls = self._default_providers[base]
            for step in steps:
                raw = self.TIER_MODELS[step].get(base)
                if not raw:
                    continue
                effective = provider_cls(model=raw, force_model=True).model
                if effective in seen_effective:
                    continue
                seen_effective.add(effective)
                provider_of[raw] = provider_cls
                candidates.append((self._price_of(raw), raw))

        candidates.sort(key=lambda c: c[0])
        ladder = [model_id for _, model_id in candidates]
        return ladder, provider_of

    def _build_cost_optimized_engine(
        self, tier: str, base_keys: List[str], enable_cache: bool = True
    ) -> Optional[AsyncLLMEngine]:
        """FrugalGPT cascade (cheapest→best across all providers) + cache + compression.

        The ladder spans every configured provider that has an API key, ordered by
        price, so the cheapest capable model answers first and the priciest model
        is only paid for when nothing cheaper is confident enough.
        """
        try:
            from truthgpt.modules.api_cost import APICostOptimizer, APICostConfig
        except Exception as exc:  # pragma: no cover - optional dependency surface
            logger.warning(f"Cost optimization module unavailable: {exc}")
            return None

        # Keep only providers that actually have an API key.
        live_keys = [
            base for base in base_keys
            if self._default_providers[base](force_model=False).api_key
        ]
        if not live_keys:
            return None

        ladder, provider_of = self._global_cascade_ladder(live_keys, tier)
        if not ladder:
            return None

        provider_cache: Dict[str, BaseProvider] = {}

        def _provider_for(model_id: str) -> BaseProvider:
            prov = provider_cache.get(model_id)
            if prov is None:
                prov = provider_of[model_id](model=model_id, force_model=True)
                provider_cache[model_id] = prov
            return prov

        # Best-effort per-call trace for reporting which model resolved the query.
        trace: Dict[str, Any] = {"models": []}
        stats: Dict[str, Any] = {
            "calls": 0, "cache_hits": 0, "resolved_below_top": 0,
            "by_model": {}, "last": None,
        }
        top_model = ladder[-1]

        async def _model_llm(prompt: str, model: Optional[str] = None, **kw) -> str:
            model_id = model or top_model
            trace["models"].append(model_id)
            # Drop kwargs the providers don't accept (cascade passes none extra).
            return await _provider_for(model_id).generate(prompt)

        cfg = APICostConfig(daily_budget_usd=1_000_000.0)  # track savings, never hard-stop
        cfg.model_pricing.update(self.MODEL_PRICING_USD)
        # Cascade thresholds: be willing to accept the cheaper model fairly often.
        cfg.model_cascade.confidence_threshold = 0.7
        # Self-refining loops must not replay a cached answer for near-identical
        # prompts; callers can disable the semantic cache while keeping the cascade.
        cfg.enable_semantic_cache = enable_cache
        optimizer = APICostOptimizer(cfg)

        async def _call(prompt: str, **kwargs) -> str:
            trace["models"] = []
            response = await optimizer.call(prompt, _model_llm, models=list(ladder))
            used = trace["models"][-1] if trace["models"] else "cache"
            stats["calls"] += 1
            stats["last"] = used
            if used == "cache":
                stats["cache_hits"] += 1
            else:
                stats["by_model"][used] = stats["by_model"].get(used, 0) + 1
                if used != top_model:
                    stats["resolved_below_top"] += 1
            return response

        _call.model_name = " → ".join(ladder)
        _call.provider_name = ",".join(live_keys)
        _call.is_ensemble = False
        _call.cost_optimizer = optimizer
        _call.cascade_models = list(ladder)
        _call.cascade_stats = stats
        logger.info(f"Cost-optimized cascade [{tier}]: {' → '.join(ladder)}")
        return _call

engine_registry = EngineRegistry()
