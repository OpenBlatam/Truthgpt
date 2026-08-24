"""
Fluent Multi-Stage Learning Pipeline
====================================
Orchestrates heterogeneous learning algorithms into sequential or conditional
multi-stage training workflows with execution telemetry, error boundaries,
and checkpointing.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from .config import PipelineConfig
from .exceptions import PipelineExecutionError
from .interfaces import BaseCallback, BaseLearner, BaseLearningOptimizer, BaseLearningPipeline
from .types import PipelineStageResult

logger = logging.getLogger(__name__)


class PipelineStage:
    """Represents a single executable stage within a LearningPipeline."""

    def __init__(
        self,
        name: str,
        module: Union[BaseLearner, BaseLearningOptimizer, Callable[..., Any]],
        config: Optional[Any] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        pass_previous_output: bool = True,
    ) -> None:
        self.name = name
        self.module = module
        self.config = config
        self.condition = condition
        self.pass_previous_output = pass_previous_output

    def can_run(self, pipeline_context: Dict[str, Any]) -> bool:
        """Evaluate if conditional requirements for this stage are satisfied."""
        if self.condition is None:
            return True
        try:
            return bool(self.condition(pipeline_context))
        except Exception as e:
            logger.warning("Condition check failed for stage '%s': %s", self.name, e)
            return False

    def execute(self, current_input: Any, context: Dict[str, Any]) -> PipelineStageResult:
        """Execute this individual pipeline stage."""
        start_time = time.time()
        strategy_name = type(self.module).__name__

        try:
            logger.info("▶️ Executing Pipeline Stage: '%s' (%s)", self.name, strategy_name)

            if hasattr(self.module, "fit"):
                output = self.module.fit(current_input)
            elif hasattr(self.module, "optimize"):
                output = self.module.optimize(current_input)
            elif hasattr(self.module, "transfer"):
                output = self.module.transfer(current_input)
            elif callable(self.module):
                output = self.module(current_input, context=context)
            else:
                raise PipelineExecutionError(
                    f"Stage module '{self.name}' has no fit/optimize method and is not callable."
                )

            duration = time.time() - start_time
            metrics = output if isinstance(output, dict) else {"stage_completed": 1.0}

            logger.info("✅ Finished Stage '%s' in %.3fs", self.name, duration)
            return PipelineStageResult(
                stage_name=self.name,
                strategy_type=strategy_name,
                status="SUCCESS",
                duration_seconds=duration,
                output_data=output,
                metrics={k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))},
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error("❌ Stage '%s' failed after %.3fs: %s", self.name, duration, e)
            return PipelineStageResult(
                stage_name=self.name,
                strategy_type=strategy_name,
                status="FAILED",
                duration_seconds=duration,
                output_data=None,
                error_message=str(e),
            )


class LearningPipeline(BaseLearningPipeline):
    """
    Fluent multi-stage orchestrator for complex end-to-end learning workflows.
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        callbacks: Optional[List[BaseCallback]] = None,
    ) -> None:
        self.config = config or PipelineConfig()
        self.callbacks = callbacks or []
        self._stages: List[PipelineStage] = []
        self._execution_history: List[PipelineStageResult] = []

    def add_stage(
        self,
        stage_name: str,
        module: Union[BaseLearner, BaseLearningOptimizer, Callable[..., Any]],
        config: Optional[Any] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        pass_previous_output: bool = True,
    ) -> LearningPipeline:
        """
        Append a stage to the pipeline (fluent builder pattern).
        
        Args:
            stage_name: Unique identifier for the stage.
            module: Learner, Optimizer, or callable execution unit.
            config: Optional stage configuration.
            condition: Optional predicate to determine if stage should run.
            pass_previous_output: If True, feeds preceding stage's output as input.
            
        Returns:
            self for chaining.
        """
        stage = PipelineStage(
            name=stage_name,
            module=module,
            config=config,
            condition=condition,
            pass_previous_output=pass_previous_output,
        )
        self._stages.append(stage)
        return self

    def pipe(
        self,
        stage_name: str,
        module: Union[BaseLearner, BaseLearningOptimizer, Callable[..., Any]],
        **kwargs: Any,
    ) -> LearningPipeline:
        """Convenience alias for fluent add_stage chaining."""
        return self.add_stage(stage_name, module, **kwargs)

    def execute(self, initial_data: Any = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute all configured pipeline stages in sequence.
        
        Args:
            initial_data: Initial dataset, model, or parameters.
            
        Returns:
            Dict[str, Any]: Consolidated execution summary and outputs.
        """
        total_start = time.time()
        self._execution_history.clear()
        context: Dict[str, Any] = {"initial_data": initial_data, "stage_results": {}}
        current_data = initial_data

        logger.info("🚀 Starting Learning Pipeline: '%s' (%d stages)", self.config.pipeline_name, len(self._stages))

        for idx, stage in enumerate(self._stages):
            if not stage.can_run(context):
                logger.info("⏭️ Skipping Stage '%s' (condition not met)", stage.name)
                res = PipelineStageResult(
                    stage_name=stage.name,
                    strategy_type=type(stage.module).__name__,
                    status="SKIPPED",
                    duration_seconds=0.0,
                )
                self._execution_history.append(res)
                context["stage_results"][stage.name] = res
                continue

            stage_input = current_data if stage.pass_previous_output else initial_data
            result = stage.execute(stage_input, context)
            self._execution_history.append(result)
            context["stage_results"][stage.name] = result

            if result.status == "SUCCESS":
                if stage.pass_previous_output and result.output_data is not None:
                    current_data = result.output_data
            else:
                if self.config.stop_on_stage_failure:
                    total_duration = time.time() - total_start
                    raise PipelineExecutionError(
                        f"Pipeline '{self.config.pipeline_name}' aborted at stage '{stage.name}': "
                        f"{result.error_message}",
                        details={"history": self._execution_history, "duration": total_duration},
                    )

        total_duration = time.time() - total_start
        logger.info("🏁 Learning Pipeline '%s' finished in %.3fs", self.config.pipeline_name, total_duration)

        return {
            "pipeline_name": self.config.pipeline_name,
            "total_duration_seconds": total_duration,
            "stages_executed": len(self._execution_history),
            "success": all(r.status in ("SUCCESS", "SKIPPED") for r in self._execution_history),
            "final_output": current_data,
            "stage_results": {r.stage_name: r for r in self._execution_history},
        }

    @property
    def history(self) -> List[PipelineStageResult]:
        """Retrieve execution history of the last pipeline run."""
        return list(self._execution_history)


class LearningPipelineBuilder:
    """Builder pattern for constructing complex LearningPipelines with configuration."""

    def __init__(self, name: str = "custom_pipeline") -> None:
        self.config = PipelineConfig(pipeline_name=name)
        self.pipeline = LearningPipeline(config=self.config)

    def with_config(self, config: PipelineConfig) -> LearningPipelineBuilder:
        self.config = config
        self.pipeline.config = config
        return self

    def add_stage(
        self,
        name: str,
        module: Any,
        config: Optional[Any] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> LearningPipelineBuilder:
        self.pipeline.add_stage(name, module, config=config, condition=condition)
        return self

    def add_callback(self, callback: BaseCallback) -> LearningPipelineBuilder:
        self.pipeline.callbacks.append(callback)
        return self

    def build(self) -> LearningPipeline:
        return self.pipeline


def create_pipeline_builder(name: str = "custom_pipeline") -> LearningPipelineBuilder:
    return LearningPipelineBuilder(name=name)


def create_learning_pipeline(
    stages: Optional[List[Tuple[str, Any]]] = None,
    config: Optional[PipelineConfig] = None,
) -> LearningPipeline:
    pipeline = LearningPipeline(config=config)
    if stages:
        for name, module in stages:
            pipeline.add_stage(name, module)
    return pipeline


CompositeLearningPipeline = LearningPipeline

__all__ = [
    'LearningPipeline',
    'CompositeLearningPipeline',
    'PipelineStage',
    'LearningPipelineBuilder',
    'create_pipeline_builder',
    'create_learning_pipeline',
]

