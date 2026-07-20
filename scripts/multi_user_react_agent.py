# multi_user_react_agent.py - Basic Multi-User ReAct Agent for TruthGPT
# Place within: optimization_core

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

class MultiUserReActAgent:
    def __init__(self):
        self.users = {}  # user_id -> session state
        
    async def handle_user_message(self, user_id: str, message: str) -> str:
        """Process a message from a specific user using ReAct loop."""
        if user_id not in self.users:
            self.users[user_id] = {
                "history": [],
                "context": {}
            }
        session = self.users[user_id]
        session["history"].append(("user", message))
        
        # Simple ReAct reasoning
        thought = f"User {user_id} says: {message}. I will respond helpfully."
        action = "generate_answer"
        observation = f"Thinking: {thought}"
        
        # Generate answer based on context
        answer = f"[{user_id}] Received your message at {datetime.now().strftime('%H:%M:%S')}. Echo: {message}"
        session["history"].append(("assistant", answer))
        return answer
        
    async def run_cli(self):
        """Interactive multi-user CLI."""
        print("Multi-User ReAct Agent started.")
        print("Type 'exit' to quit.")
        print("Format: <user_id> <message>")
        while True:
            try:
                user_input = input(">>> ").strip()
                if user_input.lower() == "exit":
                    break
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: <user_id> Your message")
                    continue
                user_id, msg = parts
                response = await self.handle_user_message(user_id, msg)
                print(response)
            except KeyboardInterrupt:
                break
        print("Agent shutting down.")

if __name__ == "__main__":
    agent = MultiUserReActAgent()
    asyncio.run(agent.run_cli())
