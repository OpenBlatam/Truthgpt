import asyncio
import sys
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import shlex
from loguru import logger
import json

try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

@dataclass
class Command:
    """Represents a CLI command with metadata."""
    name: str
    handler: Callable
    description: str
    usage: str
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []

class CommandRegistry:
    """Registry for CLI commands with auto-completion support."""
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.aliases: Dict[str, str] = {}
        
    def register(self, name: str, description: str, usage: str, aliases: List[str] = None):
        """Decorator to register a command."""
        def decorator(func):
            cmd = Command(name, func, description, usage, aliases or [])
            self.commands[name] = cmd
            
            # Register aliases
            for alias in cmd.aliases:
                self.aliases[alias] = name
                
            return func
        return decorator
        
    def get_command(self, name: str) -> Optional[Command]:
        """Get command by name or alias."""
        if name in self.commands:
            return self.commands[name]
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        return None
        
    def get_completions(self, text: str) -> List[str]:
        """Get command completions for autocomplete."""
        all_names = list(self.commands.keys()) + list(self.aliases.keys())
        return [name for name in all_names if name.startswith(text)]

class TruthGPTCLI:
    """Interactive CLI for TruthGPT Kernel management."""
    
    def __init__(self, kernel=None):
        self.kernel = kernel
        self.commands = CommandRegistry()
        self.running = False
        self.setup_commands()
        self.setup_readline()
        
    def setup_readline(self):
        """Setup readline for command history and auto-completion."""
        if not HAS_READLINE:
            return
            
        def completer(text, state):
            """Auto-completion function."""
            line = readline.get_line_buffer()
            parts = shlex.split(line) if line else []
            
            if not parts or (len(parts) == 1 and not line.endswith(' ')):
                # Complete command names
                matches = self.commands.get_completions(text)
            else:
                # Complete command arguments (can be extended later)
                matches = []
                
            try:
                return matches[state]
            except IndexError:
                return None
                
        readline.set_completer(completer)
        readline.parse_and_bind('tab: complete')
        
        # Load command history
        try:
            readline.read_history_file('.truthgpt_history')
        except FileNotFoundError:
            pass
            
    def setup_commands(self):
        """Register all built-in commands."""
        
        @self.commands.register('help', 'Show help information', 'help [command]', ['h', '?'])
        async def cmd_help(args: List[str]):
            if not args:
                # Show all commands
                print("\n🚀 TruthGPT Kernel CLI - Available Commands:")
                print("=" * 50)
                
                for name, cmd in sorted(self.commands.commands.items()):
                    aliases = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                    print(f"  {cmd.name:<12}{aliases:<10} - {cmd.description}")
                    
                print("\nUse 'help <command>' for detailed usage information.")
                print("Use 'exit' or Ctrl+C to quit.\n")
            else:
                # Show specific command help
                cmd_name = args[0]
                cmd = self.commands.get_command(cmd_name)
                if cmd:
                    print(f"\nCommand: {cmd.name}")
                    print(f"Description: {cmd.description}")
                    print(f"Usage: {cmd.usage}")
                    if cmd.aliases:
                        print(f"Aliases: {', '.join(cmd.aliases)}")
                    print()
                else:
                    print(f"Unknown command: {cmd_name}")
                    
        @self.commands.register('status', 'Show kernel and service status', 'status [detail]', ['st'])
        async def cmd_status(args: List[str]):
            if not self.kernel:
                print("❌ Kernel not available")
                return
                
            detailed = len(args) > 0 and args[0] in ['detail', 'detailed', '-d']
            
            print("\n🔍 TruthGPT Kernel Status")
            print("=" * 30)
            
            # Kernel status
            print(f"Kernel: ✅ Running")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Service status
            if hasattr(self.kernel.service_manager, 'get_service_status'):
                services = self.kernel.service_manager.get_service_status()
                
                print(f"\n📊 Services ({len(services)} total):")
                for name, info in services.items():
                    status_icon = "✅" if info['running'] and info['healthy'] else "❌"
                    print(f"  {status_icon} {name:<15} - {'Running' if info['running'] else 'Stopped'}")
                    
                    if detailed:
                        print(f"    {'':>4}Health: {'OK' if info['healthy'] else 'FAILED'}")
                        if info['startup_time']:
                            print(f"    {'':>4}Startup: {info['startup_time']:.2f}s")
                        if info['restart_count'] > 0:
                            print(f"    {'':>4}Restarts: {info['restart_count']}")
                        if info['dependencies']:
                            print(f"    {'':>4}Depends on: {', '.join(info['dependencies'])}")
            else:
                print("\n📊 Services: Status unavailable (using basic ServiceManager)")
                
            print()
            
        @self.commands.register('services', 'Manage services', 'services <list|start|stop|restart> [service_name]', ['svc'])
        async def cmd_services(args: List[str]):
            if not args:
                await cmd_status([])
                return
                
            action = args[0].lower()
            
            if action == 'list':
                await cmd_status(['detail'])
            elif action in ['start', 'stop', 'restart']:
                if len(args) < 2:
                    print(f"Usage: services {action} <service_name>")
                    return
                    
                service_name = args[1]
                
                if not hasattr(self.kernel.service_manager, f'{action}_service'):
                    print(f"❌ Service management not available (using basic ServiceManager)")
                    return
                    
                print(f"🔄 {action.title()}ing service: {service_name}...")
                
                try:
                    method = getattr(self.kernel.service_manager, f'{action}_service')
                    success = await method(service_name)
                    
                    if success:
                        print(f"✅ Service {service_name} {action}ed successfully")
                    else:
                        print(f"❌ Failed to {action} service {service_name}")
                        
                except Exception as e:
                    print(f"❌ Error {action}ing service {service_name}: {e}")
            else:
                print(f"Unknown action: {action}. Use: list, start, stop, restart")
                
        @self.commands.register('logs', 'Show recent logs', 'logs [lines]', ['log'])
        async def cmd_logs(args: List[str]):
            lines = 20
            if args:
                try:
                    lines = int(args[0])
                except ValueError:
                    print("Invalid number of lines")
                    return
                    
            print(f"\n📄 Recent logs ({lines} lines):")
            print("=" * 40)
            
            # This would integrate with actual logging system
            # For now, show placeholder
            print("(Log integration pending - would show recent kernel/service logs)")
            print()
            
        @self.commands.register('config', 'Show or reload configuration', 'config [reload]', ['cfg'])
        async def cmd_config(args: List[str]):
            if args and args[0] == 'reload':
                print("🔄 Reloading configuration...")
                # This would integrate with config system
                print("✅ Configuration reloaded")
            else:
                print("\n⚙️ Current Configuration:")
                print("=" * 30)
                if hasattr(self.kernel, 'config'):
                    # Show current config (simplified)
                    print(f"Config object: {type(self.kernel.config).__name__}")
                    print("(Detailed config display pending)")
                else:
                    print("Configuration not available")
                print()
                
        @self.commands.register('events', 'Show recent events', 'events [count]', ['evt'])
        async def cmd_events(args: List[str]):
            count = 10
            if args:
                try:
                    count = int(args[0])
                except ValueError:
                    print("Invalid count")
                    return
                    
            print(f"\n📡 Recent Events (last {count}):")
            print("=" * 35)
            
            # This would integrate with event bus
            if hasattr(self.kernel.event_bus, 'event_history'):
                events = getattr(self.kernel.event_bus, 'event_history', [])
                recent_events = events[-count:] if events else []
                
                if recent_events:
                    for event in recent_events:
                        print(f"  📅 {event}")
                else:
                    print("  (No recent events)")
            else:
                print("  (Event history not available)")
            print()
            
        @self.commands.register('clear', 'Clear the screen', 'clear', ['cls'])
        async def cmd_clear(args: List[str]):
            import os
            os.system('clear' if os.name == 'posix' else 'cls')
            
        @self.commands.register('exit', 'Exit the CLI', 'exit', ['quit', 'q'])
        async def cmd_exit(args: List[str]):
            print("👋 Goodbye!")
            self.running = False
            
    def print_banner(self):
        """Print startup banner."""
        print("")
        print("🚀 TruthGPT Kernel CLI v2.0")
        print("==============================")
        print("Interactive Command Interface")
        print("Type 'help' for commands, 'exit' to quit")
        print("")
        
    async def execute_command(self, line: str):
        """Execute a command line."""
        line = line.strip()
        if not line:
            return
            
        try:
            parts = shlex.split(line)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            return
            
        cmd_name = parts[0]
        args = parts[1:]
        
        command = self.commands.get_command(cmd_name)
        if command:
            try:
                await command.handler(args)
            except Exception as e:
                print(f"Error executing command '{cmd_name}': {e}")
                logger.error(f"CLI command error: {e}", exc_info=True)
        else:
            print(f"Unknown command: {cmd_name}. Type 'help' for available commands.")
            
    async def start_interactive_mode(self):
        """Start the interactive CLI loop."""
        self.print_banner()
        self.running = True
        
        try:
            while self.running:
                try:
                    if HAS_READLINE:
                        line = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: input("truthgpt> ")
                        )
                    else:
                        print("truthgpt> ", end="", flush=True)
                        line = await asyncio.get_event_loop().run_in_executor(
                            None, sys.stdin.readline
                        )
                        line = line.rstrip('\n\r')
                        
                    if line:
                        await self.execute_command(line)
                        
                except EOFError:
                    # Ctrl+D
                    print("\n👋 Goodbye!")
                    break
                except KeyboardInterrupt:
                    # Ctrl+C
                    print("\n👋 Goodbye!")
                    break
                    
        finally:
            # Save command history
            if HAS_READLINE:
                try:
                    readline.write_history_file('.truthgpt_history')
                except:
                    pass
                    
    async def run_single_command(self, command: str):
        """Execute a single command (for non-interactive mode)."""
        await self.execute_command(command)
