import asyncio
import logging
from typing import Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """
    Implements a Circuit Breaker pattern to prevent infinite blocking on WAITING_FOR_APPROVAL.
    Allows automatic bypass of approvals up to a certain failure_threshold.
    """
    def __init__(self, failure_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.approvals_bypassed = 0
        self.state = "CLOSED"  # CLOSED means we can auto-approve. OPEN means we MUST wait for human.

    def can_auto_approve(self) -> bool:
        if self.state == "CLOSED":
            if self.approvals_bypassed < self.failure_threshold:
                self.approvals_bypassed += 1
                return True
            else:
                self.state = "OPEN"
                logger.warning("CircuitBreaker OPENED: Maximum auto-approvals reached. Human intervention required.")
                return False
        return False

    def reset(self):
        """Reset the circuit breaker manually if a human approves."""
        self.approvals_bypassed = 0
        self.state = "CLOSED"
        logger.info("CircuitBreaker RESET: Auto-approvals restored.")


class AdaptiveTimeoutStrategy:
    """
    Calculates adaptive timeouts based on historical execution of agents.
    """
    def __init__(self, default_timeout: float = 60.0):
        self.default_timeout = default_timeout
        self.history: Dict[str, list] = {}

    def calculate_timeout(self, agent_type: str) -> float:
        if agent_type not in self.history or len(self.history[agent_type]) < 2:
            # Increased base timeout for complex planning agents
            return 300.0 if agent_type == 'planning_agent' else self.default_timeout
        
        # Calculate timeout based on moving average + std dev buffer
        times = self.history[agent_type][-5:] # look at last 5 runs
        avg = sum(times) / len(times)
        # Add 50% buffer to average
        adaptive = avg * 1.5
        
        # Upper bounds to prevent runaway
        max_timeout = 600.0 if agent_type == 'planning_agent' else 150.0
        min_timeout = 120.0 if agent_type == 'planning_agent' else self.default_timeout
        return max(min_timeout, min(adaptive, max_timeout))

    def record_success(self, agent_type: str, duration: float):
        if agent_type not in self.history:
            self.history[agent_type] = []
        self.history[agent_type].append(duration)


class SmartAgentScheduler:
    """
    Orchestrates agent execution with timeouts and circuit breakers.
    """
    def __init__(self):
        self.timeout_strategy = AdaptiveTimeoutStrategy()
        self.circuit_breaker = CircuitBreaker(failure_threshold=3)
        
    async def execute_with_timeout(
        self, 
        agent_type: str, 
        coro: Awaitable[Any], 
        fallback_coro: Callable[[], Awaitable[Any]] = None
    ) -> Any:
        """
        Executes a coroutine with an adaptive timeout.
        If it times out, runs an optional fallback coroutine.
        """
        timeout = self.timeout_strategy.calculate_timeout(agent_type)
        logger.info(f"Executing {agent_type} with timeout {timeout:.1f}s")
        
        start_time = asyncio.get_event_loop().time()
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            duration = asyncio.get_event_loop().time() - start_time
            self.timeout_strategy.record_success(agent_type, duration)
            return result
        except asyncio.TimeoutError:
            logger.error(f"TIMEOUT: {agent_type} execution exceeded {timeout:.1f}s")
            if fallback_coro:
                logger.info(f"Running fallback strategy for {agent_type}")
                return await fallback_coro()
            raise
