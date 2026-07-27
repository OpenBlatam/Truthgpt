"""
TruthGPT Swarm Node Server — Refactored Platinum Edition.
Industrial-grade remote agent execution server.
"""

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from loguru import logger
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.persistence.task_manager import TaskSnapshot, get_persistence_manager
from optimization_core.agents.framework.architectures.react_agent import MultiUserReActAgent
from optimization_core.agents.framework.models import AgentConfig, AgentResponse
from optimization_core.agents.framework.engines.engines import engine_registry

# Configure specialized logging for the node
logger.add("swarm_node.log", rotation="50 MB", level="DEBUG", backtrace=True, diagnose=True)

app = FastAPI(
    title="TruthGPT Swarm Node (Platinum)",
    description="Remote bridge for autonomous agent continuity",
    version="1.0.0"
)

# In-memory result cache (can be moved to Redis for production)
class ResultStore:
    def __init__(self):
        self.results = {}
    
    def set(self, task_id: str, value: dict):
        self.results[task_id] = value
    
    def get(self, task_id: str):
        return self.results.get(task_id)

store = ResultStore()

async def execute_remote_loop(snapshot: TaskSnapshot):
    """
    Background worker that resumes the agent's reasoning loop.
    """
    logger.info(f"Handoff received: {snapshot.task_id}. Starting remote execution...")
    
    try:
        # 1. Initialize High-Performance Engine
        llm = engine_registry.get_engine("deepseek") or engine_registry.get_engine("google")
        config = AgentConfig(llm_engine=llm, persistent=True)
        
        # 2. Instantiate Platinum Orchestrator
        agent = MultiUserReActAgent(config=config)
        
        # 3. Resume from snapshot state
        response = await agent.resume_task(snapshot.task_id)
        
        # 4. Finalize and Store
        content = response.content if hasattr(response, 'content') else str(response)
        store.set(snapshot.task_id, {
            "status": "completed",
            "content": content,
            "metadata": {"execution_mode": "remote_swarm"}
        })
        
        logger.success(f"Task {snapshot.task_id} successfully completed in the cloud.")
        
    except Exception as e:
        logger.exception(f"Critical failure in remote task {snapshot.task_id}")
        store.set(snapshot.task_id, {"status": "error", "error": str(e)})

@app.post("/v1/persistence/sync")
async def sync_state(snapshot: TaskSnapshot, background_tasks: BackgroundTasks):
    """
    Receives an agent's mental state and continues the task.
    """
    logger.info(f"Mental state synchronized for task {snapshot.task_id}")
    
    # Persist locally in the Node's DB
    await get_persistence_manager().save_snapshot(snapshot)
    
    # Offload to background executor
    background_tasks.add_task(execute_remote_loop, snapshot)
    
    return {"status": "accepted", "message": "State synchronized. Agent active in swarm."}

@app.get("/v1/persistence/status/{task_id}")
async def get_status(task_id: str):
    """
    Retrieves the current status or final result of a task.
    """
    result = store.get(task_id)
    if result:
        return result
    
    # Check if we have a snapshot but it's not finished
    snapshot = await get_persistence_manager().load_snapshot(task_id)
    if snapshot:
        return {"status": snapshot.status, "iteration": snapshot.iteration}
    
    raise HTTPException(status_code=404, detail="Task ID not found in swarm history.")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "engines": engine_registry.list_engines(),
        "tasks_active": len(await get_persistence_manager().list_active_tasks())
    }

if __name__ == "__main__":
    logger.info("Starting TruthGPT Swarm Node on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")
