import hashlib
import json
import logging
from typing import Dict, Any, Tuple, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)

class SemanticLRUCache:
    """A bounded LRU cache for semantic tool responses to prevent redundant executions."""
    def __init__(self, maxsize: int = 100):
        self.cache = OrderedDict()
        self.maxsize = maxsize

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            # Move to end to show it was recently used
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: Any):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.maxsize:
            # Pop the first item (least recently used)
            self.cache.popitem(last=False)


class MemoryOptimizer:
    """
    Optimizes agent execution by caching redundant tool calls 
    and implementing semantic deduplication.
    """
    def __init__(self):
        # We use a global LRU cache for all agents in this orchestrator instance
        self._action_cache = SemanticLRUCache(maxsize=500)
        
    def _hash_action(self, tool_name: str, tool_input: str, user_id: str) -> str:
        """
        Creates a deterministic hash for a tool execution context.
        To maintain security, cache is strictly segregated by user_id.
        """
        raw_str = f"{user_id}:{tool_name}:{str(tool_input).strip()}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()
        
    def should_skip_redundant_action(self, tool_name: str, tool_input: str, user_id: str) -> Tuple[bool, Optional[Any]]:
        """
        Checks if the exact same action has been successfully run recently by this user.
        """
        # Exclude tools that intentionally mutate state or need fresh data every time
        volatile_tools = {"python_execute", "shell_execute", "store_memory"}
        if tool_name in volatile_tools:
            return False, None
            
        action_hash = self._hash_action(tool_name, tool_input, user_id)
        cached_result = self._action_cache.get(action_hash)
        
        if cached_result is not None:
            logger.info(f"MEMORY OPTIMIZER: Reused cached result for {tool_name}")
            return True, cached_result
            
        return False, None
        
    def cache_result(self, tool_name: str, tool_input: str, user_id: str, result: Any):
        """Stores the result of a tool execution in the cache."""
        volatile_tools = {"python_execute", "shell_execute", "store_memory"}
        if tool_name in volatile_tools:
            return
            
        action_hash = self._hash_action(tool_name, tool_input, user_id)
        self._action_cache.put(action_hash, result)

# Singleton instance for the orchestrator to import if needed
optimizer_instance = MemoryOptimizer()
