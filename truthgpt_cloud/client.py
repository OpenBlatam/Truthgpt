"""
🚀 TruthGPT Cloud - Official Python SDK Client
Enables seamless developer interaction with TruthGPT Cloud services,
tier management, Z3 formal verification, and multi-agent swarm orchestration.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union

from .core.tiers import CloudTier, TierConfig, get_tier_config, get_all_tiers
from .billing import subscription_manager, UserSubscription
from .engine_router import cloud_router, CloudInferenceResponse
from .verification import cloud_verifier, ProofCertificate
from .swarm import cloud_swarm, SwarmExecutionTrace


class TruthGPTCloudClient:
    """
    Developer Client SDK for TruthGPT Cloud.
    Supports both asynchronous and synchronous paradigms.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        tier: Optional[Union[str, CloudTier]] = None
    ):
        self.sub_manager = subscription_manager
        self.router = cloud_router
        self.verifier = cloud_verifier
        self.swarm = cloud_swarm
        
        # Resolve user
        self.user: Optional[UserSubscription] = None
        if api_key:
            self.user = self.sub_manager.get_user_by_api_key(api_key)
        elif user_id:
            self.user = self.sub_manager.get_user(user_id)
            
        if not self.user:
            # Fallback to default demo user or create with specified tier
            tier_enum = CloudTier(tier.lower()) if (isinstance(tier, str) and tier) else (tier if isinstance(tier, CloudTier) else CloudTier.FREE)
            self.user = self.sub_manager.get_user("usr_default_demo")
            if not self.user:
                self.user = self.sub_manager.register_user(
                    email="developer@truthgpt.ai",
                    name="TruthGPT Developer",
                    tier=tier_enum
                )

        self.api_key = self.user.api_keys[0] if self.user.api_keys else "tgpt_cloud_live_demo"
        self.user_id = self.user.user_id

    @property
    def tier(self) -> CloudTier:
        user = self.sub_manager.get_user(self.user_id)
        return user.tier if user else CloudTier.FREE

    @property
    def tier_config(self) -> TierConfig:
        return get_tier_config(self.tier)

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
        """
        Synchronous wrapper for ask_async.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                pass
            return loop.run_until_complete(
                self.ask_async(prompt, model, enable_swarm, enable_formal_verification, constraints)
            )
        else:
            return loop.run_until_complete(
                self.ask_async(prompt, model, enable_swarm, enable_formal_verification, constraints)
            )

    # ---------------------------------------------------------------------------
    # 🛡️ Formal Verification API
    # ---------------------------------------------------------------------------

    def verify_claim(
        self,
        claim: str,
        constraints: Optional[List[str]] = None,
        depth_level: Optional[int] = None
    ) -> ProofCertificate:
        """
        Formally verify an algebraic, mathematical, or invariant claim using Z3 SMT Prover.
        """
        depth = depth_level if depth_level is not None else self.tier_config.smt_z3_verification_depth
        return self.verifier.verify_expression(
            claim_text=claim,
            constraints=constraints,
            tier_depth=depth
        )

    # ---------------------------------------------------------------------------
    # 🐝 Multi-Agent Swarm API
    # ---------------------------------------------------------------------------

    async def run_swarm_async(self, prompt: str, max_agents: Optional[int] = None) -> SwarmExecutionTrace:
        """
        Run an autonomous multi-agent swarm research round asynchronously.
        """
        limit = max_agents or self.tier_config.max_swarm_agents
        return await self.swarm.execute_swarm_session(
            prompt=prompt,
            user_id=self.user_id,
            max_agents=limit,
            depth_level=self.tier_config.smt_z3_verification_depth
        )

    def run_swarm(self, prompt: str, max_agents: Optional[int] = None) -> SwarmExecutionTrace:
        """
        Run an autonomous multi-agent swarm research round synchronously.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                pass
            return loop.run_until_complete(self.run_swarm_async(prompt, max_agents))
        else:
            return loop.run_until_complete(self.run_swarm_async(prompt, max_agents))

    # ---------------------------------------------------------------------------
    # 💳 Subscription & Tier Management
    # ---------------------------------------------------------------------------

    def get_subscription_status(self) -> Dict[str, Any]:
        """Get current tier status, quotas, and remaining token metrics."""
        return self.sub_manager.get_user_status_summary(self.user_id)

    def upgrade_tier(
        self,
        new_tier: Union[str, CloudTier],
        billing_cycle: str = "monthly",
        payment_method: str = "stripe_card"
    ) -> Dict[str, Any]:
        """Upgrade current subscription tier."""
        tier_enum = CloudTier(new_tier.lower()) if isinstance(new_tier, str) else new_tier
        return self.sub_manager.upgrade_subscription(
            user_id=self.user_id,
            target_tier=tier_enum,
            billing_cycle=billing_cycle,
            payment_method=payment_method
        )

    def generate_api_key(self) -> str:
        """Generate an additional API key under current subscription limits."""
        key = self.sub_manager.generate_new_api_key(self.user_id)
        if not key:
            raise RuntimeError("Failed to generate API key")
        return key

    @staticmethod
    def list_available_tiers() -> List[Dict[str, Any]]:
        """List all subscription tier offerings and pricing matrices."""
        return get_all_tiers()


__all__ = ["TruthGPTCloudClient"]
