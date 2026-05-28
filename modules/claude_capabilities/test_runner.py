import subprocess
import os
from typing import List, Optional
from pathlib import Path

class TestRunner:
    """Orchestrates and runs test suites, supporting various frameworks."""
    def __init__(self, cwd: Optional[str] = None):
        self.cwd = cwd or os.getcwd()
        self.results: List[dict] = []

    def run_tests(self, test_paths: Optional[List[str]] = None) -> str:
        """Execute tests from given paths. Uses pytest if available, else unittest."""
        if test_paths is None:
            test_paths = ["tests"]
        command = ["pytest", "-v"] + test_paths
        try:
            result = subprocess.run(
                command,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=120,
                check=False
            )
            output = result.stdout + "\n" + result.stderr
            return output if output else "[TestRunner] No output."
        except subprocess.TimeoutExpired:
            return "[TestRunner] Test execution timed out."
        except FileNotFoundError:
            # fallback to unittest
            return self._run_unittest(test_paths)

    def _run_unittest(self, test_paths: List[str]) -> str:
        # Simple fallback using unittest discover
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=test_paths[0] if test_paths else '.', pattern='test*.py')
        runner = unittest.TextTestRunner(verbosity=2)
        with open(os.devnull, 'w') as null_out:
            result = runner.run(suite)
        return f"[TestRunner] Unittest results: {result.testsRun} run, {len(result.failures)} failures, {len(result.errors)} errors."
