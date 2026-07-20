"""
System 5.9 — Formal Verification & Mathematics Agent.

Capabilities:
- Lean 4 theorem proving and proof verification
- SymPy symbolic computation and algebraic verification
- Z3 SMT constraint solving
- Numerical analysis with SciPy/NumPy
- LaTeX proof rendering
- Code correctness verification via formal methods
- Custom verification pipeline composition
"""

import logging
import json
import re
import subprocess
import tempfile
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..arquitecturas_fundamentales.base_agent import BaseAgent
from ..models import AgentResponse, AgentConfig
from ..razonamiento_planificacion.tools import (
    BaseTool, FileReadTool, FileWriteTool, DirectoryListTool
)
from ..razonamiento_planificacion.orchestrator import MultiUserReActAgent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Verification Tools
# ---------------------------------------------------------------------------

class SymPyVerifyTool(BaseTool):
    """
    Verifica expresiones matemáticas usando SymPy.
    Acepta expresiones algebraicas, ecuaciones, límites, integrales, etc.
    Ejemplo: 'simplify: (x**2 - 1)/(x - 1)' o 'solve: x**2 + 2*x + 1 = 0'
    """
    name = "sympy_verify"

    async def run(self, expr: str) -> str:
        try:
            import sympy
            from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication

            # Detect operation type
            expr_lower = expr.strip().lower()

            if expr_lower.startswith("simplify:"):
                raw = expr.split(":", 1)[1].strip()
                result = sympy.simplify(parse_expr(raw))
                return f"✓ Simplificado: {result}\nLaTeX: ${sympy.latex(result)}$"

            elif expr_lower.startswith("solve:"):
                raw = expr.split(":", 1)[1].strip()
                if "=" in raw:
                    lhs, rhs = raw.split("=", 1)
                    eq = sympy.Eq(parse_expr(lhs.strip()), parse_expr(rhs.strip()))
                else:
                    eq = parse_expr(raw)
                solutions = sympy.solve(eq)
                return f"✓ Soluciones: {solutions}\nLaTeX: ${sympy.latex(solutions)}$"

            elif expr_lower.startswith("prove:"):
                raw = expr.split(":", 1)[1].strip()
                if "==" in raw:
                    lhs, rhs = raw.split("==", 1)
                    diff = sympy.simplify(parse_expr(lhs.strip()) - parse_expr(rhs.strip()))
                    verified = diff == 0
                    return (
                        f"{'✓ PROBADO' if verified else '✗ NO VERIFICADO'}: "
                        f"{lhs.strip()} == {rhs.strip()}\n"
                        f"Diferencia simplificada: {diff}"
                    )
                return "Error: Use 'prove: LHS == RHS'"

            elif expr_lower.startswith("limit:"):
                raw = expr.split(":", 1)[1].strip()
                # Format: expr, var, point
                parts = [p.strip() for p in raw.split(",")]
                if len(parts) >= 3:
                    x = sympy.Symbol(parts[1])
                    result = sympy.limit(parse_expr(parts[0]), x, parse_expr(parts[2]))
                    return f"✓ Límite: {result}\nLaTeX: ${sympy.latex(result)}$"
                return "Error: Use 'limit: expr, variable, punto'"

            elif expr_lower.startswith("integrate:"):
                raw = expr.split(":", 1)[1].strip()
                result = sympy.integrate(parse_expr(raw))
                return f"✓ Integral: {result}\nLaTeX: $\\int {sympy.latex(parse_expr(raw))} \\, dx = {sympy.latex(result)} + C$"

            elif expr_lower.startswith("diff:") or expr_lower.startswith("derivative:"):
                raw = expr.split(":", 1)[1].strip()
                result = sympy.diff(parse_expr(raw))
                return f"✓ Derivada: {result}\nLaTeX: ${sympy.latex(result)}$"

            elif expr_lower.startswith("factor:"):
                raw = expr.split(":", 1)[1].strip()
                result = sympy.factor(parse_expr(raw))
                return f"✓ Factorizado: {result}\nLaTeX: ${sympy.latex(result)}$"

            elif expr_lower.startswith("matrix:"):
                raw = expr.split(":", 1)[1].strip()
                m = sympy.Matrix(json.loads(raw))
                det = m.det()
                eigenvals = m.eigenvals()
                return (
                    f"✓ Determinante: {det}\n"
                    f"  Eigenvalores: {eigenvals}\n"
                    f"  Rango: {m.rank()}\n"
                    f"  LaTeX: ${sympy.latex(m)}$"
                )

            else:
                # Generic evaluation
                result = sympy.simplify(parse_expr(expr.strip()))
                return f"✓ Resultado: {result}\nLaTeX: ${sympy.latex(result)}$"

        except ImportError:
            return "[TOOL DEGRADED] SymPy no instalado. pip install sympy"
        except Exception as e:
            return f"Error SymPy: {e}"


