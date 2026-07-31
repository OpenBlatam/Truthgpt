import json
from pathlib import Path
from typing import Optional, Protocol, Union, runtime_checkable
from abc import ABC, abstractmethod

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger

from .ssl_context import httpx_verify_setting
from .models import InferenceResult
from .exceptions import InferenceError
from .engine_config import _resolve_api_key

@runtime_checkable
class AsyncLLMEngine(Protocol):
    """Protocol for any callable engine."""
    async def __call__(self, prompt: str, **kwargs) -> Union[str, InferenceResult]: ...

class DummyAsyncLLM:
    """Mock engine that returns valid AgentAction JSON for testing."""
    model_name = "dummy-fallback"
    provider_name = "dummy"
    is_ensemble = False

    async def __call__(self, prompt: str, **kwargs) -> str:
        return json.dumps({
            "thought": "No hay motor LLM real configurado.",
            "tool": None,
            "tool_input": None,
            "final_answer": "⚠️ Motor de inferencia no configurado. Configura una API key en Settings > Engines."
        })

class BaseProvider(ABC):
    """Base class for all LLM providers."""
    
    def __init__(self, model: str, api_key: Optional[str] = None, env_var: str = "",
                 force_model: bool = False):
        custom_model = model
        # When force_model is set, the caller's model wins over the stored
        # engine_models preference (used by tier selection / explicit overrides).
        try:
            prefs_path = Path(__file__).resolve().parent.parent / "user_preferences.json"
            if not force_model and prefs_path.exists():
                import json
                data = json.loads(prefs_path.read_text())
                engine_models = data.get("engine_models", {})
                
                # Map env_var to preference key name
                env_to_key = {
                    "DEEPSEEK_API_KEY": "deepseek",
                    "GOOGLE_API_KEY": "google",
                    "OPENAI_API_KEY": "chatgpt",
                    "ANTHROPIC_API_KEY": "claude",
                    "OPENROUTER_API_KEY": "openrouter",
                }
                pref_key = env_to_key.get(env_var)
                if pref_key and pref_key in engine_models:
                    custom_model = engine_models[pref_key]
        except Exception:
            pass
            
        self.model = custom_model
        self.api_key = _resolve_api_key(env_var, api_key) if env_var else api_key
        if isinstance(self.api_key, str):
            self.api_key = self.api_key.strip()
        self.timeout = 300.0

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

    async def __call__(self, prompt: str, **kwargs) -> str:
        return await self.generate(prompt, **kwargs)

    def _safe_fallback(self, thought: str, message: str, error: str = "provider_error") -> str:
        return json.dumps({
            "thought": thought,
            "tool": None,
            "tool_input": None,
            "final_answer": message,
            "metadata": {"error": error}
        })

class DeepSeekProvider(BaseProvider):
    def __init__(self, model: str = "deepseek-reasoner", api_key: Optional[str] = None,
                 force_model: bool = False):
        super().__init__(model, api_key, env_var="DEEPSEEK_API_KEY", force_model=force_model)
        self.url = "https://api.deepseek.com/chat/completions"
        model_lower = str(self.model).lower().strip()
        if model_lower in ("v4-flash", "flash", "chat", "v3", "v4", "deepseek-chat", "deepseek-v4-flash"):
            self.model = "deepseek-v4-flash"
        elif model_lower in ("v4-pro", "pro", "reasoner", "r1", "deepseek-reasoner", "deepseek-v4-pro", "1", ""):
            self.model = "deepseek-v4-pro"
        else:
            self.model = "deepseek-v4-pro"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            return self._safe_fallback("DeepSeek API Key missing.", "Configura DEEPSEEK_API_KEY.")
        
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192
        }
        if "chat" in self.model:
            data["temperature"] = 0.1
        
        async with httpx.AsyncClient(timeout=180.0, verify=httpx_verify_setting()) as client:
            resp = await client.post(self.url, headers=headers, json=data)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            
            err_msg = resp.text
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                pass
            logger.warning(f"DeepSeek API Error {resp.status_code}: {err_msg}")
            raise InferenceError(f"DeepSeek API Error {resp.status_code}: {err_msg}")

class GoogleGeminiProvider(BaseProvider):
    def __init__(self, model: str = "gemini-2.0-flash-exp", api_key: Optional[str] = None,
                 force_model: bool = False):
        super().__init__(model, api_key, env_var="GOOGLE_API_KEY", force_model=force_model)
        model_lower = str(self.model).lower().strip()
        if "pro" in model_lower:
            # Detecta cualquier variante que indique "Pro" (ej. "Gemini 3.1 Pro (High)")
            self.model = "gemini-2.0-pro-exp-02-05"
        elif "flash" in model_lower or model_lower in ("1", ""):
            self.model = "gemini-2.0-flash-exp"
        else:
            if not model_lower.startswith("gemini-"):
                self.model = "gemini-2.0-flash-exp"
            else:
                self.model = self.model.strip()
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            return self._safe_fallback("Google API Key missing.", "Google API Key missing.")
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192}
        }
        
        async with httpx.AsyncClient(timeout=self.timeout, verify=httpx_verify_setting()) as client:
            resp = await client.post(self.url, json=data)
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            
            err_msg = resp.text
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                pass
            logger.warning(f"Google API Error {resp.status_code}: {err_msg}")
            raise InferenceError(f"Google API Error {resp.status_code}: {err_msg}")

