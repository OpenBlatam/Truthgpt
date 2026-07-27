from typing import Protocol, AsyncGenerator, Any, List, Optional, Dict, Union
from abc import abstractmethod

class AsyncInferenceEngine(Protocol):
    """
    Protocol defining the strict contract for any Inference Engine implementation.
    This guarantees static analysis compliance and strict separation of concerns.
    """
    
    @abstractmethod
    async def generate_stream(
        self, 
        prompt: Union[str, List[str]], 
        max_tokens: int = 128,
        temperature: float = 0.8,
        top_p: float = 0.95,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously generates a token stream.
        """
        ...
        
    @abstractmethod
    async def generate_batch(
        self,
        prompts: List[str],
        max_tokens: int = 128,
        temperature: float = 0.8,
        top_p: float = 0.95,
        **kwargs: Any
    ) -> List[str]:
        """
        Asynchronously generates a batch of responses.
        """
        ...

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Retrieves telemetry and configuration stats for the engine.
        """
        ...
