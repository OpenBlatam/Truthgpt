"""
Refactored Configuration Management System
Advanced configuration management with validation, hot-reloading, and environment-specific configs.
"""

import os
import json
import yaml
import time
import threading
from typing import Dict, List, Optional, Any, Union, Callable, Type
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging
from contextlib import contextmanager
import hashlib

class ConfigSource(Enum):
    """Configuration source types."""
    FILE = "file"
    ENVIRONMENT = "environment"
    DATABASE = "database"
    API = "api"
    MEMORY = "memory"

class ConfigFormat(Enum):
    """Configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    INI = "ini"
    ENV = "env"

@dataclass
class ConfigValidationRule:
    """Configuration validation rule."""
    field: str
    validator: Callable[[Any], bool]
    error_message: str
    required: bool = True

@dataclass
class ConfigSourceInfo:
    """Configuration source information."""
    source: ConfigSource
    path: Optional[str] = None
    format: ConfigFormat = ConfigFormat.JSON
    priority: int = 0
    hot_reload: bool = False
    checksum: Optional[str] = None
    last_modified: Optional[float] = None

class ConfigurationManager:
    """Advanced configuration manager with validation and hot-reloading."""
    
    def __init__(self, base_config: Dict[str, Any] = None):
        self.base_config = base_config or {}
        self.config = self.base_config.copy()
        self.sources: List[ConfigSourceInfo] = []
        self.validation_rules: List[ConfigValidationRule] = []
        self.observers: List[Callable[[str, Any], None]] = []
        self.hot_reload_thread = None
        self._stop_hot_reload = False
        self._lock = threading.RLock()
        self.logger = logging.getLogger('config_manager')
        
        # Setup default validation rules
        self._setup_default_validation_rules()
    
    def _setup_default_validation_rules(self) -> None:
        """Setup default validation rules."""
        # Add common validation rules
        self.add_validation_rule(
            ConfigValidationRule(
                field="production_mode",
                validator=lambda x: x in ["development", "staging", "production", "high_performance", "cost_optimized"],
                error_message="Invalid production mode",
                required=True
            )
        )
        
        self.add_validation_rule(
            ConfigValidationRule(
                field="hidden_size",
                validator=lambda x: isinstance(x, int) and x > 0,
                error_message="Hidden size must be a positive integer",
                required=True
            )
        )
        
        self.add_validation_rule(
            ConfigValidationRule(
                field="num_experts",
                validator=lambda x: isinstance(x, int) and x > 0,
                error_message="Number of experts must be a positive integer",
                required=True
            )
        )
    
    def add_source(self, source_info: ConfigSourceInfo) -> None:
        """Add a configuration source."""
        with self._lock:
            self.sources.append(source_info)
            self.sources.sort(key=lambda x: x.priority, reverse=True)
    
    def add_validation_rule(self, rule: ConfigValidationRule) -> None:
        """Add a validation rule."""
        self.validation_rules.append(rule)
    
    def add_observer(self, observer: Callable[[str, Any], None]) -> None:
        """Add a configuration change observer."""
        self.observers.append(observer)
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from all sources."""
        with self._lock:
            # Start with base config
            self.config = self.base_config.copy()
            
            # Load from each source
            for source_info in self.sources:
                try:
                    source_config = self._load_from_source(source_info)
                    if source_config:
                        self.config.update(source_config)
                        self.logger.info(f"Loaded config from {source_info.source.value}")
                except Exception as e:
                    self.logger.error(f"Failed to load config from {source_info.source.value}: {e}")
            
            # Validate configuration
            self._validate_configuration()
            
            # Start hot reload if enabled
            self._start_hot_reload()
            
            return self.config.copy()
    
    def _load_from_source(self, source_info: ConfigSourceInfo) -> Dict[str, Any]:
        """Load configuration from a specific source."""
        if source_info.source == ConfigSource.FILE:
            return self._load_from_file(source_info)
        elif source_info.source == ConfigSource.ENVIRONMENT:
            return self._load_from_environment()
        elif source_info.source == ConfigSource.MEMORY:
            return self._load_from_memory()
        else:
            raise ValueError(f"Unsupported config source: {source_info.source}")
    
    def _load_from_file(self, source_info: ConfigSourceInfo) -> Dict[str, Any]:
        """Load configuration from file."""
        if not source_info.path or not os.path.exists(source_info.path):
            return {}
        
        # Check if file has changed
        current_checksum = self._calculate_file_checksum(source_info.path)
        if source_info.checksum == current_checksum:
            return {}
        
        # Update source info
        source_info.checksum = current_checksum
        source_info.last_modified = os.path.getmtime(source_info.path)
        
        # Load file based on format
        with open(source_info.path, 'r') as f:
            if source_info.format == ConfigFormat.JSON:
                return json.load(f)
            elif source_info.format == ConfigFormat.YAML:
                return yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported file format: {source_info.format}")
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        for key, value in os.environ.items():
            if key.startswith('PIMOE_'):
                # Remove prefix and convert to nested dict
                config_key = key[6:].lower().replace('_', '.')
                self._set_nested_value(config, config_key, value)
        return config
    
    def _load_from_memory(self) -> Dict[str, Any]:
        """Load configuration from memory."""
        return {}
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate file checksum for change detection."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested dictionary value from dot notation."""
        keys = key.split('.')
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    
    def _validate_configuration(self) -> None:
        """Validate configuration against rules."""
        for rule in self.validation_rules:
            if rule.required and rule.field not in self.config:
                raise ValueError(f"Required field '{rule.field}' not found in configuration")
            
            if rule.field in self.config:
                if not rule.validator(self.config[rule.field]):
                    raise ValueError(f"Validation failed for '{rule.field}': {rule.error_message}")
    
    def _start_hot_reload(self) -> None:
        """Start hot reload monitoring."""
        if any(source.hot_reload for source in self.sources):
            self._stop_hot_reload = False
            self.hot_reload_thread = threading.Thread(target=self._hot_reload_loop, daemon=True)
            self.hot_reload_thread.start()
    
    def _hot_reload_loop(self) -> None:
        """Hot reload monitoring loop."""
        while not self._stop_hot_reload:
            try:
                for source_info in self.sources:
                    if source_info.hot_reload and source_info.source == ConfigSource.FILE:
                        if self._check_file_changed(source_info):
                            self.logger.info(f"File {source_info.path} changed, reloading config")
                            self.load_configuration()
                            break
                
                time.sleep(1.0)  # Check every second
            except Exception as e:
                self.logger.error(f"Error in hot reload loop: {e}")
                time.sleep(5.0)
    
    def _check_file_changed(self, source_info: ConfigSourceInfo) -> bool:
        """Check if file has changed."""
        if not source_info.path or not os.path.exists(source_info.path):
            return False
        
        current_checksum = self._calculate_file_checksum(source_info.path)
        return current_checksum != source_info.checksum
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        with self._lock:
            return self._get_nested_value(self.config, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        with self._lock:
            self._set_nested_value(self.config, key, value)
            self._notify_observers(key, value)
    
    def _get_nested_value(self, config: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get nested dictionary value from dot notation."""
        keys = key.split('.')
        current = config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current
    
    def _notify_observers(self, key: str, value: Any) -> None:
        """Notify observers of configuration changes."""
        for observer in self.observers:
            try:
                observer(key, value)
            except Exception as e:
                self.logger.error(f"Error in config observer: {e}")
    
    def save_configuration(self, file_path: str, format: ConfigFormat = ConfigFormat.JSON) -> None:
        """Save current configuration to file."""
        with self._lock:
            with open(file_path, 'w') as f:
                if format == ConfigFormat.JSON:
                    json.dump(self.config, f, indent=2)
                elif format == ConfigFormat.YAML:
                    yaml.dump(self.config, f, default_flow_style=False)
                else:
                    raise ValueError(f"Unsupported save format: {format}")
    
    def stop_hot_reload(self) -> None:
        """Stop hot reload monitoring."""
        self._stop_hot_reload = True
        if self.hot_reload_thread:
            self.hot_reload_thread.join()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary."""
        return {
            'sources': [asdict(source) for source in self.sources],
            'validation_rules': len(self.validation_rules),
            'observers': len(self.observers),
            'hot_reload_enabled': any(source.hot_reload for source in self.sources),
            'config_keys': list(self.config.keys())
        }

# Environment-specific Configuration Builder
class EnvironmentConfigBuilder:
    """Builder for environment-specific configurations."""
    
    def __init__(self):
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.current_environment = None
    
    def for_environment(self, environment: str) -> 'EnvironmentConfigBuilder':
        """Set current environment."""
        self.current_environment = environment
        if environment not in self.configs:
            self.configs[environment] = {}
        return self
    
    def with_base_config(self, config: Dict[str, Any]) -> 'EnvironmentConfigBuilder':
        """Set base configuration."""
        if self.current_environment:
            self.configs[self.current_environment].update(config)
        return self
    
    def with_override(self, key: str, value: Any) -> 'EnvironmentConfigBuilder':
        """Add configuration override."""
        if self.current_environment:
            self.configs[self.current_environment][key] = value
        return self
    
    def with_file_source(self, file_path: str, priority: int = 0) -> 'EnvironmentConfigBuilder':
        """Add file source."""
        if self.current_environment:
            if 'sources' not in self.configs[self.current_environment]:
                self.configs[self.current_environment]['sources'] = []
            self.configs[self.current_environment]['sources'].append({
                'source': ConfigSource.FILE,
                'path': file_path,
                'priority': priority
            })
        return self
    
    def with_environment_source(self, priority: int = 0) -> 'EnvironmentConfigBuilder':
        """Add environment variable source."""
        if self.current_environment:
            if 'sources' not in self.configs[self.current_environment]:
                self.configs[self.current_environment]['sources'] = []
            self.configs[self.current_environment]['sources'].append({
                'source': ConfigSource.ENVIRONMENT,
                'priority': priority
            })
        return self
    
    def build(self) -> Dict[str, Dict[str, Any]]:
        """Build environment configurations."""
        return self.configs.copy()

# Configuration Factory
class ConfigurationFactory:
    """Factory for creating configuration managers."""
    
    @staticmethod
    def create_from_file(file_path: str, format: ConfigFormat = ConfigFormat.JSON) -> ConfigurationManager:
        """Create configuration manager from file."""
        manager = ConfigurationManager()
        
        source_info = ConfigSourceInfo(
            source=ConfigSource.FILE,
            path=file_path,
            format=format,
            priority=1,
            hot_reload=True
        )
        
        manager.add_source(source_info)
        manager.load_configuration()
        
        return manager
    
    @staticmethod
    def create_from_environment() -> ConfigurationManager:
        """Create configuration manager from environment variables."""
        manager = ConfigurationManager()
        
        source_info = ConfigSourceInfo(
            source=ConfigSource.ENVIRONMENT,
            priority=1
        )
        
        manager.add_source(source_info)
        manager.load_configuration()
        
        return manager
    
    @staticmethod
    def create_multi_source(sources: List[ConfigSourceInfo]) -> ConfigurationManager:
        """Create configuration manager with multiple sources."""
        manager = ConfigurationManager()
        
        for source_info in sources:
            manager.add_source(source_info)
        
        manager.load_configuration()
        return manager
    
    @staticmethod
    def create_for_environment(environment: str, configs: Dict[str, Dict[str, Any]]) -> ConfigurationManager:
        """Create configuration manager for specific environment."""
        if environment not in configs:
            raise ValueError(f"Environment '{environment}' not found in configurations")
        
        manager = ConfigurationManager(configs[environment])
        
        # Add sources if specified
        if 'sources' in configs[environment]:
            for source_config in configs[environment]['sources']:
                source_info = ConfigSourceInfo(**source_config)
                manager.add_source(source_info)
        
        manager.load_configuration()
        return manager

# Configuration Validators
class ConfigValidators:
    """Collection of common configuration validators."""
    
    @staticmethod
    def is_positive_int(value: Any) -> bool:
        """Check if value is a positive integer."""
        return isinstance(value, int) and value > 0
    
    @staticmethod
    def is_positive_float(value: Any) -> bool:
        """Check if value is a positive float."""
        return isinstance(value, (int, float)) and value > 0
    
    @staticmethod
    def is_in_range(value: Any, min_val: float, max_val: float) -> bool:
        """Check if value is in range."""
        return isinstance(value, (int, float)) and min_val <= value <= max_val
    
    @staticmethod
    def is_one_of(value: Any, options: List[Any]) -> bool:
        """Check if value is one of the options."""
        return value in options
    
    @staticmethod
    def is_boolean(value: Any) -> bool:
        """Check if value is boolean."""
        return isinstance(value, bool)
    
    @staticmethod
    def is_string(value: Any) -> bool:
        """Check if value is string."""
        return isinstance(value, str)
    
    @staticmethod
    def is_dict(value: Any) -> bool:
        """Check if value is dictionary."""
        return isinstance(value, dict)
    
    @staticmethod
    def is_list(value: Any) -> bool:
        """Check if value is list."""
        return isinstance(value, list)

# Configuration Templates
class ConfigTemplates:
    """Predefined configuration templates."""
    
    @staticmethod
    def development_config() -> Dict[str, Any]:
        """Development environment configuration."""
        return {
            "production_mode": "development",
            "hidden_size": 256,
            "num_experts": 4,
            "max_batch_size": 8,
            "max_sequence_length": 512,
            "enable_monitoring": True,
            "enable_metrics": True,
            "log_level": "debug",
            "max_concurrent_requests": 10,
            "request_timeout": 30.0,
            "memory_threshold_mb": 2000.0,
            "cpu_threshold_percent": 70.0
        }
    
    @staticmethod
    def staging_config() -> Dict[str, Any]:
        """Staging environment configuration."""
        return {
            "production_mode": "staging",
            "hidden_size": 512,
            "num_experts": 8,
            "max_batch_size": 16,
            "max_sequence_length": 1024,
            "enable_monitoring": True,
            "enable_metrics": True,
            "log_level": "info",
            "max_concurrent_requests": 50,
            "request_timeout": 30.0,
            "memory_threshold_mb": 4000.0,
            "cpu_threshold_percent": 75.0
        }
    
    @staticmethod
    def production_config() -> Dict[str, Any]:
        """Production environment configuration."""
        return {
            "production_mode": "production",
            "hidden_size": 512,
            "num_experts": 8,
            "max_batch_size": 32,
            "max_sequence_length": 2048,
            "enable_monitoring": True,
            "enable_metrics": True,
            "log_level": "info",
            "max_concurrent_requests": 100,
            "request_timeout": 30.0,
            "memory_threshold_mb": 8000.0,
            "cpu_threshold_percent": 80.0
        }
    
    @staticmethod
    def high_performance_config() -> Dict[str, Any]:
        """High performance environment configuration."""
        return {
            "production_mode": "high_performance",
            "hidden_size": 1024,
            "num_experts": 16,
            "max_batch_size": 64,
            "max_sequence_length": 4096,
            "enable_monitoring": True,
            "enable_metrics": True,
            "log_level": "warning",
            "max_concurrent_requests": 200,
            "request_timeout": 60.0,
            "memory_threshold_mb": 16000.0,
            "cpu_threshold_percent": 90.0
        }

# Usage Examples and Demo
def create_configuration_demo():
    """Demonstrate configuration management system."""
    print("🔧 Configuration Management System Demo")
    print("=" * 50)
    
    # Create configuration manager
    manager = ConfigurationManager()
    
    # Add validation rules
    manager.add_validation_rule(ConfigValidationRule(
        field="hidden_size",
        validator=ConfigValidators.is_positive_int,
        error_message="Hidden size must be a positive integer"
    ))
    
    manager.add_validation_rule(ConfigValidationRule(
        field="production_mode",
        validator=lambda x: x in ["development", "staging", "production"],
        error_message="Invalid production mode"
    ))
    
    # Add observer
    def config_observer(key: str, value: Any):
        print(f"  📝 Config changed: {key} = {value}")
    
    manager.add_observer(config_observer)
    
    # Set base configuration
    manager.base_config = ConfigTemplates.development_config()
    
    # Load configuration
    config = manager.load_configuration()
    print(f"📊 Loaded configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # Test configuration changes
    print(f"\n🔄 Testing configuration changes...")
    manager.set("hidden_size", 1024)
    manager.set("num_experts", 16)
    
    # Test validation
    print(f"\n✅ Testing validation...")
    try:
        manager.set("hidden_size", -1)  # Should fail validation
    except Exception as e:
        print(f"  ❌ Validation failed as expected: {e}")
    
    # Get configuration summary
    print(f"\n📋 Configuration Summary:")
    summary = manager.get_config_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Test environment-specific configuration
    print(f"\n🌍 Testing environment-specific configuration...")
    builder = EnvironmentConfigBuilder()
    
    # Development environment
    dev_config = (builder
                  .for_environment("development")
                  .with_base_config(ConfigTemplates.development_config())
                  .with_override("debug_mode", True)
                  .build())
    
    # Production environment
    prod_config = (builder
                   .for_environment("production")
                   .with_base_config(ConfigTemplates.production_config())
                   .with_override("debug_mode", False)
                   .build())
    
    print(f"  Development config: {dev_config['development']}")
    print(f"  Production config: {prod_config['production']}")
    
    print(f"\n✅ Configuration management demo completed!")
    
    return manager

if __name__ == "__main__":
    # Run configuration demo
    manager = create_configuration_demo()




