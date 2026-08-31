"""
Swarm Intelligence & Multi-Agent Consensus Subsystem for TruthGPT Interface.
=============================================================================

This package provides decomposed handlers, consensus fusion, interactive inspection,
background missions, and code execution sandboxing for TruthGPT Swarm agents.
"""
from __future__ import annotations

import sys

# Module aliasing for enterprise imports
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.interface.swarm":
        sys.modules["interface.swarm"] = _mod
    elif __name__ == "interface.swarm":
        sys.modules["optimization_core.interface.swarm"] = _mod

# 1. Handlers
from .handlers import (
    handle_agent_composer,
    handle_expert_matrix,
    handle_math_verification,
    handle_mcp_connect,
    handle_persona_tuning,
    handle_swarm_ask,
    handle_swarm_telemetry,
)

# 2. Missions
from .missions import (
    BackgroundMission,
    handle_background_missions,
    handle_continuous_mission,
    wait_with_interrupt,
)

# 3. Fusion & Dispatch
from .fusion import (
    execute_swarm_dispatch,
    extract_filename_from_code,
    handle_swarm_fusion,
    run_google_simulation,
    run_mcp_simulation,
    save_code_blocks_to_directory,
)

# 4. Inspector & Sandbox
from .inspector import (
    execute_sandbox_code,
    inspect_single_phase,
    optimize_sandbox_code,
    safe_panel,
    swarm_phase_inspector,
    view_and_edit_code,
)

__all__ = [
    # Handlers
    "handle_agent_composer",
    "handle_expert_matrix",
    "handle_math_verification",
    "handle_mcp_connect",
    "handle_persona_tuning",
    "handle_swarm_ask",
    "handle_swarm_telemetry",
    # Missions
    "BackgroundMission",
    "handle_background_missions",
    "handle_continuous_mission",
    "wait_with_interrupt",
    # Fusion
    "execute_swarm_dispatch",
    "extract_filename_from_code",
    "handle_swarm_fusion",
    "run_google_simulation",
    "run_mcp_simulation",
    "save_code_blocks_to_directory",
    # Inspector
    "execute_sandbox_code",
    "inspect_single_phase",
    "optimize_sandbox_code",
    "safe_panel",
    "swarm_phase_inspector",
    "view_and_edit_code",
]
