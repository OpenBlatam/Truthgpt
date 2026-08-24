"""
TruthGPT Interface Package
==========================
Rich text user interfaces, interactive dashboard, CC spinner animations,
and CLI telemetry providers.
"""

from .core import LazyConsole, TelemetryProvider
from .tui_base import BaseTUIApp
from .interactive_dashboard import InteractiveDashboardApp
from .interactive_swarm import InteractiveSwarmApp
from .cc_style import CCSpinner

__all__ = [
    "LazyConsole",
    "TelemetryProvider",
    "BaseTUIApp",
    "InteractiveDashboardApp",
    "InteractiveSwarmApp",
    "CCSpinner",
]
