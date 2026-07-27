import asyncio
import logging
import json
import os
import time
import threading
from typing import Dict, Any, Callable, Awaitable, List, Optional, Set

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """
    Implements an advanced Circuit Breaker pattern with CLOSED, OPEN, and HALF_OPEN state transitions.
    Prevents cascading failures and supports automatic trial-recovery.
    """
    def __init__(self, failure_threshold: int = 3, recovery_time_seconds: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.approvals_bypassed = 0
        self.consecutive_failures = 0
        self.state = "CLOSED"  # CLOSED (normal), OPEN (tripped), HALF_OPEN (probing)
        self.last_tripped: Optional[float] = None
        self._lock = threading.Lock()

    def can_auto_approve(self) -> bool:
        with self._lock:
            now = time.time()
            if self.state == "OPEN":
                if self.last_tripped and (now - self.last_tripped >= self.recovery_time_seconds):
                    self.state = "HALF_OPEN"
                    logger.info("CircuitBreaker state transitioned from OPEN to HALF_OPEN (recovery probe).")
                    return True
                return False

            if self.state == "HALF_OPEN":
                # Allow a single probe request
                return True

            if self.state == "CLOSED":
                if self.approvals_bypassed < self.failure_threshold:
                    self.approvals_bypassed += 1
                    return True
                else:
                    self.state = "OPEN"
                    self.last_tripped = now
                    logger.warning(f"CircuitBreaker OPENED: Maximum auto-approvals ({self.failure_threshold}) reached.")
                    return False

            return False

    def record_success(self) -> None:
        """Record a successful execution, resetting circuit breaker if in HALF_OPEN."""
        with self._lock:
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.approvals_bypassed = 0
                self.consecutive_failures = 0
                self.last_tripped = None
                logger.info("CircuitBreaker RECOVERED: Restored to CLOSED state after successful probe.")
            elif self.state == "CLOSED":
                self.consecutive_failures = 0

    def record_failure(self) -> None:
        """Record an execution failure, opening circuit breaker if threshold reached."""
        with self._lock:
            self.consecutive_failures += 1
            if self.state == "HALF_OPEN" or self.consecutive_failures >= self.failure_threshold:
                self.state = "OPEN"
                self.last_tripped = time.time()
                logger.warning(f"CircuitBreaker TRIPPED to OPEN state. Consecutive failures: {self.consecutive_failures}")

    def reset(self) -> None:
        """Reset the circuit breaker manually."""
        with self._lock:
            self.approvals_bypassed = 0
            self.consecutive_failures = 0
            self.state = "CLOSED"
            self.last_tripped = None
            logger.info("CircuitBreaker RESET manually.")


class AdaptiveTimeoutStrategy:
    """
    Calculates adaptive execution timeouts using Exponential Moving Average (EMA) and outlier rejection.
    """
    def __init__(self, default_timeout: float = 60.0, alpha: float = 0.3, persist_path: Optional[str] = None):
        self.default_timeout = default_timeout
        self.alpha = alpha  # EMA smoothing factor
        self.persist_path = persist_path
        self.history: Dict[str, List[float]] = {}
        self.ema_map: Dict[str, float] = {}
        self._load_history()

    def _load_history(self) -> None:
        if self.persist_path and os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get("history", {})
                    self.ema_map = data.get("ema_map", {})
                logger.info(f"Loaded timeout history from {self.persist_path}")
            except Exception as e:
                logger.error(f"Failed to load timeout history: {e}")

    def _save_history(self) -> None:
        if self.persist_path:
            try:
                with open(self.persist_path, 'w', encoding='utf-8') as f:
                    json.dump({"history": self.history, "ema_map": self.ema_map}, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save timeout history: {e}")

    def calculate_timeout(self, agent_type: str) -> float:
        if agent_type not in self.ema_map:
            return 300.0 if agent_type == 'planning_agent' else self.default_timeout

        ema = self.ema_map[agent_type]
        adaptive = ema * 1.6  # 60% buffer over EMA

        max_timeout = 600.0 if agent_type == 'planning_agent' else 150.0
        min_timeout = 120.0 if agent_type == 'planning_agent' else self.default_timeout
        return max(min_timeout, min(adaptive, max_timeout))

    def record_success(self, agent_type: str, duration: float) -> None:
        if agent_type not in self.history:
            self.history[agent_type] = []
            self.ema_map[agent_type] = duration
        else:
            # Filter extreme outliers (> 5x current EMA)
            current_ema = self.ema_map[agent_type]
            if duration <= current_ema * 5.0:
                self.ema_map[agent_type] = self.alpha * duration + (1 - self.alpha) * current_ema

        self.history[agent_type].append(duration)
        if len(self.history[agent_type]) > 20:
            self.history[agent_type] = self.history[agent_type][-20:]
        self._save_history()


class AgentTask:
    """Represents a scheduled agent task with dependencies, priority, and metadata."""
    def __init__(
        self, 
        task_id: str, 
        agent_type: str, 
        coro: Awaitable[Any], 
        fallback_coro: Optional[Callable[[], Awaitable[Any]]] = None, 
        priority: int = 0, 
        dependencies: Optional[List[str]] = None
    ):
        self.task_id = task_id
        self.agent_type = agent_type
        self.coro = coro
        self.fallback_coro = fallback_coro
        self.priority = priority
        self.dependencies = dependencies or []
        self.status = "PENDING"
        self.result = None
        self.error: Optional[Exception] = None
        self.created_at: float = time.time()


class SmartAgentScheduler:
    """
    Orchestrates agent execution with adaptive timeouts, half-open circuit breakers,
    and cycle-aware DAG task queues.
    """
    def __init__(self):
        self.timeout_strategy = AdaptiveTimeoutStrategy()
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_time_seconds=30.0)
        self.tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Set[str] = set()
        self.task_queue = asyncio.PriorityQueue()

    def can_auto_approve(self) -> bool:
        """Delegates auto-approval check to internal circuit breaker."""
        return self.circuit_breaker.can_auto_approve()

    def submit_task(
        self, 
        task_id: str, 
        agent_type: str, 
        coro: Awaitable[Any], 
        fallback_coro: Optional[Callable[[], Awaitable[Any]]] = None, 
        priority: int = 0, 
        dependencies: Optional[List[str]] = None
    ):
        """Submit a task to the scheduler after verifying DAG cycle safety."""
        deps = dependencies or []
        # Cycle check
        if self._detect_cycle(task_id, deps):
            raise ValueError(f"Cyclic dependency detected when submitting task '{task_id}' with deps {deps}")

        task = AgentTask(task_id, agent_type, coro, fallback_coro, priority, deps)
        self.tasks[task_id] = task
        self.task_queue.put_nowait((priority, task_id))

    def _detect_cycle(self, new_task_id: str, dependencies: List[str]) -> bool:
        """Check if adding new_task_id with dependencies introduces a cycle in the task graph."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            node_deps = dependencies if node == new_task_id else (self.tasks[node].dependencies if node in self.tasks else [])
            for dep in node_deps:
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        return dfs(new_task_id)

    def _check_engine_health(self, engine: Any) -> None:
        """Check engine health and metrics to proactively update circuit breaker."""
        if hasattr(engine, "get_stats"):
            try:
                stats = engine.get_stats()
                if stats.get("queue_size", 0) > 50 or stats.get("waiting", 0) > 100:
                    logger.warning(f"Engine overloaded (queue={stats.get('queue_size')}, waiting={stats.get('waiting')}).")
                    self.circuit_breaker.record_failure()
            except Exception as e:
                logger.debug(f"Failed to check engine health: {e}")

    def create_inference_task(
        self, 
        engine: Any, 
        prompt: str, 
        task_id: str, 
        priority: int = 0, 
        dependencies: Optional[List[str]] = None, 
        **kwargs
    ):
        """Helper to create and submit an inference task."""
        self._check_engine_health(engine)
        timeout = self.timeout_strategy.calculate_timeout("inference_engine")

        async def inference_wrapper():
            try:
                if hasattr(engine, "generate_async"):
                    return await engine.generate_async(prompt, request_id=task_id, timeout=timeout, **kwargs)
                else:
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(None, lambda: engine.generate(prompt, **kwargs))
            except Exception as e:
                logger.error(f"Inference engine failed for task {task_id}: {e}")
                raise

        self.submit_task(
            task_id=task_id,
            agent_type="inference_engine",
            coro=inference_wrapper(),
            priority=priority,
            dependencies=dependencies
        )

    async def execute_task_graph(self):
        """Executes all submitted tasks respecting DAG dependencies and priority."""
        pending_tasks = set(self.tasks.keys())
        running_tasks: Dict[str, asyncio.Task] = {}

        while pending_tasks or running_tasks:
            # Find tasks whose dependencies are fully met
            ready_tasks = [
                tid for tid in list(pending_tasks)
                if all(dep in self.completed_tasks for dep in self.tasks[tid].dependencies)
            ]

            # Sort ready tasks by priority (lower priority int = higher priority)
            ready_tasks.sort(key=lambda tid: self.tasks[tid].priority)

            for task_id in ready_tasks:
                pending_tasks.remove(task_id)
                task = self.tasks[task_id]
                running_tasks[task_id] = asyncio.create_task(
                    self.execute_with_timeout(task.agent_type, task.coro, task.fallback_coro)
                )

            if not running_tasks:
                if pending_tasks:
                    logger.error("Deadlock detected: Unable to resolve dependencies for remaining tasks.")
                    break
                break

            done, _ = await asyncio.wait(
                running_tasks.values(), 
                return_when=asyncio.FIRST_COMPLETED
            )

            for task_coro in done:
                task_id = next(tid for tid, c in running_tasks.items() if c == task_coro)
                try:
                    result = task_coro.result()
                    self.tasks[task_id].result = result
                    self.tasks[task_id].status = "COMPLETED"
                    self.circuit_breaker.record_success()
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    self.tasks[task_id].status = "FAILED"
                    self.tasks[task_id].error = e
                    self.circuit_breaker.record_failure()

                self.completed_tasks.add(task_id)
                del running_tasks[task_id]

    async def execute_with_timeout(
        self, 
        agent_type: str, 
        coro: Awaitable[Any], 
        fallback_coro: Optional[Callable[[], Awaitable[Any]]] = None
    ) -> Any:
        """
        Executes a coroutine with an adaptive EMA timeout.
        """
        timeout = self.timeout_strategy.calculate_timeout(agent_type)
        logger.info(f"Executing {agent_type} with adaptive timeout {timeout:.1f}s")

        loop = asyncio.get_running_loop()
        start_time = loop.time()
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            duration = loop.time() - start_time
            self.timeout_strategy.record_success(agent_type, duration)
            self.circuit_breaker.record_success()
            return result
        except asyncio.TimeoutError:
            logger.error(f"TIMEOUT: {agent_type} execution exceeded {timeout:.1f}s")
            self.circuit_breaker.record_failure()
            if fallback_coro:
                logger.info(f"Running fallback strategy for {agent_type}")
                return await fallback_coro()
            raise

    def get_telemetry(self) -> Dict[str, Any]:
        """Return structured telemetry metadata about tasks and circuit breaker."""
        return {
            "total_tasks": len(self.tasks),
            "completed_tasks": len(self.completed_tasks),
            "pending_tasks": len(self.tasks) - len(self.completed_tasks),
            "circuit_breaker_state": self.circuit_breaker.state,
            "circuit_breaker_bypassed": self.circuit_breaker.approvals_bypassed,
            "circuit_breaker_failures": self.circuit_breaker.consecutive_failures,
        }




