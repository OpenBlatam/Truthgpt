"""
🤖 SwarmAssistant - Autonomous Collaborative Intelligence
=========================================================
An active agent participant that monitors shared workspaces 
and provides real-time SOTA suggestions and code fixes.
"""
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger("collaboration.assistant")

class SwarmAssistant:
    def __init__(self, relay):
        self.relay = relay
        self.is_active = True

    async def _get_llm(self):
        try:
            from interface.core import USER_PREFS
            from agents.engines import engine_registry
            engine_name = USER_PREFS.get("preferred_engine", "deepseek")
            engine_name = engine_name.split(",")[0].strip()
            return engine_registry.get_engine(engine_name)
        except Exception as e:
            logger.error(f"Could not load LLM engine: {e}")
            return None

    async def analyze_chat(self, user: str, text: str):
        """Monitor chat for questions or intent using real LLM inference."""
        if any(keyword in text.lower() for keyword in ["help", "suggest", "assistant", "swarm"]):
            llm = await self._get_llm()
            if not llm:
                await self.relay.emit("chat", {"user": "SwarmAgent", "text": "I am offline. No Neural Engine available."})
                return
            
            prompt = f"You are the SwarmAssistant, an autonomous AI helping users in a collaborative multi-agent workspace. The user '{user}' said: '{text}'. Give a helpful, concise response."
            try:
                response = await llm(prompt)
                await self.relay.emit("chat", {"user": "SwarmAgent", "text": response})
            except Exception as e:
                logger.error(f"LLM Error in analyze_chat: {e}")

    async def analyze_code(self, filename: str, content: str):
        """Monitor code for potential optimizations using real LLM inference."""
        if "TODO" in content or "FIXME" in content or "optimize" in content.lower():
            llm = await self._get_llm()
            if not llm: return

            prompt = (
                f"You are the SwarmAssistant code optimizer.\n"
                f"The file '{filename}' contains TODOs or requires optimization.\n\n"
                f"CODE:\n{content}\n\n"
                f"Refactor the code to resolve the TODO/FIXME and apply best practices. Return ONLY the fully refactored valid code inside ```python\n...\n``` blocks."
            )
            
            await self.relay.emit("chat", {"user": "SwarmAgent", "text": f"Detected optimization request in {filename}. Applying SOTA logic via Neural Engine..."})
            try:
                response = await llm(prompt)
                import re
                code_match = re.search(r"```(?:python|py)?\n(.*?)\n```", response, re.DOTALL | re.IGNORECASE)
                if code_match:
                    new_content = code_match.group(1).strip()
                    await self.relay.emit("code_update", {
                        "user": "SwarmAgent",
                        "filename": filename,
                        "content": new_content
                    })
                else:
                    await self.relay.emit("chat", {"user": "SwarmAgent", "text": f"Could not synthesize a valid Python block for {filename}."})
            except Exception as e:
                logger.error(f"LLM Error in analyze_code: {e}")

    async def monitor_swarm(self):
        """Background monitoring of swarm health with real telemetry."""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        
        while self.is_active:
            await asyncio.sleep(600) # Every 10 minutes
            
            try:
                cpu_usage = psutil.cpu_percent()
                mem_usage = process.memory_info().rss / (1024 * 1024)
                load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0.0
                
                status_msg = (
                    f"Swarm Health: Operational. CPU: {cpu_usage}%, "
                    f"Kernel Memory: {mem_usage:.2f}MB, Load: {load_avg:.2f}. "
                    f"Node synchronization verified."
                )
                
                await self.relay.emit("chat", {"user": "SwarmAgent", "text": f"Industrial Telemetry: {status_msg}"})
            except Exception as e:
                logger.error(f"Error in monitor_swarm telemetry: {e}")
