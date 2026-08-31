"""
🚀 TruthGPT Cloud - Official Python SDK Client
Enables seamless developer interaction with TruthGPT Cloud services,
tier management, Z3 formal verification, and multi-agent swarm orchestration.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union

from ..core.tiers import CloudTier, TierConfig, get_tier_config, get_all_tiers
from ..billing.subscription import subscription_manager, UserSubscription
from ..routing.router import cloud_router, CloudInferenceResponse
from ..verification.verifier import cloud_verifier
from ..verification.certificate import ProofCertificate
from ..swarm.orchestrator import cloud_swarm, SwarmExecutionTrace
from ..papers.compiler import cloud_paper_compiler


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
        self.paper_compiler = cloud_paper_compiler
        
        # Resolve user
        self.user: Optional[UserSubscription] = None
        if api_key:
            self.user = self.sub_manager.get_user_by_api_key(api_key)
        elif user_id:
            self.user = self.sub_manager.get_user(user_id)
            
        if not self.user:
            # Fallback to default demo user or create with specified tier
            tier_enum = CloudTier(tier.lower()) if tier else CloudTier.FREE
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
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self.ask_async(
                            prompt=prompt,
                            model=model,
                            enable_swarm=enable_swarm,
                            enable_formal_verification=enable_formal_verification,
                            constraints=constraints
                        )
                    ).result()
            return loop.run_until_complete(
                self.ask_async(
                    prompt=prompt,
                    model=model,
                    enable_swarm=enable_swarm,
                    enable_formal_verification=enable_formal_verification,
                    constraints=constraints
                )
            )
        except RuntimeError:
            return asyncio.run(
                self.ask_async(
                    prompt=prompt,
                    model=model,
                    enable_swarm=enable_swarm,
                    enable_formal_verification=enable_formal_verification,
                    constraints=constraints
                )
            )

    async def stream_async(
        self,
        prompt: str,
        model: Optional[str] = None
    ):
        """
        Stream reasoning tokens and formal verification metadata asynchronously.
        """
        async for chunk in self.router.stream_inference(
            prompt=prompt,
            user_id=self.user_id,
            model_override=model
        ):
            yield chunk

    async def stream_chat(
        self,
        prompt: str,
        model: Optional[str] = None
    ):
        """
        Alias for stream_async.
        """
        async for chunk in self.stream_async(prompt, model):
            yield chunk


    def stream(
        self,
        prompt: str,
        model: Optional[str] = None
    ):
        """
        Stream reasoning tokens and formal verification metadata synchronously as an iterator.
        """
        async def _collect():
            chunks = []
            async for c in self.stream_async(prompt, model):
                chunks.append(c)
            return chunks

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return iter(pool.submit(asyncio.run, _collect()).result())
            return iter(loop.run_until_complete(_collect()))
        except RuntimeError:
            return iter(asyncio.run(_collect()))

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
        Directly verify a mathematical, algorithmic or logical invariant with Z3 SMT in the cloud.
        """
        tier_cfg = self.tier_config
        depth = depth_level if depth_level is not None else tier_cfg.smt_z3_verification_depth
        return self.verifier.verify_expression(
            claim_text=claim,
            constraints=constraints,
            tier_depth=depth
        )

    def verify_batch(
        self,
        claims: List[str],
        depth_level: Optional[int] = None
    ) -> List[ProofCertificate]:
        """
        Verify multiple mathematical propositions in batch with Merkle proof trees.
        """
        tier_cfg = self.tier_config
        depth = depth_level if depth_level is not None else tier_cfg.smt_z3_verification_depth
        return self.verifier.verify_batch(claims=claims, tier_depth=depth)

    def verify_certificate(self, certificate: ProofCertificate) -> bool:
        """
        Cryptographically verify that a ProofCertificate is authentic, uncorrupted, and valid.
        """
        return certificate.verify_integrity()

    def verify_contract(
        self,
        preconditions: List[str],
        postconditions: List[str],
        invariants: Optional[List[str]] = None,
        function_name: str = "routine_spec",
        code_snippet: Optional[str] = None
    ):
        """
        Execute Design-by-Contract (DbC) Hoare Triple verification.
        """
        return self.verifier.verify_contract(
            preconditions=preconditions,
            postconditions=postconditions,
            invariants=invariants,
            function_name=function_name,
            code_snippet=code_snippet,
            tier_depth=self.tier_config.smt_z3_verification_depth
        )



    # ---------------------------------------------------------------------------
    # 🐝 Multi-Agent Swarm Execution
    # ---------------------------------------------------------------------------

    async def run_swarm_async(
        self,
        prompt: str,
        max_agents: Optional[int] = None
    ) -> SwarmExecutionTrace:
        """
        Execute an autonomous multi-agent swarm research cycle.
        """
        tier_cfg = self.tier_config
        num_agents = max_agents if max_agents is not None else tier_cfg.max_swarm_agents
        return await self.swarm.execute_swarm_session(
            prompt=prompt,
            user_id=self.user_id,
            max_agents=num_agents,
            depth_level=tier_cfg.smt_z3_verification_depth
        )

    # ---------------------------------------------------------------------------
    # 🔬 SOTA Paper Compiler
    # ---------------------------------------------------------------------------

    def compile_paper(self, paper_id: str) -> Dict[str, Any]:
        """Compile SOTA research paper architecture and inject into cloud pipeline."""
        return self.paper_compiler.compile_paper_technique(paper_id, user_tier=self.tier.value)

    # ---------------------------------------------------------------------------
    # 💳 Subscription & Account Management
    # ---------------------------------------------------------------------------

    def get_subscription_status(self) -> Dict[str, Any]:
        """Get live token quota, tier status, and billing metrics."""
        return self.sub_manager.get_user_status_summary(self.user_id)

    def upgrade_tier(
        self,
        target_tier: Union[str, CloudTier],
        billing_cycle: str = "monthly",
        payment_method: str = "stripe_card"
    ) -> Dict[str, Any]:
        """Upgrade subscription tier with checkout simulation."""
        tier_enum = CloudTier(target_tier.lower()) if isinstance(target_tier, str) else target_tier
        return self.sub_manager.upgrade_subscription(
            user_id=self.user_id,
            target_tier=tier_enum,
            billing_cycle=billing_cycle,
            payment_method=payment_method
        )

    def generate_api_key(self) -> str:
        """Generate a new dedicated API key."""
        return self.sub_manager.generate_new_api_key(self.user_id)

    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an active API key."""
        return self.sub_manager.revoke_api_key(self.user_id, api_key)
