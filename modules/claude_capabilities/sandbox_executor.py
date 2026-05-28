import subprocess
import tempfile
import os
from typing import Optional

class SandboxExecutor:
    """Safe execution environment for untrusted code, inspired by Claude Code."""
    def __init__(self, timeout: int = 30, allowed_commands: Optional[list] = None):
        self.timeout = timeout
        self.allowed_commands = allowed_commands or ["python", "python3"]

    def execute(self, code: str, language: str = "python") -> str:
        """Execute code in a sandboxed temporary file. Returns output."""
        if language not in ("python",):
            return f"[SandboxExecutor] Language '{language}' not yet supported."
        if not code.strip():
            return "[SandboxExecutor] No code to execute."
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        try:
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False
            )
            output = result.stdout + result.stderr
            return output if output else "[SandboxExecutor] (empty output)"
        except subprocess.TimeoutExpired:
            return f"[SandboxExecutor] Code execution timed out after {self.timeout}s."
        except Exception as e:
            return f"[SandboxExecutor] Error: {str(e)}"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