class Lean4VerifyTool(BaseTool):
    """
    Verifica teoremas y pruebas formales usando Lean 4.
    Acepta código Lean 4 y devuelve el resultado de verificación.
    Ejemplo: 'theorem add_comm (a b : Nat) : a + b = b + a := Nat.add_comm a b'
    """
    name = "lean4_verify"

    async def run(self, code: str) -> str:
        # Check if Lean 4 is available
        lean_path = self._find_lean()
        if lean_path is None:
            return await self._simulate_lean(code)

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".lean", delete=False, encoding="utf-8"
            ) as f:
                # Add Mathlib-compatible header
                full_code = (
                    "import Mathlib.Tactic\n"
                    "import Mathlib.Data.Nat.Basic\n"
                    "import Mathlib.Data.Int.Basic\n\n"
                    + code
                )
                f.write(full_code)
                f.flush()

                proc = await asyncio.create_subprocess_exec(
                    lean_path, f.name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tempfile.gettempdir(),
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=120.0
                )

                if proc.returncode == 0:
                    return f"✓ LEAN 4: Proof verified successfully.\n{stdout.decode()}"
                else:
                    errors = stderr.decode()
                    return f"✗ LEAN 4: Verification failed.\n{errors[:2000]}"

        except asyncio.TimeoutError:
            return "✗ LEAN 4: Proof timed out (>120s). Try breaking into lemmas."
        except Exception as e:
            return f"Error Lean 4: {e}"

    def _find_lean(self) -> Optional[str]:
        """Locate Lean 4 binary."""
        import shutil
        for name in ("lean", "lean4", "lake"):
            path = shutil.which(name)
            if path:
                return path

        # Common elan locations
        for p in [
            Path.home() / ".elan" / "bin" / "lean",
            Path.home() / ".elan" / "bin" / "lean.exe",
        ]:
            if p.exists():
                return str(p)
        return None

    async def _simulate_lean(self, code: str) -> str:
        """LLM-assisted Lean verification when binary is not available."""
        return (
            "[LEAN 4 NOT INSTALLED]\n"
            "Para verificación formal completa, instala Lean 4:\n"
            "  curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh\n\n"
            f"Código recibido ({len(code)} chars):\n"
            f"```lean\n{code[:1000]}\n```\n\n"
            "Análisis estático del código:\n"
            + self._static_analyze(code)
        )

    def _static_analyze(self, code: str) -> str:
        """Basic static analysis of Lean code structure."""
        lines = []
        if "theorem" in code:
            theorems = re.findall(r"theorem\s+(\w+)", code)
            lines.append(f"• Teoremas encontrados: {', '.join(theorems)}")
        if "def" in code:
            defs = re.findall(r"def\s+(\w+)", code)
            lines.append(f"• Definiciones: {', '.join(defs)}")
        if "sorry" in code:
            lines.append("⚠️ Contiene 'sorry' — prueba incompleta")
        if "#check" in code:
            lines.append("• Usa #check para inspección de tipos")
        if not lines:
            lines.append("• Estructura no reconocida. Verifica la sintaxis Lean 4.")
        return "\n".join(lines)


