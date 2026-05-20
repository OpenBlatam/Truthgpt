"""
Feed-Forward module for TruthGPT Optimization Core
Contains feed-forward network implementations with various activation functions
"""

from .feed_forward import (
    FeedForward,
    GatedFeedForward,
    SwiGLU,
    create_feed_forward
)

from .mlp import (
    MLP,
    GatedMLP,
    create_mlp
)

from .mixture_of_experts import (
    MixtureOfExperts,
    create_mixture_of_experts
)

from .pimoe_router import (
    PiMoESystem,
    TokenLevelRouter,
    PiMoEExpert,
    ExpertType,
    RoutingDecision,
    create_pimoe_system
)

from .enhanced_pimoe_integration import (
    EnhancedPiMoEIntegration,
    AdaptivePiMoE,
    OptimizationMetrics,
    create_enhanced_pimoe_integration
)

# Core feed forward components
from .pimoe_demo import (
    PiMoEDemo,
    DemoConfig,
    run_pimoe_demo
)

# Organized demos
from .demos import (
    create_demo,
    list_available_demos,
    get_demo_info,
    DEMO_REGISTRY,
    # Re-export all demos
    AdvancedPiMoEDemo,
    run_advanced_pimoe_demo,
    EnhancedAIDemo,
    run_enhanced_ai_demo,
    ModularDemo,
    run_modular_demo,
    RefactoredSystemDemo,
    run_refactored_demo,
    ProductionDemo,
    run_production_demo,
    UltraOptimizationDemo,
    run_ultra_optimization_demo,
    NextGenAIDemo,
    run_next_gen_ai_demo,
    HyperSpeedDemo,
    run_hyper_speed_demo,
    TruthGPTPiMoEIntegration,
    PiMoEIntegrationExample,
    run_pimoe_integration_example,
)

