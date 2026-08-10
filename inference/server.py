import os
from typing import Optional

from fastapi import FastAPI, Header, HTTPException

try:
    from ..configs.loader import load_config
except (ImportError, ValueError):
    try:
        from optimization_core.configs.loader import load_config
    except ImportError:
        from configs.loader import load_config

from .api.app import create_app
from .api.dependencies import state
from .core.engine_factory import create_inference_engine, EngineType

API_TOKEN = os.environ.get("TRUTHGPT_API_TOKEN", "changeme")
CONFIG_PATH = os.environ.get(
    "TRUTHGPT_CONFIG",
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "configs",
        "llm_default.yaml",
    ),
)


def _load_model():
    cfg = load_config(CONFIG_PATH, overrides=None)
    model_id = getattr(cfg.model, "path", None) or getattr(cfg.model, "family", "default")
    return create_inference_engine(model=model_id, engine_type=EngineType.AUTO)


app = create_app()


@app.get("/generate")
def generate(q: str, max_new_tokens: int = 64, temperature: float = 0.8, authorization: Optional[str] = Header(None)):
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")
    if state.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    result = state.model.generate(q, max_new_tokens=max_new_tokens, temperature=temperature)
    out = result.text if hasattr(result, "text") else result
    return {"text": out}





