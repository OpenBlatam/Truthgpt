#!/usr/bin/env python3
"""
🚀 TruthGPT Enhanced Command Center — Enterprise-Ready AI Kernel
System 6.1 Enhanced Architecture with CLI, API, and Service Management

Usage:
    python enhanced_main.py                    # Start with interactive CLI
    python enhanced_main.py --daemon           # Start as background service
    python enhanced_main.py --api              # Start with REST API
    python enhanced_main.py --config dev       # Use development config
    python enhanced_main.py --no-cli           # Start without CLI
    python enhanced_main.py --status           # Show system status
"""
import sys
import os
import asyncio

# Fix Windows emoji encoding issues
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import argparse
import signal
import json
from pathlib import Path
from typing import Optional

# Ensure paths are ready before loading the kernel
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from loguru import logger
from core.kernel.truthgpt_kernel import TruthGPTKernel
from core.kernel.config.kernel_config import (
    KernelConfig, DEVELOPMENT_CONFIG, PRODUCTION_CONFIG, TESTING_CONFIG
)

class TruthGPTLauncher:
    """Enhanced launcher for TruthGPT with multiple execution modes."""
    
    def __init__(self):
        self.kernel: Optional[TruthGPTKernel] = None
        self.shutdown_requested = False
        
    def setup_logging(self, log_level: str = "INFO"):
        """Setup enhanced logging configuration."""
        logger.remove()  # Remove default handler
        
        # Console output with colors
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True
        )
        
        # File output for persistence. Per-process filename + enqueue/catch so the
        # rotation rename can't fail on Windows with WinError 32 ("file in use")
        # when another handler or a second instance holds the log open.
        logger.add(
            f"logs/truthgpt_kernel_{os.getpid()}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="100 MB",
            retention="7 days",
            compression="zip",
            enqueue=True,
            catch=True,
        )
        
    def load_config(self, config_name: Optional[str] = None, config_file: Optional[str] = None) -> KernelConfig:
        """Load configuration from file or use preset."""
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    return KernelConfig.from_dict(config_data)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_file}: {e}")
                logger.info("Falling back to default configuration")
                
        # Use preset configurations
        configs = {
            "dev": DEVELOPMENT_CONFIG,
            "development": DEVELOPMENT_CONFIG,
            "prod": PRODUCTION_CONFIG,
            "production": PRODUCTION_CONFIG,
            "test": TESTING_CONFIG,
            "testing": TESTING_CONFIG
        }
        
        if config_name and config_name.lower() in configs:
            logger.info(f"Using preset configuration: {config_name}")
            return configs[config_name.lower()]
            
        logger.info("Using default configuration")
        return KernelConfig()
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers."""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            logger.info(f"Received {signal_name}, initiating graceful shutdown...")
            self.shutdown_requested = True
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)
            
    async def start_kernel(self, config: KernelConfig, enable_cli: bool = True, 
                          enable_api: bool = False) -> TruthGPTKernel:
        """Start the enhanced kernel with specified configuration."""
        logger.info("🚀 Starting Enhanced TruthGPT Kernel...")
        
        # Create and configure kernel
        kernel = TruthGPTKernel(config)
        
        try:
            # Start kernel
            await kernel.start(enable_cli=enable_cli)
            
            # Start API if requested
            if enable_api:
                await self.start_api_server(kernel, config)
                
            return kernel
            
        except Exception as e:
            logger.error(f"Failed to start kernel: {e}")
            if kernel:
                await kernel.stop()
            raise
            
    async def start_api_server(self, kernel: TruthGPTKernel, config: KernelConfig):
        """Start REST API server (placeholder for future implementation)."""
        if config.enable_rest_api:
            logger.info(f"🌐 REST API would start on {config.api_host}:{config.api_port}")
            # Placeholder for FastAPI integration
            logger.info("📝 REST API integration pending implementation")
        else:
            logger.info("📴 REST API disabled in configuration")
            
    async def run_daemon_mode(self, config: KernelConfig):
        """Run in daemon mode (background service)."""
        logger.info("🔧 Starting in daemon mode...")
        
        kernel = await self.start_kernel(config, enable_cli=False, enable_api=True)
        self.kernel = kernel
        
        try:
            # Keep running until shutdown requested
            while not self.shutdown_requested and kernel.running:
                await asyncio.sleep(1)
                
                # Periodic health check
                if not kernel.health_monitor.check_health():
                    logger.warning("⚠️ Health check failed in daemon mode")
                    
        finally:
            await kernel.stop()
            
    async def run_cli_mode(self, config: KernelConfig):
        """Run with interactive CLI."""
        logger.info("💻 Starting in CLI mode...")
        
        kernel = await self.start_kernel(config, enable_cli=True)
        self.kernel = kernel
        
        # CLI handles the main loop, just wait for completion
        try:
            while kernel.running and not self.shutdown_requested:
                await asyncio.sleep(1)
        finally:
            await kernel.stop()
            
    async def run_api_mode(self, config: KernelConfig):
        """Run with REST API server."""
        logger.info("🌐 Starting in API mode...")
        
        config.enable_rest_api = True
        kernel = await self.start_kernel(config, enable_cli=False, enable_api=True)
        self.kernel = kernel
        
        try:
            while not self.shutdown_requested and kernel.running:
                await asyncio.sleep(1)
        finally:
            await kernel.stop()
            
    async def show_status(self, config: KernelConfig):
        """Show system status and exit."""
        logger.info("📊 Checking system status...")
        
        # Try to connect to running kernel (if any)
        # For now, just show configuration
        
        print("\n🔍 TruthGPT System Status")
        print("=" * 40)
        print(f"Configuration: {config.log_level.value} level")
        print(f"Services configured: {len(config.services)}")
        print(f"Health check interval: {config.health_check_interval}s")
        print(f"Event history size: {config.event_history_size}")
        print(f"Auto recovery: {'Enabled' if config.enable_auto_recovery else 'Disabled'}")
        
        if config.enable_rest_api:
            print(f"API endpoint: http://{config.api_host}:{config.api_port}")
        else:
            print("API: Disabled")
            
        print("\n📝 Note: This shows configuration only.")
        print("For live status, start the kernel and use 'status' command in CLI.")
        print()
        
def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="TruthGPT Enhanced Kernel - Enterprise AI Operating System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Interactive CLI mode
  %(prog)s --daemon                 # Background service mode  
  %(prog)s --api                    # REST API mode
  %(prog)s --config dev             # Use development configuration
  %(prog)s --config-file config.json # Use custom configuration file
  %(prog)s --status                 # Show system status
  %(prog)s --no-cli --daemon        # Headless daemon mode
        """
    )
    
    # Execution modes (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--daemon", action="store_true",
        help="Run as background daemon service"
    )
    mode_group.add_argument(
        "--api", action="store_true",
        help="Run with REST API server"
    )
    mode_group.add_argument(
        "--status", action="store_true",
        help="Show system status and exit"
    )
    
    # Configuration
    parser.add_argument(
        "--config", 
        choices=["dev", "development", "prod", "production", "test", "testing"],
        help="Use preset configuration"
    )
    parser.add_argument(
        "--config-file", 
        help="Load configuration from JSON file"
    )
    
    # Options
    parser.add_argument(
        "--no-cli", action="store_true",
        help="Disable interactive CLI (useful with --daemon)"
    )
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    parser.add_argument(
        "--version", action="version",
        version="TruthGPT Enhanced Kernel 2.0"
    )
    
    return parser

async def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    launcher = TruthGPTLauncher()
    launcher.setup_logging(args.log_level)
    launcher.setup_signal_handlers()
    
    # Load configuration
    config = launcher.load_config(args.config, args.config_file)
    
    # Override config with command line options
    if args.log_level:
        from core.kernel.config.kernel_config import LogLevel
        config.log_level = LogLevel(args.log_level)
        
    try:
        # Determine execution mode
        if args.status:
            await launcher.show_status(config)
        elif args.daemon:
            await launcher.run_daemon_mode(config)
        elif args.api:
            await launcher.run_api_mode(config)
        else:
            # Default: CLI mode (unless --no-cli specified)
            if args.no_cli:
                logger.info("CLI disabled, running in minimal daemon mode")
                await launcher.run_daemon_mode(config)
            else:
                await launcher.run_cli_mode(config)
                
    except KeyboardInterrupt:
        logger.info("👋 Shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Kernel failed with error: {e}")
        sys.exit(1)
        
    logger.info("✅ TruthGPT Enhanced Kernel stopped gracefully")

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)