class OpenAIProvider(BaseProvider):
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None,
                 force_model: bool = False):
        super().__init__(model, api_key, env_var="OPENAI_API_KEY", force_model=force_model)
        self.url = "https://api.openai.com/v1/chat/completions"
        model_lower = str(self.model).lower().strip()
        if model_lower in ("si", "gpt4", "gpt-4", "gpt-4o", "1", ""):
            self.model = "gpt-4o"
        else:
            if not model_lower.startswith("gpt-"):
                self.model = "gpt-4o"
            else:
                self.model = self.model.strip()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            return self._safe_fallback("OpenAI API Key missing.", "Configura OPENAI_API_KEY.")
        
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 4096
        }
        
        async with httpx.AsyncClient(timeout=self.timeout, verify=httpx_verify_setting()) as client:
            resp = await client.post(self.url, headers=headers, json=data)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            
            err_msg = resp.text
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                pass
            logger.warning(f"OpenAI API Error {resp.status_code}: {err_msg}")
            raise InferenceError(f"OpenAI API Error {resp.status_code}: {err_msg}")

class OpenRouterProvider(BaseProvider):
    def __init__(self, model: str = "~anthropic/claude-sonnet-latest", api_key: Optional[str] = None,
                 force_model: bool = False):
        super().__init__(model, api_key, env_var="OPENROUTER_API_KEY", force_model=force_model)
        model_lower = str(self.model).lower().strip()
        # Map retired model IDs to current ones
        _retired_models = {
            "anthropic/claude-sonnet-latest": "~anthropic/claude-sonnet-latest",
            "anthropic/claude-3.7-sonnet": "~anthropic/claude-sonnet-latest",
            "anthropic/claude-3-7-sonnet": "~anthropic/claude-sonnet-latest",
            "anthropic/claude-3.5-sonnet": "~anthropic/claude-sonnet-latest",
            "anthropic/claude-sonnet-4-20250514": "~anthropic/claude-sonnet-latest",
            "anthropic/claude-sonnet-4-0": "~anthropic/claude-sonnet-latest",
            "anthropic/claude-3.7-sonnet:beta": "~anthropic/claude-sonnet-latest",
            "anthropic/claude-3.5-sonnet:beta": "~anthropic/claude-sonnet-latest",
        }
        if model_lower in ("1", ""):
            self.model = "~anthropic/claude-sonnet-latest"
        elif model_lower in _retired_models:
            self.model = _retired_models[model_lower]
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            return self._safe_fallback("OpenRouter API Key missing.", "Configura OPENROUTER_API_KEY.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://truthgpt.ai",
            "X-Title": "TruthGPT OS",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 4096
        }
        
        async with httpx.AsyncClient(timeout=self.timeout, verify=httpx_verify_setting()) as client:
            resp = await client.post(self.url, headers=headers, json=data)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            
            err_msg = resp.text
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                pass
            logger.warning(f"OpenRouter API Error {resp.status_code}: {err_msg}")
            raise InferenceError(f"OpenRouter API Error {resp.status_code}: {err_msg}")

class AnthropicProvider(BaseProvider):
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: Optional[str] = None,
                 force_model: bool = False):
        super().__init__(model, api_key, env_var="ANTHROPIC_API_KEY", force_model=force_model)
        self.url = "https://api.anthropic.com/v1/messages"
        model_lower = str(self.model).lower().strip()
        if model_lower in ("opus", "claude-3-opus", "claude-3-opus-20240229", "claude-opus-4-8"):
            self.model = "claude-opus-4-8"
        elif "haiku" in model_lower or model_lower in ("claude-haiku-4-5-20251001",):
            self.model = "claude-haiku-4-5-20251001"
        elif model_lower in ("sonnet", "claude-3-5-sonnet", "claude-3.5-sonnet", "claude-3-5-sonnet-latest", "claude-sonnet-4-6"):
            self.model = "claude-sonnet-4-6"
        elif model_lower in ("claude-3-7-sonnet", "claude-3.7-sonnet", "claude-3-7-sonnet-latest", "claude-sonnet-4-20250514", "claude-sonnet-4-0", "1", ""):
            self.model = "claude-sonnet-4-6"
        else:
            self.model = "claude-sonnet-4-6"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            or_key = _resolve_api_key("OPENROUTER_API_KEY")
            if or_key:
                logger.warning("Anthropic API Key missing. Trying fallback to OpenRouter.")
                try:
                    fallback_provider = OpenRouterProvider(api_key=or_key)
                    return await fallback_provider.generate(prompt, **kwargs)
                except Exception as fallback_exc:
                    logger.error(f"Fallback to OpenRouter failed: {fallback_exc}")
            return self._safe_fallback("Anthropic API Key missing.", "Configura ANTHROPIC_API_KEY.")
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=httpx_verify_setting()) as client:
                resp = await client.post(self.url, headers=headers, json=data)
                if resp.status_code == 200:
                    return resp.json()["content"][0]["text"]
                
                err_msg = resp.text
                try:
                    err_msg = resp.json().get("error", {}).get("message", resp.text)
                except Exception:
                    pass
                logger.warning(f"Anthropic API Error {resp.status_code}: {err_msg}")
                raise InferenceError(f"Anthropic API Error {resp.status_code}: {err_msg}")
        except Exception as e:
            or_key = _resolve_api_key("OPENROUTER_API_KEY")
            if or_key:
                logger.warning(f"Anthropic direct call failed: {e}. Trying fallback to OpenRouter.")
                try:
                    fallback_provider = OpenRouterProvider(api_key=or_key)
                    return await fallback_provider.generate(prompt, **kwargs)
                except Exception as fallback_exc:
                    logger.error(f"Fallback to OpenRouter failed: {fallback_exc}")
                    raise e
            else:
                raise e
