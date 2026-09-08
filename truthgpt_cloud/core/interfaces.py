"""
🏛️ TruthGPT Cloud - Core Abstract Lifecycle Interfaces
Defines abstract contracts, base classes, and protocols for all cloud subsystems:
storage, proof caching, formal verification, swarm consensus, intelligent routing,
rate limiting, subscription accounting, telemetry, resilience, webhooks, and paper compilation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Union, Callable, AsyncIterator, Iterator


class IStorageBackend(ABC):
    """Abstract interface for TruthGPT Cloud persistence engines (JSON, SQLite, Redis)."""

    @abstractmethod
    def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record by key from a collection."""
        pass

    @abstractmethod
    def set(self, collection: str, key: str, value: Dict[str, Any]) -> None:
        """Store or update a record by key in a collection."""
        pass

    @abstractmethod
    def delete(self, collection: str, key: str) -> bool:
        """Delete a record by key from a collection."""
        pass

    @abstractmethod
    def get_all(self, collection: str) -> Dict[str, Dict[str, Any]]:
        """Retrieve all records from a collection."""
        pass

    @abstractmethod
    def set_all(self, collection: str, data: Dict[str, Dict[str, Any]]) -> None:
        """Overwrite an entire collection atomically."""
        pass

    @abstractmethod
    def create_snapshot(self) -> str:
        """Create a point-in-time snapshot or backup archive."""
        pass


