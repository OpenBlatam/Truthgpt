"""
Feed Forward Production Systems
================================
Unified exports for all production feed forward systems.
"""

# Import production systems
from ..production_pimoe_system import (
    ProductionPiMoESystem,
    ProductionConfig,
    ProductionMode,
    ProductionLogger,
    ProductionMonitor,
    ProductionErrorHandler,
    ProductionRequestQueue,
    create_production_pimoe_system,
    run_production_demo,
)

from ..production_api_server import (
    ProductionAPIServer,
    PiMoERequest,
    PiMoEResponse,
    HealthResponse,
    MetricsResponse,
    WebSocketMessage,
    create_production_api_server,
    run_production_api_demo,
)

from ..production_deployment import (
    ProductionDeployment,
    DeploymentEnvironment,
    ScalingStrategy,
    DockerConfig,
    KubernetesConfig,
    MonitoringConfig,
    LoadBalancerConfig,
    create_production_deployment,
    run_production_deployment_demo,
)

from ..refactored_production_system import (
    RefactoredProductionPiMoESystem,
    create_refactored_production_system,
    run_refactored_production_demo,
)

from ..refactored_config_manager import (
    ConfigurationManager,
    ConfigurationFactory,
    ConfigTemplates,
    ConfigValidators,
    EnvironmentConfigBuilder,
    ConfigSource,
    ConfigFormat,
    ConfigValidationRule,
    ConfigSourceInfo,
    create_configuration_demo,
)


# Unified production system factory
def create_production_system(
    system_type: str = "pimoe",
    config: dict = None
):
    """
    Unified factory function to create production systems.
    
    Args:
        system_type: Type of production system to create. Options:
            - "pimoe" - ProductionPiMoESystem
            - "api_server" - ProductionAPIServer
            - "deployment" - ProductionDeployment
            - "refactored" - RefactoredProductionPiMoESystem
        config: Optional configuration dictionary
    
    Returns:
        The requested production system instance
    """
    if config is None:
        config = {}
    
    system_type = system_type.lower()
    
    factory_map = {
        "pimoe": create_production_pimoe_system,
        "api_server": create_production_api_server,
        "deployment": create_production_deployment,
        "refactored": create_refactored_production_system,
    }
    
    if system_type not in factory_map:
        available = ", ".join(factory_map.keys())
        raise ValueError(
            f"Unknown production system type: '{system_type}'. "
            f"Available types: {available}"
        )
    
    factory = factory_map[system_type]
    return factory(config)


# Registry of all available production systems
PRODUCTION_SYSTEM_REGISTRY = {
    "pimoe": {
        "class": ProductionPiMoESystem,
        "module": "modules.feed_forward.production_pimoe_system",
        "description": "Production PiMoE system",
    },
    "api_server": {
        "class": ProductionAPIServer,
        "module": "modules.feed_forward.production_api_server",
        "description": "Production API server",
    },
    "deployment": {
        "class": ProductionDeployment,
        "module": "modules.feed_forward.production_deployment",
        "description": "Production deployment system",
    },
    "refactored": {
        "class": RefactoredProductionPiMoESystem,
        "module": "modules.feed_forward.refactored_production_system",
        "description": "Refactored production system",
    },
}


def list_available_production_systems() -> list:
    """List all available production system types."""
    return list(PRODUCTION_SYSTEM_REGISTRY.keys())


def get_production_system_info(system_type: str) -> dict:
    """
    Get information about a specific production system.
    
    Args:
        system_type: Type of production system
    
    Returns:
        Dictionary with production system information
    """
    if system_type not in PRODUCTION_SYSTEM_REGISTRY:
        raise ValueError(f"Unknown production system type: {system_type}")
    
    registry_entry = PRODUCTION_SYSTEM_REGISTRY[system_type]
    return {
        "type": system_type,
        "class": registry_entry["class"].__name__,
        "module": registry_entry["module"],
        "description": registry_entry["description"],
    }


__all__ = [
    # Production PiMoE System
    "ProductionPiMoESystem",
    "ProductionConfig",
    "ProductionMode",
    "ProductionLogger",
    "ProductionMonitor",
    "ProductionErrorHandler",
    "ProductionRequestQueue",
    "create_production_pimoe_system",
    "run_production_demo",
    # Production API Server
    "ProductionAPIServer",
    "PiMoERequest",
    "PiMoEResponse",
    "HealthResponse",
    "MetricsResponse",
    "WebSocketMessage",
    "create_production_api_server",
    "run_production_api_demo",
    # Production Deployment
    "ProductionDeployment",
    "DeploymentEnvironment",
    "ScalingStrategy",
    "DockerConfig",
    "KubernetesConfig",
    "MonitoringConfig",
    "LoadBalancerConfig",
    "create_production_deployment",
    "run_production_deployment_demo",
    # Refactored Production System
    "RefactoredProductionPiMoESystem",
    "create_refactored_production_system",
    "run_refactored_production_demo",
    # Configuration Management
    "ConfigurationManager",
    "ConfigurationFactory",
    "ConfigTemplates",
    "ConfigValidators",
    "EnvironmentConfigBuilder",
    "ConfigSource",
    "ConfigFormat",
    "ConfigValidationRule",
    "ConfigSourceInfo",
    "create_configuration_demo",
    # Unified factory
    "create_production_system",
    # Registry
    "PRODUCTION_SYSTEM_REGISTRY",
    "list_available_production_systems",
    "get_production_system_info",
]

