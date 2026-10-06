"""
🚀 TruthGPT Cloud - Official Python SDK Client
Enables seamless developer interaction with TruthGPT Cloud services,
tier management, Z3 formal verification, and multi-agent swarm orchestration.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union, AsyncGenerator

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False

from ..core.tiers import CloudTier, TierConfig, calculate_request_cost
from ..core.health import cloud_health_checker
from ..billing.subscription import subscription_manager, UserSubscription
from ..billing.webhooks import webhook_manager
from ..routing.router import cloud_router, CloudInferenceResponse
from ..verification.verifier import cloud_verifier
from ..swarm.orchestrator import cloud_swarm
from ..papers.compiler import cloud_paper_compiler
from ..telemetry import cloud_telemetry
from ..cache import proof_cache
from ..security.manager import cloud_security

from .http_layer import ClientHttpMixin, _run_sync
from .billing_client import ClientBillingMixin
from .verification_client import ClientVerificationMixin
from .swarm_client import ClientSwarmMixin
from .papers_client import ClientPapersMixin
from .ops_client import ClientOpsMixin


class TruthGPTCloudClient(
    ClientHttpMixin,
    ClientBillingMixin,
    ClientVerificationMixin,
    ClientSwarmMixin,
    ClientPapersMixin,
    ClientOpsMixin,
):
    """
    Developer Client SDK for TruthGPT Cloud.
    Supports both asynchronous and synchronous paradigms across all platform capabilities,
    with seamless in-process execution and high-performance remote HTTP/REST/SSE client via httpx.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        tier: Optional[Union[str, CloudTier]] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        http_client: Optional[Any] = None,
        context: Optional[Any] = None,
    ):
        if context is not None:
            self.context = context
            self.sub_manager = context.subscription_manager
            self.router = context.router
            self.verifier = context.verifier
            self.swarm = context.swarm
            self.paper_compiler = context.paper_compiler
            self.webhooks = context.webhooks
            self.telemetry = context.telemetry
            self.cache = context.cache
            self.security = context.security
            self.health_checker = getattr(context, "health_checker", cloud_health_checker)
            self.secrets = getattr(context, "secrets", None)
            self.rate_limiter = getattr(context, "rate_limiter", None)
            self.circuit_breaker = getattr(context, "circuit_breaker", None)
            self.adaptive_limiter = getattr(context, "adaptive_limiter", None)
        else:
            self.context = None
            self.sub_manager = subscription_manager
            self.router = cloud_router
            self.verifier = cloud_verifier
            self.swarm = cloud_swarm
            self.paper_compiler = cloud_paper_compiler
            self.webhooks = webhook_manager
            self.telemetry = cloud_telemetry
            self.cache = proof_cache
            self.security = cloud_security
            self.health_checker = cloud_health_checker
            self.secrets = None
            self.rate_limiter = None
            self.circuit_breaker = None
            self.adaptive_limiter = None

        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = timeout
        self._is_remote = bool(self.base_url)
        self._http_client = http_client
        self._async_http_client = None

        # Resolve user
        self.user: Optional[UserSubscription] = None
        if api_key:
            self.user = self.sub_manager.get_user_by_api_key(api_key)
        elif user_id:
            self.user = self.sub_manager.get_user(user_id)

        if not self.user:
            # Fallback to demo user matching requested tier or default demo user
            tier_enum = (
                CloudTier(tier.lower())
                if (isinstance(tier, str) and tier)
                else (tier if isinstance(tier, CloudTier) else None)
            )
            if tier_enum:
                for u in self.sub_manager._users.values():
                    if u.tier == tier_enum:
                        self.user = u
                        break
                if not self.user:
                    self.user = self.sub_manager.register_user(
                        email=f"{tier_enum.value}_developer@truthgpt.ai",
                        name=f"TruthGPT {tier_enum.value.capitalize()} Developer",
                        tier=tier_enum
                    )
            else:
                self.user = self.sub_manager.get_user("usr_default_demo")
                if not self.user:
                    self.user = self.sub_manager.register_user(
                        email="developer@truthgpt.ai",
                        name="TruthGPT Developer",
                        tier=CloudTier.FREE
                    )

        self.api_key = self.user.api_keys[0] if self.user.api_keys else "tgpt_cloud_live_demo"
        self.user_id = self.user.user_id
        super().__init__()

    def __repr__(self) -> str:
        return f"<TruthGPTCloudClient user_id='{self.user_id}' tier={self.tier.value}>"

    def __str__(self) -> str:
        return f"TruthGPTCloudClient(user_id='{self.user_id}', tier='{self.tier.value}')"

    def calculate_cost(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        is_verification: bool = False,
        swarm_agents: int = 0,
        tier: Optional[Union[str, CloudTier, TierConfig]] = None,
    ) -> float:
        """
        Calculate or estimate request expenditure in USD for this client's tier or a specified tier.
        """
        target_tier = tier if tier is not None else self.tier_config
        return calculate_request_cost(
            tier=target_tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            is_verification=is_verification,
            swarm_agents=swarm_agents,
        )

    estimate_cost = calculate_cost

    # ---------------------------------------------------------------------------
    # 💬 Async & Sync Cloud Inference
    # ---------------------------------------------------------------------------

    async def ask_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        enable_swarm: Optional[bool] = None,
        enable_formal_verification: Optional[bool] = None,
        constraints: Optional[List[str]] = None
    ) -> CloudInferenceResponse:
        """
        Execute an asynchronous reasoning query on TruthGPT Cloud with formal verification.
        """
        return await self.router.route_inference(
            prompt=prompt,
            user_id=self.user_id,
            model_override=model,
            enable_swarm=enable_swarm,
            enable_formal_verification=enable_formal_verification,
            constraints=constraints
        )

    def ask(
        self,
        prompt: str,
        model: Optional[str] = None,
        enable_swarm: Optional[bool] = None,
        enable_formal_verification: Optional[bool] = None,
        constraints: Optional[List[str]] = None
    ) -> CloudInferenceResponse:
        """Synchronous wrapper for ask_async."""
        return _run_sync(
            self.ask_async(
                prompt=prompt,
                model=model,
                enable_swarm=enable_swarm,
                enable_formal_verification=enable_formal_verification,
                constraints=constraints
            )
        )

    async def batch_ask_async(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        enable_formal_verification: bool = True
    ) -> List[CloudInferenceResponse]:
        """Execute multiple prompts in parallel on TruthGPT Cloud."""
        tasks = [
            self.ask_async(
                prompt=p,
                model=model,
                enable_formal_verification=enable_formal_verification
            )
            for p in prompts
        ]
        return await asyncio.gather(*tasks)

    def batch_ask(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        enable_formal_verification: bool = True
    ) -> List[CloudInferenceResponse]:
        """Synchronous wrapper for batch_ask_async."""
        return _run_sync(self.batch_ask_async(prompts, model, enable_formal_verification))

    # ---------------------------------------------------------------------------
    # 🌊 Streaming APIs
    # ---------------------------------------------------------------------------

    async def stream_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        enable_formal_verification: Optional[bool] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream reasoning chunks and formal verification metadata asynchronously."""
        async for chunk in self.router.stream_inference(
            prompt=prompt,
            user_id=self.user_id,
            model_override=model,
            enable_formal_verification=enable_formal_verification
        ):
            yield chunk

    async def stream_chat(
        self,
        prompt: str,
        model: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Alias for stream_async."""
        async for chunk in self.stream_async(prompt, model):
            yield chunk

    async def ask_stream_async(
        self,
        prompt: str,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Yields text deltas directly as strings for seamless CLI and terminal streaming."""
        async for chunk in self.stream_async(prompt, model):
            if chunk.get("type") == "token_chunk":
                yield chunk.get("delta", "")

    def stream(
        self,
        prompt: str,
        model: Optional[str] = None
    ):
        """Stream reasoning tokens and formal verification metadata synchronously as an iterator."""
        async def _collect():
            chunks = []
            async for c in self.stream_async(prompt, model):
                chunks.append(c)
            return chunks

        return iter(_run_sync(_collect()))


__all__ = ["TruthGPTCloudClient"]