class Z3VerifyTool(BaseTool):
    """
    Verificación de restricciones y satisfacibilidad usando Z3 SMT Solver.
    Acepta restricciones lógicas y devuelve SAT/UNSAT con modelo.
    Ejemplo: 'x > 0, x < 10, x*x == 49'
    """
    name = "z3_verify"

    async def run(self, constraints: str) -> str:
        try:
            from z3 import Solver, Int, Real, Bool, sat, unsat, parse_smt2_string

            solver = Solver()

            # Check if it's raw SMT-LIB2
            if constraints.strip().startswith("("):
                solver.add(parse_smt2_string(constraints))
            else:
                # Parse simple constraint format: comma-separated
                x = Int("x")
                y = Int("y")
                z = Int("z")
                namespace = {"x": x, "y": y, "z": z, "Int": Int, "Real": Real}

                for c in constraints.split(","):
                    c = c.strip()
                    if not c:
                        continue
                    try:
                        solver.add(eval(c, {"__builtins__": {}}, namespace))
                    except Exception as e:
                        return f"Error parsing constraint '{c}': {e}"

            result = solver.check()
            if result == sat:
                model = solver.model()
                vals = ", ".join(f"{d} = {model[d]}" for d in model)
                return f"✓ SAT (Satisfacible)\nModelo: {vals}"
            elif result == unsat:
                return "✗ UNSAT — No existe solución que satisfaga las restricciones."
            else:
                return "? UNKNOWN — Z3 no pudo determinar satisfacibilidad."

        except ImportError:
            return "[TOOL DEGRADED] z3-solver no instalado. pip install z3-solver"
        except Exception as e:
            return f"Error Z3: {e}"


class NumericalVerifyTool(BaseTool):
    """
    Verificación numérica con NumPy/SciPy.
    Evalúa expresiones numéricas, resuelve ecuaciones, analiza convergencia.
    Ejemplo: 'eigenvalues: [[1,2],[3,4]]' o 'roots: [1, -5, 6]'
    """
    name = "numerical_verify"

    async def run(self, expr: str) -> str:
        try:
            import numpy as np

            expr_lower = expr.strip().lower()

            if expr_lower.startswith("eigenvalues:"):
                raw = expr.split(":", 1)[1].strip()
                m = np.array(json.loads(raw), dtype=float)
                vals, vecs = np.linalg.eig(m)
                return (
                    f"✓ Eigenvalores: {vals}\n"
                    f"  Eigenvectores:\n{vecs}\n"
                    f"  Determinante: {np.linalg.det(m):.6f}\n"
                    f"  Condición: {np.linalg.cond(m):.4f}"
                )

            elif expr_lower.startswith("roots:"):
                raw = expr.split(":", 1)[1].strip()
                coeffs = json.loads(raw)
                roots = np.roots(coeffs)
                return f"✓ Raíces del polinomio: {roots}"

            elif expr_lower.startswith("svd:"):
                raw = expr.split(":", 1)[1].strip()
                m = np.array(json.loads(raw), dtype=float)
                U, S, Vt = np.linalg.svd(m)
                return f"✓ SVD:\n  Σ (valores singulares): {S}\n  Rango: {np.linalg.matrix_rank(m)}"

            elif expr_lower.startswith("eval:"):
                raw = expr.split(":", 1)[1].strip()
                result = eval(raw, {"__builtins__": {}, "np": np, "pi": np.pi, "e": np.e, "sqrt": np.sqrt, "sin": np.sin, "cos": np.cos, "log": np.log})
                return f"✓ Resultado: {result}"

            else:
                return (
                    "Comandos disponibles:\n"
                    "  eigenvalues: [[a,b],[c,d]]\n"
                    "  roots: [coeff_n, ..., coeff_0]\n"
                    "  svd: [[a,b],[c,d]]\n"
                    "  eval: np.sin(np.pi/4)"
                )

        except ImportError:
            return "[TOOL DEGRADED] NumPy no instalado. pip install numpy"
        except Exception as e:
            return f"Error numérico: {e}"


