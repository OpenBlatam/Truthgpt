import subprocess
import shlex
from typing import List, Optional

class CommandExecutor:
    """Executes shell commands safely, inspired by Claude Code capabilities."""
    def __init__(self, allowed_commands: Optional[List[str]] = None, timeout: int = 30):
        self.allowed_commands = allowed_commands or ["ls", "cat", "echo", "pwd", "whoami", "date"]
        self.timeout = timeout

    def execute(self, command: str) -> str:
        """Execute a shell command if allowed. Returns output as string."""
        if not command.strip():
            return "[CommandExecutor] Empty command."
        parts = shlex.split(command)
        if not parts:
            return "[CommandExecutor] Invalid command."
        base_cmd = parts[0]
        if base_cmd not in self.allowed_commands:
            return f"[CommandExecutor] Command '{base_cmd}' not allowed. Allowed: {self.allowed_commands}"
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False
            )
            output = result.stdout + result.stderr
            return output if output else "[CommandExecutor] (empty output)"
        except subprocess.TimeoutExpired:
            return f"[CommandExecutor] Command timed out after {self.timeout}s."
        except Exception as e:
            return f"[CommandExecutor] Error: {str(e)}"
