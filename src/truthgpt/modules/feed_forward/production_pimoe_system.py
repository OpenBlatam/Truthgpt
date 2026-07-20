"""
Production-Ready PiMoE System
Enhanced for production deployment with:
- Production optimizations
- Monitoring and logging
- Error handling and recovery
- Scalability features
- Deployment configurations
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
import math
import numpy as np
import time
import logging
import json
import os
import threading
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import psutil
import gc
from contextlib import contextmanager
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import signal
import sys

from .advanced_pimoe_routing import RoutingStrategy, AdvancedPiMoESystem, AdvancedRoutingConfig
from .pimoe_performance_optimizer import OptimizationLevel

class ProductionMode(Enum):
    """Production deployment modes."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    HIGH_PERFORMANCE = "high_performance"
    COST_OPTIMIZED = "cost_optimized"

class LogLevel(Enum):
    """Logging levels for production."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ProductionConfig:
    """Production configuration for PiMoE system."""
    # System configuration
    hidden_size: int = 512
    num_experts: int = 8
    max_batch_size: int = 32
    max_sequence_length: int = 2048
    
    # Production settings
    production_mode: ProductionMode = ProductionMode.PRODUCTION
    log_level: LogLevel = LogLevel.INFO
    enable_monitoring: bool = True
    enable_metrics: bool = True
    enable_health_checks: bool = True
    
    # Performance settings
    optimization_level: OptimizationLevel = OptimizationLevel.EXTREME
    enable_quantization: bool = True
    enable_pruning: bool = True
    enable_distillation: bool = False
    mixed_precision: bool = True
    
    # Scalability settings
    max_concurrent_requests: int = 100
    request_timeout: float = 30.0
    memory_threshold_mb: float = 8000.0
    cpu_threshold_percent: float = 80.0
    
    # Monitoring settings
    metrics_interval: float = 1.0
    health_check_interval: float = 5.0
    log_interval: float = 10.0
    
    # Error handling
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 10
    
    # Deployment settings
    model_version: str = "1.0.0"
    deployment_id: str = "pimoe-prod-001"
    environment: str = "production"

class ProductionLogger:
    """Production-ready logging system."""
    
    def __init__(self, config: ProductionConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.metrics_logger = self._setup_metrics_logger()
        self.error_logger = self._setup_error_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup main application logger."""
        logger = logging.getLogger('pimoe_production')
        logger.setLevel(getattr(logging, self.config.log_level.value.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler('pimoe_production.log')
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def _setup_metrics_logger(self) -> logging.Logger:
        """Setup metrics logger."""
        logger = logging.getLogger('pimoe_metrics')
        logger.setLevel(logging.INFO)
        
        # Metrics file handler
        metrics_handler = logging.FileHandler('pimoe_metrics.log')
        metrics_handler.setLevel(logging.INFO)
        
        # JSON formatter for metrics
        json_formatter = logging.Formatter('%(message)s')
        metrics_handler.setFormatter(json_formatter)
        
        logger.addHandler(metrics_handler)
        logger.propagate = False
        
        return logger
    
    def _setup_error_logger(self) -> logging.Logger:
        """Setup error logger."""
        logger = logging.getLogger('pimoe_errors')
        logger.setLevel(logging.ERROR)
        
        # Error file handler
        error_handler = logging.FileHandler('pimoe_errors.log')
        error_handler.setLevel(logging.ERROR)
        
        # Detailed formatter for errors
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        
        logger.addHandler(error_handler)
        logger.propagate = False
        
        return logger
    
    def log_info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(f"{message} | {kwargs}")
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(f"{message} | {kwargs}")
    
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message."""
        if exception:
            self.error_logger.error(f"{message} | {kwargs}", exc_info=exception)
        else:
            self.error_logger.error(f"{message} | {kwargs}")
    
    def log_metrics(self, metrics: Dict[str, Any]):
        """Log metrics in JSON format."""
        metrics['timestamp'] = time.time()
        metrics['deployment_id'] = self.config.deployment_id
        self.metrics_logger.info(json.dumps(metrics))

class ProductionMonitor:
    """Production monitoring system."""
    
    def __init__(self, config: ProductionConfig, logger: ProductionLogger):
        self.config = config
        self.logger = logger
        self.metrics = defaultdict(list)
        self.health_status = "healthy"
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.circuit_breaker_count = 0
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                self._collect_metrics()
                self._check_health()
                time.sleep(self.config.metrics_interval)
            except Exception as e:
                self.logger.log_error("Monitoring loop error", e)
                time.sleep(1.0)
    
    def _collect_metrics(self):
        """Collect system metrics."""
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Custom metrics
        uptime = time.time() - self.start_time
        request_rate = self.request_count / uptime if uptime > 0 else 0
        error_rate = self.error_count / max(self.request_count, 1)
        
        metrics = {
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_mb': disk.free / (1024 * 1024)
            },
            'process': {
                'memory_rss_mb': process_memory.rss / (1024 * 1024),
                'memory_vms_mb': process_memory.vms / (1024 * 1024),
                'cpu_percent': process.cpu_percent()
            },
            'application': {
                'uptime_seconds': uptime,
                'request_count': self.request_count,
                'error_count': self.error_count,
                'request_rate': request_rate,
                'error_rate': error_rate,
                'health_status': self.health_status
            }
        }
        
        # Log metrics
        self.logger.log_metrics(metrics)
        
        # Store metrics for analysis
        self.metrics['system'].append(metrics['system'])
        self.metrics['process'].append(metrics['process'])
        self.metrics['application'].append(metrics['application'])
        
        # Keep only recent metrics
        max_metrics = 1000
        for key in self.metrics:
            if len(self.metrics[key]) > max_metrics:
                self.metrics[key] = self.metrics[key][-max_metrics:]
    
    def _check_health(self):
        """Check system health."""
        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > self.config.memory_threshold_mb / 100 * 100:
            self.health_status = "unhealthy"
            self.logger.log_warning(f"High memory usage: {memory.percent}%")
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > self.config.cpu_threshold_percent:
            self.health_status = "unhealthy"
            self.logger.log_warning(f"High CPU usage: {cpu_percent}%")
        
        # Check circuit breaker
        if self.circuit_breaker_count > self.config.circuit_breaker_threshold:
            self.health_status = "circuit_breaker_open"
            self.logger.log_error("Circuit breaker opened due to high error rate")
    
    def record_request(self, success: bool = True):
        """Record a request."""
        self.request_count += 1
        if not success:
            self.error_count += 1
            self.circuit_breaker_count += 1
        else:
            self.circuit_breaker_count = max(0, self.circuit_breaker_count - 1)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            'status': self.health_status,
            'uptime': time.time() - self.start_time,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1),
            'circuit_breaker_count': self.circuit_breaker_count
        }

class ProductionErrorHandler:
    """Production error handling system."""
    
    def __init__(self, config: ProductionConfig, logger: ProductionLogger):
        self.config = config
        self.logger = logger
        self.error_counts = defaultdict(int)
        self.last_error_time = defaultdict(float)
        
    def handle_error(self, error: Exception, context: str = "") -> bool:
        """Handle production errors."""
        error_type = type(error).__name__
        current_time = time.time()
        
        # Check if this is a new error or repeated
        if current_time - self.last_error_time[error_type] > 60:  # 1 minute window
            self.error_counts[error_type] = 0
        
        self.error_counts[error_type] += 1
        self.last_error_time[error_type] = current_time
        
        # Log error
        self.logger.log_error(
            f"Error in {context}",
            error,
            error_type=error_type,
            error_count=self.error_counts[error_type]
        )
        
        # Determine if we should retry
        if self.error_counts[error_type] <= self.config.max_retries:
            return True  # Retry
        
        return False  # Don't retry
    
    def should_circuit_break(self) -> bool:
        """Check if circuit breaker should be opened."""
        total_errors = sum(self.error_counts.values())
        return total_errors > self.config.circuit_breaker_threshold

class ProductionRequestQueue:
    """Production request queue for handling concurrent requests."""
    
    def __init__(self, config: ProductionConfig, logger: ProductionLogger):
        self.config = config
        self.logger = logger
        self.request_queue = queue.Queue(maxsize=config.max_concurrent_requests)
        self.processing_pool = ThreadPoolExecutor(max_workers=config.max_concurrent_requests)
        self.active_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0
        
    def submit_request(self, request_data: Dict[str, Any], callback: Callable) -> str:
        """Submit a request for processing."""
        request_id = f"req_{int(time.time() * 1000)}"
        
        try:
            # Add to queue
            self.request_queue.put({
                'request_id': request_id,
                'data': request_data,
                'callback': callback,
                'timestamp': time.time()
            }, timeout=1.0)
            
            self.logger.log_info(f"Request submitted: {request_id}")
            return request_id
            
        except queue.Full:
            self.logger.log_error(f"Request queue full, rejecting request: {request_id}")
            raise RuntimeError("Request queue is full")
    
    def process_requests(self):
        """Process requests from the queue."""
        while True:
            try:
                # Get request from queue
                request = self.request_queue.get(timeout=1.0)
                
                # Process request
                self.processing_pool.submit(self._process_single_request, request)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.log_error("Error processing request", e)
    
    def _process_single_request(self, request: Dict[str, Any]):
        """Process a single request."""
        request_id = request['request_id']
        start_time = time.time()
        
        try:
            self.active_requests += 1
            
            # Process request
            result = request['callback'](request['data'])
            
            # Record success
            self.completed_requests += 1
            processing_time = time.time() - start_time
            
            self.logger.log_info(
                f"Request completed: {request_id}",
                processing_time=processing_time,
                active_requests=self.active_requests
            )
            
        except Exception as e:
            # Record failure
            self.failed_requests += 1
            processing_time = time.time() - start_time
            
            self.logger.log_error(
                f"Request failed: {request_id}",
                e,
                processing_time=processing_time,
                active_requests=self.active_requests
            )
            
        finally:
            self.active_requests -= 1
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            'queue_size': self.request_queue.qsize(),
            'active_requests': self.active_requests,
            'completed_requests': self.completed_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.completed_requests / max(self.completed_requests + self.failed_requests, 1)
        }

class ProductionPiMoESystem(AdvancedPiMoESystem):
    """
    Production-ready PiMoE system with monitoring, error handling, and scalability.
    """
    
    def __init__(self, config: ProductionConfig):
        # Convert production config to advanced config
        advanced_config = AdvancedRoutingConfig(
            hidden_size=config.hidden_size,
            num_experts=config.num_experts,
            routing_strategy=RoutingStrategy.ATTENTION_BASED,
            optimization_level=config.optimization_level
        )
        
        super().__init__(advanced_config)
        
        # Production components
        self.production_config = config
        self.logger = ProductionLogger(config)
        self.monitor = ProductionMonitor(config, self.logger)
        self.error_handler = ProductionErrorHandler(config, self.logger)
        self.request_queue = ProductionRequestQueue(config, self.logger)
        
        # Production optimizations
        self._apply_production_optimizations()
        
        # Start request processing
        self._start_request_processing()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        self.logger.log_info("Production PiMoE system initialized", **asdict(config))
    
    def _apply_production_optimizations(self):
        """Apply production-specific optimizations."""
        # Optimize for inference
        self.optimize_for_inference()
        
        # Apply quantization if enabled
        if self.production_config.enable_quantization:
            self._apply_quantization()
        
        # Apply pruning if enabled
        if self.production_config.enable_pruning:
            self._apply_pruning()
        
        # Set to evaluation mode
        self.eval()
        
        # Disable gradients
        for param in self.parameters():
            param.requires_grad = False
        
        self.logger.log_info("Production optimizations applied")
    
    def _apply_quantization(self):
        """Apply quantization for production."""
        try:
            # Apply dynamic quantization
            self.pimoe_system = torch.quantization.quantize_dynamic(
                self.pimoe_system,
                {nn.Linear, nn.MultiheadAttention},
                dtype=torch.qint8
            )
            self.logger.log_info("Quantization applied successfully")
        except Exception as e:
            self.logger.log_error("Failed to apply quantization", e)
    
    def _apply_pruning(self):
        """Apply pruning for production."""
        try:
            # Apply structured pruning
            for module in self.modules():
                if isinstance(module, nn.Linear):
                    # Prune 10% of weights
                    weight = module.weight.data
                    threshold = torch.quantile(torch.abs(weight), 0.1)
                    mask = torch.abs(weight) > threshold
                    module.weight.data *= mask.float()
            
            self.logger.log_info("Pruning applied successfully")
        except Exception as e:
            self.logger.log_error("Failed to apply pruning", e)
    
    def _start_request_processing(self):
        """Start request processing thread."""
        processing_thread = threading.Thread(
            target=self.request_queue.process_requests,
            daemon=True
        )
        processing_thread.start()
        self.logger.log_info("Request processing started")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.log_info(f"Received signal {signum}, shutting down gracefully")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def process_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a production request."""
        start_time = time.time()
        request_id = input_data.get('request_id', 'unknown')
        
        try:
            # Check circuit breaker
            if self.error_handler.should_circuit_break():
                raise RuntimeError("Circuit breaker is open")
            
            # Extract input tensor
            input_tensor = input_data['input_tensor']
            attention_mask = input_data.get('attention_mask', None)
            return_comprehensive_info = input_data.get('return_comprehensive_info', False)
            
            # Validate input
            if not isinstance(input_tensor, torch.Tensor):
                raise ValueError("Input must be a torch.Tensor")
            
            if input_tensor.dim() != 3:
                raise ValueError("Input must be 3D tensor [batch, seq, hidden]")
            
            # Check batch size
            if input_tensor.size(0) > self.production_config.max_batch_size:
                raise ValueError(f"Batch size {input_tensor.size(0)} exceeds maximum {self.production_config.max_batch_size}")
            
            # Check sequence length
            if input_tensor.size(1) > self.production_config.max_sequence_length:
                raise ValueError(f"Sequence length {input_tensor.size(1)} exceeds maximum {self.production_config.max_sequence_length}")
            
            # Process request
            with torch.no_grad():
                if return_comprehensive_info:
                    output, comprehensive_info = self.forward(
                        input_tensor, attention_mask, return_comprehensive_info=True
                    )
                else:
                    output = self.forward(input_tensor, attention_mask)
                    comprehensive_info = None
            
            # Record success
            processing_time = time.time() - start_time
            self.monitor.record_request(success=True)
            
            # Log success
            self.logger.log_info(
                f"Request processed successfully: {request_id}",
                processing_time=processing_time,
                batch_size=input_tensor.size(0),
                sequence_length=input_tensor.size(1)
            )
            
            # Prepare response
            response = {
                'request_id': request_id,
                'output': output.cpu().numpy().tolist(),
                'processing_time': processing_time,
                'success': True
            }
            
            if comprehensive_info:
                response['comprehensive_info'] = comprehensive_info
            
            return response
            
        except Exception as e:
            # Record failure
            processing_time = time.time() - start_time
            self.monitor.record_request(success=False)
            
            # Handle error
            should_retry = self.error_handler.handle_error(e, f"Request {request_id}")
            
            # Log error
            self.logger.log_error(
                f"Request failed: {request_id}",
                e,
                processing_time=processing_time,
                should_retry=should_retry
            )
            
            # Return error response
            return {
                'request_id': request_id,
                'error': str(e),
                'processing_time': processing_time,
                'success': False,
                'should_retry': should_retry
            }
    
    def submit_request(self, input_data: Dict[str, Any], callback: Optional[Callable] = None) -> str:
        """Submit a request for asynchronous processing."""
        if callback is None:
            callback = self._default_callback
        
        return self.request_queue.submit_request(input_data, callback)
    
    def _default_callback(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default callback for request processing."""
        return self.process_request(input_data)
    
    def get_production_stats(self) -> Dict[str, Any]:
        """Get production statistics."""
        stats = {
            'system': self.get_system_stats(),
            'monitoring': self.monitor.get_health_status(),
            'queue': self.request_queue.get_queue_stats(),
            'production_config': asdict(self.production_config)
        }
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health_status = self.monitor.get_health_status()
        
        # Additional health checks
        try:
            # Test model forward pass
            test_input = torch.randn(1, 10, self.production_config.hidden_size)
            with torch.no_grad():
                _ = self.forward(test_input)
            
            health_status['model_health'] = 'healthy'
        except Exception as e:
            health_status['model_health'] = 'unhealthy'
            health_status['model_error'] = str(e)
        
        return health_status
    
    def shutdown(self):
        """Graceful shutdown."""
        self.logger.log_info("Shutting down production PiMoE system")
        
        # Stop request processing
        self.request_queue.processing_pool.shutdown(wait=True)
        
        # Log final statistics
        final_stats = self.get_production_stats()
        self.logger.log_info("Final statistics", **final_stats)
        
        self.logger.log_info("Production PiMoE system shutdown complete")

def create_production_pimoe_system(
    hidden_size: int = 512,
    num_experts: int = 8,
    production_mode: ProductionMode = ProductionMode.PRODUCTION,
    **kwargs
) -> ProductionPiMoESystem:
    """
    Factory function to create a production PiMoE system.
    """
    config = ProductionConfig(
        hidden_size=hidden_size,
        num_experts=num_experts,
        production_mode=production_mode,
        **kwargs
    )
    
    return ProductionPiMoESystem(config)

def run_production_demo():
    """Run production system demonstration."""
    print("🚀 Production PiMoE System Demo")
    print("=" * 50)
    
    # Create production system
    system = create_production_pimoe_system(
        hidden_size=512,
        num_experts=8,
        production_mode=ProductionMode.PRODUCTION,
        max_batch_size=16,
        max_sequence_length=1024,
        enable_monitoring=True,
        enable_metrics=True
    )
    
    # Generate test data
    batch_size = 2
    seq_len = 128
    hidden_size = 512
    test_input = torch.randn(batch_size, seq_len, hidden_size)
    
    print(f"📊 System Configuration:")
    print(f"  Hidden Size: {hidden_size}")
    print(f"  Number of Experts: 8")
    print(f"  Production Mode: {system.production_config.production_mode.value}")
    print(f"  Max Batch Size: {system.production_config.max_batch_size}")
    print(f"  Max Sequence Length: {system.production_config.max_sequence_length}")
    
    # Test request processing
    print(f"\n🔄 Testing Request Processing...")
    
    request_data = {
        'request_id': 'test_001',
        'input_tensor': test_input,
        'return_comprehensive_info': True
    }
    
    # Process request
    start_time = time.time()
    response = system.process_request(request_data)
    end_time = time.time()
    
    print(f"  Request ID: {response['request_id']}")
    print(f"  Success: {response['success']}")
    print(f"  Processing Time: {response['processing_time']:.4f} s")
    print(f"  Output Shape: {len(response['output'])} x {len(response['output'][0])} x {len(response['output'][0][0])}")
    
    # Test health check
    print(f"\n🏥 Testing Health Check...")
    health_status = system.health_check()
    print(f"  System Health: {health_status['status']}")
    print(f"  Model Health: {health_status.get('model_health', 'unknown')}")
    print(f"  Uptime: {health_status['uptime']:.2f} s")
    print(f"  Request Count: {health_status['request_count']}")
    print(f"  Error Count: {health_status['error_count']}")
    
    # Test production statistics
    print(f"\n📈 Production Statistics:")
    stats = system.get_production_stats()
    
    print(f"  System Stats:")
    print(f"    System Type: {stats['system']['system_type']")
    print(f"    Hidden Size: {stats['system']['hidden_size']}")
    print(f"    Number of Experts: {stats['system']['num_experts']}")
    
    print(f"  Monitoring Stats:")
    print(f"    Health Status: {stats['monitoring']['status']}")
    print(f"    Request Count: {stats['monitoring']['request_count']}")
    print(f"    Error Rate: {stats['monitoring']['error_rate']:.3f}")
    
    print(f"  Queue Stats:")
    print(f"    Queue Size: {stats['queue']['queue_size']}")
    print(f"    Active Requests: {stats['queue']['active_requests']}")
    print(f"    Success Rate: {stats['queue']['success_rate']:.3f}")
    
    # Test multiple requests
    print(f"\n🔄 Testing Multiple Requests...")
    
    for i in range(5):
        request_data = {
            'request_id': f'test_{i:03d}',
            'input_tensor': torch.randn(1, 64, hidden_size),
            'return_comprehensive_info': False
        }
        
        response = system.process_request(request_data)
        print(f"  Request {i+1}: {'✅' if response['success'] else '❌'} ({response['processing_time']:.4f}s)")
    
    # Final statistics
    print(f"\n📊 Final Statistics:")
    final_stats = system.get_production_stats()
    
    print(f"  Total Requests: {final_stats['monitoring']['request_count']}")
    print(f"  Total Errors: {final_stats['monitoring']['error_count']}")
    print(f"  Error Rate: {final_stats['monitoring']['error_rate']:.3f}")
    print(f"  Success Rate: {final_stats['queue']['success_rate']:.3f}")
    
    # Graceful shutdown
    print(f"\n🛑 Shutting Down...")
    system.shutdown()
    
    print(f"\n✅ Production PiMoE demo completed successfully!")
    
    return system

if __name__ == "__main__":
    # Run production demo
    system = run_production_demo()




