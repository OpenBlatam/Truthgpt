# continuous_agent.py
"""
Continuous Agent using Dynamic Workflow + Claude-like Live Terminal.
Runs a personalized workflow loop with real-time Rich TUI featuring
side-by-side reasoning and workflow panels.
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Optional

from dynamic_workflow import DynamicWorkflow, action_system_check, action_run_model_inference, action_save_output
from enhanced_terminal import ClaudeLikeTUI


DEFAULT_YAML = Path(__file__).parent / "default_workflow.yaml"


async def continuous_agent_loop(workflow_config: Optional[Path] = None,
                                personalization_overrides: Optional[dict] = None):
    config_path = workflow_config or DEFAULT_YAML
    wf = DynamicWorkflow(config_path=config_path)
    
    # Register common actions
    wf.register_action("system_check", action_system_check)
    wf.register_action("inference", action_run_model_inference)
    wf.register_action("save", action_save_output)
    # More actions can be registered dynamically from plugins
    
    tui = ClaudeLikeTUI()
    with tui:
        tui.update_header("Continuous Agent · Claude‑like Terminal")
        tui.set_user_input("Personalized workflow loop active")
        tui.add_thought("Initializing dynamic workflow...")
        tui.add_workflow_log("Loading workflow configuration...")
        tui.update_metrics(model="TruthGPT", temperature=0.8)
        
        while True:  # Continuous loop
            tui.add_thought("Starting new workflow iteration")
            tui.add_workflow_log("Executing workflow steps...")
            
            start_time = time.time()
            result = await wf.run(personalization_overrides)
            elapsed = time.time() - start_time
            
            # Update metrics
            tui.update_metrics(elapsed=elapsed)
            
            # Log step results
            tui.add_workflow_log(f"Workflow completed: {len(result['history'])} steps in {elapsed:.2f}s")
            for entry in result['history']:
                status_icon = "✓" if entry['status'] == 'ok' else "✗" if entry['status'] == 'error' else "○"
                tui.add_workflow_log(f"  {status_icon} {entry['step']}: {entry['status']}")
            
            tui.add_thought("Waiting 10 seconds before next iteration...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(continuous_agent_loop())