class IProofCache(ABC):
    """Abstract interface for semantic proof and theorem verification caches."""

    @abstractmethod
    def get_proof(self, claim: str, constraints: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a cached proof certificate for a claim."""
        pass

    @abstractmethod
    def store_proof(
        self,
        claim: str,
        certificate_data: Dict[str, Any],
        constraints: Optional[List[str]] = None,
        estimated_tokens: int = 450,
    ) -> None:
        """Store a verified proof certificate in the cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Flush and clear all entries in the cache."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Return cache hit, miss, and efficiency metrics."""
        pass

    @abstractmethod
    def __len__(self) -> int:
        """Return current count of cached proof entries."""
        pass


class IFormalVerifier(ABC):
    """Abstract interface for axiomatic and SMT formal theorem verification engines."""

    @abstractmethod
    def verify_claim(
        self,
        claim: str,
        constraints: Optional[List[str]] = None,
        tier: Optional[Any] = None,
    ) -> Any:
        """Verify an algebraic, logical, or mathematical claim and generate a cryptographic certificate."""
        pass

    @abstractmethod
    def verify_tensor_shapes(
        self,
        shape_a: List[int],
        shape_b: List[int],
        operation: str = "matmul",
    ) -> Dict[str, Any]:
        """Formally verify matrix and tensor dimension compatibility."""
        pass

    @abstractmethod
    def verify_numerical_stability(
        self,
        formula_or_loss: str,
        gradient_clipping_bound: float = 1.0,
        epsilon: float = 1e-8,
    ) -> Dict[str, Any]:
        """Formally prove absence of numerical overflows and gradient explosions."""
        pass

    @abstractmethod
    def solve_smt(
        self,
        problem_or_expr: str,
        timeout_ms: Optional[int] = None,
    ) -> Any:
        """Execute satisfiability solving via SMT solver (e.g. Z3)."""
        pass


class ISwarmOrchestrator(ABC):
    """Abstract interface for multi-agent swarm debate and topological consensus orchestration."""

    @abstractmethod
    def orchestrate(
        self,
        query: str,
        tier: Optional[Any] = None,
    ) -> Any:
        """Execute multi-agent swarm reasoning and return execution trace."""
        pass

    @abstractmethod
    def execute_debate(
        self,
        topic: str,
        rounds: int = 3,
        agents: Optional[List[Any]] = None,
    ) -> Any:
        """Execute adversarial multi-agent debate across multiple structured rounds."""
        pass

    @abstractmethod
    def get_topology_metrics(self) -> Dict[str, Any]:
        """Compute and return topological graph metrics (density, diameter, centrality)."""
        pass


class IIntelligenceRouter(ABC):
    """Abstract interface for tier-aware LLM routing and token accounting."""

    @abstractmethod
    def route(
        self,
        prompt: str,
        tier: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """Route prompt to optimal tier engine and return structured response."""
        pass

    @abstractmethod
    def stream_inference(
        self,
        prompt: str,
        tier: Optional[Any] = None,
        **kwargs: Any,
    ) -> Iterator[Any]:
        """Stream chunks from the designated tier engine."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Compute token count for a text string."""
        pass


class IRateLimiter(ABC):
    """Abstract interface for rate limiting and concurrency enforcement."""

    @abstractmethod
    def check_rate_limit(self, identifier: str, tier: Optional[Any] = None) -> bool:
        """Check whether the identifier is within allowable rate limits."""
        pass

    @abstractmethod
    def consume(self, identifier: str, tokens: int = 1, tier: Optional[Any] = None) -> None:
        """Consume request or token budget against limits."""
        pass

    @abstractmethod
    def reset(self, identifier: Optional[str] = None) -> None:
        """Reset limits for an identifier or all tracked identifiers."""
        pass


class ISubscriptionManager(ABC):
    """Abstract interface for subscription lifecycles, user accounts, and token billing."""

    @abstractmethod
    def get_user_subscription(self, user_id: str) -> Optional[Any]:
        """Retrieve user subscription state."""
        pass

    @abstractmethod
    def authenticate_api_key(self, api_key: str) -> Any:
        """Validate API key and return authenticated user subscription."""
        pass

    @abstractmethod
    def upgrade_subscription(
        self,
        user_id: str,
        new_tier: Any,
        billing_cycle: str = "monthly",
    ) -> Any:
        """Upgrade a user to a higher subscription tier."""
        pass

    @abstractmethod
    def record_usage(
        self,
        user_id: str,
        tokens: int,
        verifications: int = 0,
    ) -> None:
        """Record token consumption and verification metrics."""
        pass


class IPaymentGateway(ABC):
    """Abstract interface for payment processing and invoice settlement."""

    @abstractmethod
    def process_charge(
        self,
        user_id: str,
        amount_usd: float,
        payment_method: str = "stripe_card",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process monetary charge for subscriptions or token packs."""
        pass

    @abstractmethod
    def create_invoice(
        self,
        user_id: str,
        tier_id: str,
        amount_usd: float,
        billing_cycle: str = "monthly",
        payment_method: str = "stripe_card",
        **kwargs: Any,
    ) -> Any:
        """Generate a persistent billing invoice."""
        pass


class ITelemetryCollector(ABC):
    """Abstract interface for metrics tracking, audit logs, and Prometheus exports."""

    @abstractmethod
    def record_inference(self, latency_ms: float, tokens: int, tier: str = "pro") -> None:
        """Record inference metrics."""
        pass

    @abstractmethod
    def record_verification(self, latency_ms: float, status: str = "PROVEN_VALID") -> None:
        """Record formal verification metrics."""
        pass

    @abstractmethod
    def record_swarm(self) -> None:
        """Increment swarm orchestration event counter."""
        pass

    @abstractmethod
    def get_cluster_metrics(self) -> Dict[str, Any]:
        """Retrieve aggregated cluster metrics dictionary."""
        pass

    @abstractmethod
    def to_prometheus_text(self) -> str:
        """Format cluster metrics as standard Prometheus metrics text."""
        pass


class ICircuitBreaker(ABC):
    """Abstract interface for resilience circuit breakers and error budgets."""

    @abstractmethod
    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute function protected by circuit breaker state machine."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if circuit breaker allows requests (Closed or Half-Open)."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Force reset circuit breaker to Closed state."""
        pass


class IWebhookManager(ABC):
    """Abstract interface for event dispatching and external webhooks."""

    @abstractmethod
    def register_webhook(
        self,
        user_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
    ) -> Any:
        """Register a user webhook endpoint."""
        pass

    @abstractmethod
    def dispatch_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
    ) -> int:
        """Dispatch event payload to all subscribed webhook endpoints."""
        pass


class IPaperCompiler(ABC):
    """Abstract interface for SOTA research paper catalog and compilation."""

    @abstractmethod
    def compile_paper(self, paper_id: str, format: str = "markdown") -> str:
        """Compile a research paper into formatted output."""
        pass

    @abstractmethod
    def search_papers(self, query: str) -> List[Any]:
        """Search paper registry by query terms."""
        pass


__all__ = [
    "IStorageBackend",
    "IProofCache",
    "IFormalVerifier",
    "ISwarmOrchestrator",
    "IIntelligenceRouter",
    "IRateLimiter",
    "ISubscriptionManager",
    "IPaymentGateway",
    "ITelemetryCollector",
    "ICircuitBreaker",
    "IWebhookManager",
    "IPaperCompiler",
]
