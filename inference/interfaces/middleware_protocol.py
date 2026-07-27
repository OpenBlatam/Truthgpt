from typing import Protocol, Any, Callable, Awaitable
from abc import abstractmethod

# Define a generic Handler type
NextHandler = Callable[..., Awaitable[Any]]

class MiddlewareProtocol(Protocol):
    """
    Protocol for pipeline interceptors. Follows the Chain of Responsibility pattern.
    """

    @abstractmethod
    async def process(self, request_payload: Any, next_handler: NextHandler) -> Any:
        """
        Intercepts the request, potentially modifying it, returning a cached response,
        or passing it to the next handler in the pipeline.
        
        Args:
            request_payload: The data being passed through the pipeline.
            next_handler: The next callable in the chain.
            
        Returns:
            The processed response.
        """
        ...
