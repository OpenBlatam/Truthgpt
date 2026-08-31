"""
Interactive Swarm — Swarm Intelligence Hub TUI compatibility layer.
"""
from __future__ import annotations

from typing import Any, List, Optional

from interface.swarm_menu import SwarmMenuApp


class InteractiveSwarmApp(SwarmMenuApp):
    """Compatibility subclass pointing to SwarmMenuApp."""
    pass


async def get_interactive_choice(active_agents: Optional[List[Any]] = None) -> Optional[str]:
    """Runner convenience function for InteractiveSwarmApp."""
    app = InteractiveSwarmApp(active_agents)
    return await app.run()
