"""
Marketing AI Engine Package v5.0 Enterprise-SOTA
==================================================
Full-funnel, multi-channel, persona-driven marketing system.
Provides AI copywriting, causal attribution, consumer fatigue modeling,
omnichannel campaign generation, post-publication analytics, and SOTA video clipping.
"""

from __future__ import annotations

from .knowledge import (
    CIALDINI_PRINCIPLES,
    PERSONAS,
    CHANNEL_SPECS,
    FUNNEL_STAGES,
    get_persona,
    get_channel_spec,
    get_cialdini_principle,
    get_funnel_stage,
)
from .models import ConsumerFatigueModel, CausalForestAttributor, MarketingModelError
from .generators import ContentGenerators
from .publisher import ProductionPublisher, PublisherError
from .connectors import (
    AdPlatformManager,
    BaseAdConnector,
    MetaAdsConnector,
    GoogleAdsConnector,
    TikTokAdsConnector,
    LinkedInAdsConnector,
    ConnectorError,
    AdPlatformError,
)
from .agents import (
    PersuasionCopywriterAgent,
    CausalForestAnalystAgent,
    BudgetOptimizerAgent,
    MarketingAgentError,
)
from .engine import IntegratedMarketingAITerminal, MarketingEngineError
from .opus_clipper import OpusClipAIEngine, OpusEngineError
from .broll_sfx import AIBRollSoundEngine, RealSoundSynthesizer, SynthesisError
from .social_monitor import SocialMediaPostMonitorEngine
from .thumbnail_generator import ViralThumbnailGenerator, ThumbnailGenerationError

__all__ = [
    # Knowledge
    "CIALDINI_PRINCIPLES",
    "PERSONAS",
    "CHANNEL_SPECS",
    "FUNNEL_STAGES",
    "get_persona",
    "get_channel_spec",
    "get_cialdini_principle",
    "get_funnel_stage",
    # Models & Exceptions
    "ConsumerFatigueModel",
    "CausalForestAttributor",
    "MarketingModelError",
    # Content & Publishing
    "ContentGenerators",
    "ProductionPublisher",
    "PublisherError",
    # Connectors & Exceptions
    "AdPlatformManager",
    "BaseAdConnector",
    "MetaAdsConnector",
    "GoogleAdsConnector",
    "TikTokAdsConnector",
    "LinkedInAdsConnector",
    "ConnectorError",
    "AdPlatformError",
    # Domain Agents & Exceptions
    "PersuasionCopywriterAgent",
    "CausalForestAnalystAgent",
    "BudgetOptimizerAgent",
    "MarketingAgentError",
    # Engines & Exception Classes
    "IntegratedMarketingAITerminal",
    "MarketingEngineError",
    "OpusClipAIEngine",
    "OpusEngineError",
    "AIBRollSoundEngine",
    "RealSoundSynthesizer",
    "SynthesisError",
    "SocialMediaPostMonitorEngine",
    "ViralThumbnailGenerator",
    "ThumbnailGenerationError",
]
