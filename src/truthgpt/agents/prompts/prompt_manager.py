"""
Centralized Prompt Management for TruthGPT Agents.
Decouples system instructions from agent logic for easier tuning.
"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PromptTemplate(BaseModel):
    template: str
    description: Optional[str] = None

class PromptManager:
    """Manages system prompts and dynamic instruction templates."""
    
    _instance = None
    _templates: Dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance._load_defaults()
        return cls._instance

    def _load_defaults(self):
        """Initializes default system prompts."""
        self._templates["base_agent"] = (
            "You are {name}, an autonomous agent powered by TruthGPT.\n"
            "Your role: {role}\n"
            "Current date: 2025 Standard Stack.\n"
        )
        
        self._templates["react_core"] = (
            "You operate using a ReAct (Reasoning and Action) loop.\n"
            "On EVERY turn you emit exactly ONE JSON action, choosing exactly one of:\n"
            "  • 'tool'        — call a tool (set 'tool' and 'tool_input') when you need more information or to act.\n"
            "  • 'handoff'     — transfer to another agent (set 'handoff') when it is better suited.\n"
            "  • 'final_answer'— deliver the complete result to the user when the task is done.\n"
            "'thought' is your PRIVATE reasoning; the user never sees it, so it must NEVER be the deliverable.\n"
            "When you are done, the full, self-contained answer goes in 'final_answer' — do NOT leave it empty\n"
            "and do NOT put the answer only in 'thought'. If you have enough to respond, answer NOW rather than\n"
            "looping. Always maintain a high standard of reasoning."
        )

        self._templates["json_output"] = (
            "IMPORTANTE: Debes responder ÚNICA y EXCLUSIVAMENTE con un JSON puro que cumpla estrictamente este esquema:\n"
            "{schema}\n"
            "REGLAS OBLIGATORIAS:\n"
            "1. Incluye EXACTAMENTE uno de estos campos con contenido: 'tool', 'handoff' o 'final_answer'.\n"
            "2. Si NO vas a llamar a una herramienta ni delegar, 'final_answer' DEBE contener la respuesta\n"
            "   completa y NO puede estar vacío ni ser un placeholder.\n"
            "3. NUNCA dejes 'final_answer' vacío poniendo el contenido solo en 'thought'.\n"
            "4. 'thought' es razonamiento interno breve; el entregable real va en 'final_answer'.\n"
            "No incluyas NADA de texto fuera del JSON."
        )

    def get_prompt(self, key: str, **kwargs) -> str:
        """Retrieves a prompt and injects variables."""
        template = self._templates.get(key, "")
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing key for prompt template '{key}': {e}")
            return template

    def register_template(self, key: str, template: str):
        """Adds or updates a prompt template."""
        self._templates[key] = template

# Global singleton
prompt_manager = PromptManager()

