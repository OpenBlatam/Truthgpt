"""
TruthGPT Continuity Engine -- Background Persistence Service.
Responsible for resuming local tasks and managing Windows Task Scheduler integration.
"""
import asyncio
import sys
import os
import argparse
from pathlib import Path
from loguru import logger

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from modules.persistence.task_manager import get_persistence_manager
from optimization_core.agents.framework.architectures.react_agent import MultiUserReActAgent
from optimization_core.agents.framework.models import AgentConfig
from optimization_core.agents.framework.engines.engines import engine_registry

async def resume_all_tasks():
    """Resumes all active tasks in the local database."""
    pm = get_persistence_manager()
    tasks = await pm.list_active_tasks()
    
    if not tasks:
        logger.info("No active tasks found to resume.")
        return

    logger.info(f"Resuming {len(tasks)} tasks...")
    
    # Initialize engine
    llm = engine_registry.get_engine("deepseek") or engine_registry.get_engine("google")
    config = AgentConfig(llm_engine=llm, persistent=True)
    
    # We run tasks concurrently
    async def _run_task(task):
        try:
            agent = MultiUserReActAgent(config=config)
            logger.info(f"Resuming task {task.task_id} ({task.agent_name})...")
            await agent.resume_task(task.task_id)
        except Exception as e:
            logger.error(f"Failed to resume task {task.task_id}: {e}")

    await asyncio.gather(*[_run_task(t) for t in tasks])

def install_task_scheduler():
    """Installs the continuity engine as a Windows Task."""
    if os.name != 'nt':
        logger.error("Task Scheduler installation is only supported on Windows.")
        return

    task_name = "TruthGPT_Continuity_Engine"
    script_path = str(Path(__file__).resolve())
    python_path = sys.executable
    
    # Command to run on logon
    command = f'"{python_path}" "{script_path}" --resume'
    
    logger.info(f"Installing Windows Task: {task_name}")
    # schtasks /create /tn {task_name} /tr "{command}" /sc ONLOGON /rl HIGHEST /f
    os.system(f'schtasks /create /tn "{task_name}" /tr "{command}" /sc ONLOGON /rl HIGHEST /f')
    logger.success("Continuity Engine installed successfully.")

def main():
    parser = argparse.ArgumentParser(description="TruthGPT Continuity Engine")
    parser.add_Value = parser.add_argument("--resume", action="store_true", help="Resume all active tasks")
    parser.add_argument("--install", action="store_true", help="Install as Windows Startup Task")
    
    args = parser.parse_args()
    
    if args.install:
        install_task_scheduler()
    elif args.resume:
        asyncio.run(resume_all_tasks())
    else:
        # Default behavior: list status
        pm = get_persistence_manager()
        tasks = asyncio.run(pm.list_active_tasks())
        print(f"\n--- TruthGPT Active Tasks ({len(tasks)}) ---")
        for t in tasks:
            print(f"ID: {t.task_id[:8]} | Agent: {t.agent_name} | Iter: {t.iteration} | User: {t.user_id}")
        print("------------------------------------------\n")

if __name__ == "__main__":
    main()
