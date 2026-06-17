from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class ServiceConfig:
    enabled: bool = True
    timeout: float = 30.0
    auto_restart: bool = True
    max_restarts: int = 3
    dependencies: List[str] = field(default_factory=list)

@dataclass
class MonitoringConfig:
    enable_tracing: bool = False
    metrics_port: int = 9090
    health_check_interval: float = 60.0
    enable_performance_monitoring: bool = True

@dataclass
class EventBusConfig:
    max_history: int = 1000
    enable_persistence: bool = False
    event_timeout: float = 5.0

@dataclass
class CLIConfig:
    enable_auto_completion: bool = True
    history_file: str = ".truthgpt_history"
    max_history_entries: int = 1000
    prompt_style: str = "truthgpt> "

@dataclass
class PluginConfig:
    enabled: bool = True
    plugin_directory: str = "plugins"
    auto_reload: bool = False
    load_timeout: float = 10.0

@dataclass
class KernelConfig:
    # Basic settings
    log_level: LogLevel = LogLevel.INFO
    max_concurrent_tasks: int = 1000
    
    # Service management
    service_startup_timeout: float = 30.0
    health_check_interval: float = 60.0
    enable_auto_recovery: bool = True
    
    # Event system
    event_history_size: int = 1000
    event_bus: EventBusConfig = field(default_factory=EventBusConfig)
    
    # Component configurations
    services: Dict[str, ServiceConfig] = field(default_factory=dict)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    cli: CLIConfig = field(default_factory=CLIConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)
    
    # Plugin list (for backwards compatibility)
    enabled_plugins: List[str] = field(default_factory=list)
    
    # API settings
    enable_rest_api: bool = False
    api_port: int = 8000
    api_host: str = "localhost"
    
    # Security
    enable_authentication: bool = False
    api_key: Optional[str] = None
    
    def get_service_config(self, service_name: str) -> ServiceConfig:
        """Get configuration for a specific service."""
        return self.services.get(service_name, ServiceConfig())
        
    def set_service_config(self, service_name: str, config: ServiceConfig):
        """Set configuration for a specific service."""
        self.services[service_name] = config
        
    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a service is enabled."""
        return self.get_service_config(service_name).enabled
        
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            "log_level": self.log_level.value,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "service_startup_timeout": self.service_startup_timeout,
            "health_check_interval": self.health_check_interval,
            "enable_auto_recovery": self.enable_auto_recovery,
            "event_history_size": self.event_history_size,
            "services": {name: {
                "enabled": cfg.enabled,
                "timeout": cfg.timeout,
                "auto_restart": cfg.auto_restart,
                "max_restarts": cfg.max_restarts,
                "dependencies": cfg.dependencies
            } for name, cfg in self.services.items()},
            "monitoring": {
                "enable_tracing": self.monitoring.enable_tracing,
                "metrics_port": self.monitoring.metrics_port,
                "health_check_interval": self.monitoring.health_check_interval,
                "enable_performance_monitoring": self.monitoring.enable_performance_monitoring
            },
            "cli": {
                "enable_auto_completion": self.cli.enable_auto_completion,
                "history_file": self.cli.history_file,
                "max_history_entries": self.cli.max_history_entries,
                "prompt_style": self.cli.prompt_style
            },
            "plugins": {
                "enabled": self.plugins.enabled,
                "plugin_directory": self.plugins.plugin_directory,
                "auto_reload": self.plugins.auto_reload,
                "load_timeout": self.plugins.load_timeout,
                "enabled_plugins": self.enabled_plugins
            },
            "api": {
                "enable_rest_api": self.enable_rest_api,
                "api_port": self.api_port,
                "api_host": self.api_host,
                "enable_authentication": self.enable_authentication
            }
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'KernelConfig':
        """Create configuration from dictionary."""
        config = cls()
        
        # Basic settings
        if "log_level" in data:
            config.log_level = LogLevel(data["log_level"])
        if "max_concurrent_tasks" in data:
            config.max_concurrent_tasks = data["max_concurrent_tasks"]
        if "service_startup_timeout" in data:
            config.service_startup_timeout = data["service_startup_timeout"]
        if "health_check_interval" in data:
            config.health_check_interval = data["health_check_interval"]
        if "enable_auto_recovery" in data:
            config.enable_auto_recovery = data["enable_auto_recovery"]
        if "event_history_size" in data:
            config.event_history_size = data["event_history_size"]
            
        # Services
        if "services" in data:
            for name, svc_data in data["services"].items():
                config.services[name] = ServiceConfig(
                    enabled=svc_data.get("enabled", True),
                    timeout=svc_data.get("timeout", 30.0),
                    auto_restart=svc_data.get("auto_restart", True),
                    max_restarts=svc_data.get("max_restarts", 3),
                    dependencies=svc_data.get("dependencies", [])
                )
                
        # API settings
        if "api" in data:
            api_data = data["api"]
            config.enable_rest_api = api_data.get("enable_rest_api", False)
            config.api_port = api_data.get("api_port", 8000)
            config.api_host = api_data.get("api_host", "localhost")
            config.enable_authentication = api_data.get("enable_authentication", False)
            
        # Plugins
        if "plugins" in data:
            plugins_data = data["plugins"]
            if "enabled_plugins" in plugins_data:
                config.enabled_plugins = plugins_data["enabled_plugins"]
                
        return config
        
# Default configurations for common scenarios
DEVELOPMENT_CONFIG = KernelConfig(
    log_level=LogLevel.DEBUG,
    health_check_interval=30.0,
    enable_auto_recovery=True,
    event_history_size=500
)

PRODUCTION_CONFIG = KernelConfig(
    log_level=LogLevel.INFO,
    health_check_interval=60.0,
    enable_auto_recovery=True,
    event_history_size=2000,
    enable_rest_api=True
)

TESTING_CONFIG = KernelConfig(
    log_level=LogLevel.WARNING,
    health_check_interval=10.0,
    enable_auto_recovery=False,
    event_history_size=100
)
