from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class AgentSettings(BaseSettings):
    """Configuración central para el Agente TruthGPT."""
    model_config = SettingsConfigDict(
        env_prefix="TRUTHGPT_",
        extra="ignore"
    )
    
    # Inferencia
    MAX_ITERATIONS: int = Field(default=30, description="Máximo de bucles ReAct por mensaje")
    MODEL_TEMPERATURE: float = 0.7
    
    # Persistencia
    DATABASE_PATH: str = "data/agent_memory.db"
    
    # Seguridad
    FORBIDDEN_BASH_COMMANDS: List[str] = ["rm", "chmod", "format", "del", "mkfs"]
    
    # Prompting
    AGENT_NAME: str = "TruthGPT"
    SYSTEM_PROMPT_TEMPLATE: str = (
        "You are {name}, an elite personal and autonomous AI assistant.\n"
        "Analyze the context and use the tools only if absolutely necessary.\n"
    )



settings = AgentSettings()