class CodeVerifyTool(BaseTool):
    """
    Verifica corrección de código usando análisis estático y pruebas formales.
    Acepta código Python y verifica tipos, invariantes, y pre/post-condiciones.
    Ejemplo: 'typecheck: def add(a: int, b: int) -> int: return a + b'
    """
    name = "code_verify"

    async def run(self, code: str) -> str:
        results = []

        code_lower = code.strip().lower()

        if code_lower.startswith("typecheck:"):
            raw = code.split(":", 1)[1].strip()
            results.append(await self._typecheck(raw))

        elif code_lower.startswith("invariant:"):
            raw = code.split(":", 1)[1].strip()
            results.append(await self._check_invariant(raw))

        else:
            # Run all checks
            results.append(await self._typecheck(code))
            results.append(await self._ast_analysis(code))

        return "\n".join(results)

    async def _typecheck(self, code: str) -> str:
        """Run mypy type checking."""
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                f.flush()

                proc = await asyncio.create_subprocess_exec(
                    "mypy", "--strict", f.name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
                output = stdout.decode()

                if proc.returncode == 0:
                    return "✓ Type-check: PASSED (mypy --strict)"
                else:
                    return f"✗ Type-check errors:\n{output[:1500]}"

        except FileNotFoundError:
            return "[SKIP] mypy no instalado. pip install mypy"
        except Exception as e:
            return f"Error typecheck: {e}"

    async def _check_invariant(self, spec: str) -> str:
        """Verify a simple pre/post-condition specification."""
        try:
            lines = spec.strip().split("\n")
            pre = post = body = ""
            for line in lines:
                if line.strip().startswith("pre:"):
                    pre = line.split(":", 1)[1].strip()
                elif line.strip().startswith("post:"):
                    post = line.split(":", 1)[1].strip()
                else:
                    body += line + "\n"

            return (
                f"Invariant Analysis:\n"
                f"  Pre-condition:  {pre or '(none)'}\n"
                f"  Post-condition: {post or '(none)'}\n"
                f"  Body: {len(body.strip().splitlines())} lines\n"
                f"  Status: Manual verification required (integrate with Z3 for automation)"
            )
        except Exception as e:
            return f"Error invariant check: {e}"

    async def _ast_analysis(self, code: str) -> str:
        """Basic AST complexity analysis."""
        import ast
        try:
            tree = ast.parse(code)
            funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            returns = [n for n in ast.walk(tree) if isinstance(n, ast.Return)]
            asserts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]

            return (
                f"✓ AST Analysis:\n"
                f"  Functions: {len(funcs)}\n"
                f"  Classes: {len(classes)}\n"
                f"  Return statements: {len(returns)}\n"
                f"  Assertions: {len(asserts)}\n"
                f"  Total nodes: {sum(1 for _ in ast.walk(tree))}"
            )
        except SyntaxError as e:
            return f"✗ Syntax Error: {e}"


# ---------------------------------------------------------------------------
# Available tool classes for the Agent Composer
# ---------------------------------------------------------------------------
MATH_TOOLS = {
    "sympy_verify": SymPyVerifyTool,
    "lean4_verify": Lean4VerifyTool,
    "z3_verify": Z3VerifyTool,
    "numerical_verify": NumericalVerifyTool,
    "code_verify": CodeVerifyTool,
    "file_read": FileReadTool,
    "file_write": FileWriteTool,
    "directory_list": DirectoryListTool,
}


# ---------------------------------------------------------------------------
# Math Verification Agent
# ---------------------------------------------------------------------------

