# dynamic_workflow.py
"""
Dynamic Workflow Engine for TruthGPT
Supports YAML-configured, personalized, logic-driven workflows.
"""

from __future__ import annotations
import yaml
import json
import logging
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import asyncio

logger = logging.getLogger(__name__)


class WorkflowStep:
    """Representa un paso individual en el flujo de trabajo."""
    def __init__(self, name: str, action: str, params: Dict[str, Any] = None,
                 condition: Optional[Callable[[Dict], bool]] = None,
                 depends: Optional[List[str]] = None,
                 on_error: str = "stop"):
        self.name = name
        self.action = action  # nombre de la función registrada
        self.params = params or {}
        self.condition = condition
        self.depends = depends or []
        self.on_error = on_error  # stop | skip | retry
        self.result = None


class DynamicWorkflow:
    """Motor de flujo de trabajo dinámico y personalizado."""
    def __init__(self, config_path: Optional[Union[str, Path]] = None,
                 user_prefs: Optional[Dict] = None):
        self.config_path = Path(config_path) if config_path else None
        self.steps: List[WorkflowStep] = []
        self.actions: Dict[str, Callable] = {}
        self.variables: Dict[str, Any] = {}  # estado compartido
        self.history: List[Dict] = []
        self.user_prefs = user_prefs or self._load_user_prefs()
        if self.config_path:
            self.load_from_yaml(self.config_path)

    def _load_user_prefs(self) -> Dict:
        try:
            prefs_path = Path(__file__).parent / "user_preferences.json"
            if prefs_path.exists():
                return json.loads(prefs_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not load user preferences: {e}")
        return {}

    def register_action(self, name: str, func: Callable):
        self.actions[name] = func

    def load_from_yaml(self, path: Path):
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        self.steps = []
        for step_data in config.get("workflow", []):
            condition = None
            if "condition" in step_data:
                # evalúa expresión simple
                expression = step_data["condition"]
                condition = lambda ctx, expr=expression: eval(expr, {"ctx": ctx, "vars": self.variables})
            step = WorkflowStep(
                name=step_data["name"],
                action=step_data["action"],
                params=step_data.get("params", {}),
                condition=condition,
                depends=step_data.get("depends", []),
                on_error=step_data.get("on_error", "stop")
            )
            self.steps.append(step)

    def personalize(self, overrides: Dict[str, Any]):
        """Aplica personalización según las preferencias del usuario."""
        for step in self.steps:
            if step.name in overrides:
                step.params.update(overrides[step.name])

    def run_step(self, step: WorkflowStep) -> Optional[Any]:
        """Ejecuta un paso, resolviendo dependencias previas."""
        # Verificar dependencias
        for dep in step.depends:
            if dep not in self.history_step_names or not self.history_step_names[dep]:
                logger.warning(f"Dependencia '{dep}' no cumplida para paso '{step.name}'")
                if step.on_error == "stop":
                    raise RuntimeError(f"Falta dependencia para '{step.name}'")
                return None

        # Verificar condición
        if step.condition and not step.condition(self.variables):
            logger.info(f"Condición no satisfecha para '{step.name}'. Saltando.")
            self.history.append({"step": step.name, "status": "skipped", "reason": "condition"})
            return None

        # Ejecutar acción
        if step.action not in self.actions:
            raise ValueError(f"Acción no registrada: {step.action}")
        try:
            result = self.actions[step.action](**step.params, ctx=self.variables)
            step.result = result
            self.history.append({"step": step.name, "status": "ok", "result": str(result)})
            return result
        except Exception as e:
            logger.error(f"Error en paso '{step.name}': {e}")
            if step.on_error == "stop":
                raise
            self.history.append({"step": step.name, "status": "error", "error": str(e)})
            return None

    async def run(self, personalization_overrides: Optional[Dict] = None) -> Dict[str, Any]:
        """Ejecuta el flujo completo secuencialmente."""
        if personalization_overrides:
            self.personalize(personalization_overrides)
        self.history = []
        for step in self.steps:
            self.run_step(step)
        return {"history": self.history, "variables": self.variables}

    @property
    def history_step_names(self):
        return {h["step"]: h.get("status") == "ok" for h in self.history}


# Acciones predefinidas útiles para TruthGPT
def action_system_check(**kwargs):
    ctx = kwargs.get("ctx", {})
    # Simula chequeo de sistema
    return "System OK"


def action_run_model_inference(**kwargs):
    prompt = kwargs.get("prompt", "")
    max_tokens = kwargs.get("max_tokens", 64)
    ctx = kwargs.get("ctx", {})
    # Placeholder: llamada real al modelo
    return f"Inference completed for prompt: {prompt[:30]}..."


def action_save_output(**kwargs):
    content = kwargs.get("content", "")
    output_path = kwargs.get("output", "output.txt")
    Path(output_path).write_text(content)
    return f"Saved to {output_path}"


# Ejemplo de uso:
if __name__ == "__main__":
    wf = DynamicWorkflow()
    wf.register_action("system_check", action_system_check)
    wf.register_action("inference", action_run_model_inference)
    wf.register_action("save", action_save_output)
    # Simulación de carga YAML
    test_config = {
        "workflow": [
            {"name": "CheckSystem", "action": "system_check"},
            {"name": "AskModel", "action": "inference", "params": {"prompt": "Resume TruthGPT"}},
            {"name": "WriteResult", "action": "save", "params": {"output": "result.txt"}, "depends": ["AskModel"]}
        ]
    }
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_config, f)
        config_path = f.name
    wf.config_path = Path(config_path)
    wf.load_from_yaml(wf.config_path)
    asyncio.run(wf.run())
    print(wf.history)