# Organized production systems
from .production import (
    create_production_system,
    list_available_production_systems,
    get_production_system_info,
    PRODUCTION_SYSTEM_REGISTRY,
    # Re-export all production systems
    ProductionPiMoESystem,
    ProductionConfig,
    ProductionMode,
    ProductionLogger,
    ProductionMonitor,
    ProductionErrorHandler,
    ProductionRequestQueue,
    create_production_pimoe_system,
    ProductionAPIServer,
    PiMoERequest,
    PiMoEResponse,
    HealthResponse,
    MetricsResponse,
    WebSocketMessage,
    create_production_api_server,
    run_production_api_demo,
    ProductionDeployment,
    DeploymentEnvironment,
    ScalingStrategy,
    DockerConfig,
    KubernetesConfig,
    MonitoringConfig,
    LoadBalancerConfig,
    create_production_deployment,
    run_production_deployment_demo,
    RefactoredProductionPiMoESystem,
    create_refactored_production_system,
    run_refactored_production_demo,
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

from .advanced_pimoe_routing import (
    AdvancedPiMoESystem,
    RoutingStrategy,
    AdvancedRoutingConfig,
    AttentionBasedRouter,
    HierarchicalRouter,
    DynamicExpertScaler,
    CrossExpertCommunicator,
    NeuralArchitectureSearchRouter,
    create_advanced_pimoe_system
)

from .pimoe_performance_optimizer import (
    PiMoEPerformanceOptimizer,
    PerformanceConfig,
    OptimizationLevel,
    MemoryOptimizer,
    ComputationalOptimizer,
    ParallelProcessor,
    CacheManager,
    HardwareOptimizer,
    create_performance_optimizer
)


from .production_pimoe_system import (
    ProductionPiMoESystem,
    ProductionConfig,
    ProductionMode,
    ProductionLogger,
    ProductionMonitor,
    ProductionErrorHandler,
    ProductionRequestQueue,
    create_production_pimoe_system,
    run_production_demo
)

from .production_deployment import (
    ProductionDeployment,
    DeploymentEnvironment,
    ScalingStrategy,
    DockerConfig,
    KubernetesConfig,
    MonitoringConfig,
    LoadBalancerConfig,
    create_production_deployment,
    run_production_deployment_demo
)

from .production_api_server import (
    ProductionAPIServer,
    PiMoERequest,
    PiMoEResponse,
    HealthResponse,
    MetricsResponse,
    WebSocketMessage,
    create_production_api_server,
    run_production_api_demo
)

from .refactored_pimoe_base import (
    ProductionMode, LogLevel, SystemConfig, ProductionConfig,
    LoggerProtocol, MonitorProtocol, ErrorHandlerProtocol, RequestQueueProtocol,
    PiMoEProcessorProtocol, BaseService, BaseConfig, ServiceFactory,
    DIContainer, EventBus, ResourceManager, MetricsCollector, HealthChecker,
    BasePiMoESystem, create_service_factory, create_di_container,
    create_event_bus, create_resource_manager, create_metrics_collector,
    create_health_checker
)

from .refactored_production_system import (
    RefactoredProductionPiMoESystem, create_refactored_production_system,
    run_refactored_production_demo
)

from .refactored_config_manager import (
    ConfigurationManager, ConfigurationFactory, ConfigTemplates,
    ConfigValidators, EnvironmentConfigBuilder, ConfigSource,
    ConfigFormat, ConfigValidationRule, ConfigSourceInfo,
    create_configuration_demo
)

from .refactored_demo import (
    RefactoredSystemDemo, run_refactored_demo
)

__all__ = [
    # Feed-Forward Networks
    'FeedForward',
    'GatedFeedForward',
    'SwiGLU',
    'create_feed_forward',
    
    # MLP Networks
    'MLP',
    'GatedMLP',
    'create_mlp',
    
    # Mixture of Experts
    'MixtureOfExperts',
    'create_mixture_of_experts',
    
    # PiMoE Token-Level Routing
    'PiMoESystem',
    'TokenLevelRouter',
    'PiMoEExpert',
    'ExpertType',
    'RoutingDecision',
    'create_pimoe_system',
    
    # Enhanced PiMoE Integration
    'EnhancedPiMoEIntegration',
    'AdaptivePiMoE',
    'PerformanceTracker',
    'OptimizationMetrics',
    'create_enhanced_pimoe_integration',
    
    # Advanced PiMoE Routing
    'AdvancedPiMoESystem',
    'RoutingStrategy',
    'AdvancedRoutingConfig',
    'AttentionBasedRouter',
    'HierarchicalRouter',
    'DynamicExpertScaler',
    'CrossExpertCommunicator',
    'NeuralArchitectureSearchRouter',
    'create_advanced_pimoe_system',
    
    # Performance Optimization
    'PiMoEPerformanceOptimizer',
    'PerformanceConfig',
    'OptimizationLevel',
    'MemoryOptimizer',
    'ComputationalOptimizer',
    'ParallelProcessor',
    'CacheManager',
    'HardwareOptimizer',
    'create_performance_optimizer',
    
    
    # Production PiMoE System
    'ProductionPiMoESystem',
    'ProductionConfig',
    'ProductionMode',
    'ProductionLogger',
    'ProductionMonitor',
    'ProductionErrorHandler',
    'ProductionRequestQueue',
    'create_production_pimoe_system',
    'run_production_demo',
    
    # Production Deployment
    'ProductionDeployment',
    'DeploymentEnvironment',
    'ScalingStrategy',
    'DockerConfig',
    'KubernetesConfig',
    'MonitoringConfig',
    'LoadBalancerConfig',
    'create_production_deployment',
    'run_production_deployment_demo',
    
    # Production API Server
    'ProductionAPIServer',
    'PiMoERequest',
    'PiMoEResponse',
    'HealthResponse',
    'MetricsResponse',
    'WebSocketMessage',
    'create_production_api_server',
    'run_production_api_demo',
    
    # Refactored Base Components
    'ProductionMode',
    'LogLevel',
    'SystemConfig',
    'ProductionConfig',
    'LoggerProtocol',
    'MonitorProtocol',
    'ErrorHandlerProtocol',
    'RequestQueueProtocol',
    'PiMoEProcessorProtocol',
    'BaseService',
    'BaseConfig',
    'ServiceFactory',
    'DIContainer',
    'EventBus',
    'ResourceManager',
    'MetricsCollector',
    'HealthChecker',
    'BasePiMoESystem',
    'create_service_factory',
    'create_di_container',
    'create_event_bus',
    'create_resource_manager',
    'create_metrics_collector',
    'create_health_checker',
    
    # Refactored Production System
    'RefactoredProductionPiMoESystem',
    'create_refactored_production_system',
    'run_refactored_production_demo',
    
    # Refactored Configuration Management
    'ConfigurationManager',
    'ConfigurationFactory',
    'ConfigTemplates',
    'ConfigValidators',
    'EnvironmentConfigBuilder',
    'ConfigSource',
    'ConfigFormat',
    'ConfigValidationRule',
    'ConfigSourceInfo',
    'create_configuration_demo',
    
    # Refactored Demo
    'RefactoredSystemDemo',
    'run_refactored_demo',
    
    # PiMoE Demo
    'PiMoEDemo',
    'DemoConfig',
    'run_pimoe_demo',
    
    # Organized Demos
    'create_demo',
    'list_available_demos',
    'get_demo_info',
    'DEMO_REGISTRY',
    'AdvancedPiMoEDemo',
    'run_advanced_pimoe_demo',
    'EnhancedAIDemo',
    'run_enhanced_ai_demo',
    'ModularDemo',
    'run_modular_demo',
    'RefactoredSystemDemo',
    'run_refactored_demo',
    'ProductionDemo',
    'run_production_demo',
    'UltraOptimizationDemo',
    'run_ultra_optimization_demo',
    'NextGenAIDemo',
    'run_next_gen_ai_demo',
    'HyperSpeedDemo',
    'run_hyper_speed_demo',
    'TruthGPTPiMoEIntegration',
    'PiMoEIntegrationExample',
    'run_pimoe_integration_example',
    
    # Organized Production Systems
    'create_production_system',
    'list_available_production_systems',
    'get_production_system_info',
    'PRODUCTION_SYSTEM_REGISTRY',
]