class MathVerificationAgent(BaseAgent):
    """
    Agente de Verificación Formal y Matemáticas.

    Integra Lean 4, SymPy, Z3, y análisis numérico para verificación
    rigurosa de teoremas, pruebas, y corrección de código.
    """

    def __init__(
        self,
        name: str = "MathVerifier",
        config: Optional[AgentConfig] = None,
        llm_engine: Optional[Any] = None,
        enabled_tools: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            name=name,
            role="Formal Verification & Mathematical Proof Engine",
        )
        self.llm = llm_engine
        self.config = config

        # Register selected tools (or all by default)
        tool_keys = enabled_tools or list(MATH_TOOLS.keys())
        self.tools: Dict[str, BaseTool] = {}
        for key in tool_keys:
            if key in MATH_TOOLS:
                self.tools[key] = MATH_TOOLS[key]()

        self.system_prompt = (
            "Eres el Agente de Verificación Formal de TruthGPT. Tu misión es verificar "
            "rigurosamente afirmaciones matemáticas, probar teoremas, y validar la "
            "corrección de código usando herramientas formales.\n\n"
            "Siempre usa las herramientas para verificar antes de afirmar."
        )

        self.react_agent = MultiUserReActAgent(
            config=config or AgentConfig(llm_engine=llm_engine),
            llm_engine=llm_engine,
            custom_system_instructions=self.system_prompt,
        )

        # Register tools in ReAct agent
        for tool in self.tools.values():
            self.react_agent.register_tool(tool)

    async def process(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        logger.info("MathVerificationAgent processing: %s", query[:80])

        # Auto-detect verification type and route to appropriate tool
        result = await self._auto_route(query)

        if result:
            return AgentResponse(
                content=result,
                action_type="final_answer",
                metadata={"agent": self.name, "tools_used": list(self.tools.keys())},
            )

        # Fallback: use ReAct loop for reasoning + tool calls
        user_id = (context or {}).get("user_id", "math_verifier_default")
        return await self.react_agent.process_message(user_id, query)

        return AgentResponse(
            content=(
                f"Soy {self.name}. Puedo verificar:\n"
                "• Expresiones algebraicas (SymPy)\n"
                "• Teoremas formales (Lean 4)\n"
                "• Restricciones lógicas (Z3)\n"
                "• Análisis numérico (NumPy)\n"
                "• Corrección de código (mypy/AST)\n"
                "• Lectura de archivos locales (file_read)\n"
                "• Listado de directorios (directory_list)\n\n"
                "Ejemplo: 'file_read: C:\\path\\to\\code.py' o 'directory_list: ./'"
            ),
            action_type="final_answer",
        )

    async def _auto_route(self, query: str) -> Optional[str]:
        """Route to the right tool based on query patterns."""
        q = query.strip().lower()

        # SymPy patterns
        sympy_prefixes = (
            "simplify:", "solve:", "prove:", "limit:", "integrate:",
            "diff:", "derivative:", "factor:", "matrix:",
        )
        if any(q.startswith(p) for p in sympy_prefixes):
            if "sympy_verify" in self.tools:
                return await self.tools["sympy_verify"].run(query)

        # Lean patterns
        if any(kw in q for kw in ("theorem", "lemma", "def ", "#check", "#eval", "import mathlib")):
            if "lean4_verify" in self.tools:
                return await self.tools["lean4_verify"].run(query)

        # Z3 patterns
        if any(kw in q for kw in ("sat", "unsat", "constraint", "z3", "(declare")):
            if "z3_verify" in self.tools:
                return await self.tools["z3_verify"].run(query)

        # Numerical patterns
        if any(q.startswith(p) for p in ("eigenvalues:", "roots:", "svd:", "eval:")):
            if "numerical_verify" in self.tools:
                return await self.tools["numerical_verify"].run(query)

        # Code verification
        if any(kw in q for kw in ("typecheck:", "invariant:", "def ", "class ", "async def")):
            if "code_verify" in self.tools:
                return await self.tools["code_verify"].run(query)

        # File system routing
        if q.startswith("file_read:"):
            if "file_read" in self.tools:
                return await self.tools["file_read"].run(query.split(":", 1)[1].strip())
        
        if q.startswith("directory_list:"):
            if "directory_list" in self.tools:
                return await self.tools["directory_list"].run(query.split(":", 1)[1].strip())

        return None

    async def _llm_reasoning(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Use LLM to reason about the math problem and call tools."""
        prompt = f"{self.system_prompt}\n\nUsuario: {query}\n\nRazona paso a paso y usa las herramientas disponibles."

        try:
            response = await self.llm(prompt)
            return AgentResponse(
                content=response,
                action_type="final_answer",
                metadata={"agent": self.name, "method": "llm_reasoning"},
            )
        except Exception as e:
            logger.error("MathVerificationAgent LLM error: %s", e)
            return AgentResponse(
                content=f"Error en razonamiento matemático: {e}",
                action_type="error",
            )
