import ast
import sympy as sp
from typing import List, Dict, Any

def verify_python_math(source_code: str) -> Dict[str, Any]:
    """
    Perform static and symbolic math verification on a Python source string.
    Returns a report with detected issues.
    """
    tree = ast.parse(source_code)
    issues = []
    # Check for division-by-zero in BinOp
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            # Simple heuristic: if denominator is a constant zero or likely zero
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                issues.append({
                    "line": node.lineno,
                    "type": "division_by_zero",
                    "detail": "Literal 0 used as divisor"
                })
        # Check for math domain errors (e.g., sqrt with no guard)
        if isinstance(node, ast.Call) and hasattr(node.func, 'id') and node.func.id == 'sqrt':
            # If the argument is a variable without a >= 0 check (simplified)
            if len(node.args) == 1 and isinstance(node.args[0], ast.Name):
                issues.append({
                    "line": node.lineno,
                    "type": "domain_error",
                    "detail": f"sqrt({node.args[0].id}) used without explicit >0 guard"
                })

    # Symbolic verification with sympy (if expressions convertible)
    # Attempt to extract simple functions and verify identities
    try:
        local_env = {}
        exec(source_code, {"sp": sp, "__builtins__": {}}, local_env)
        for name, obj in local_env.items():
            if callable(obj) and not name.startswith('_'):
                # Test common mathematical identities
                try:
                    x = sp.Symbol('x')
                    # Example: Check sin^2(x) + cos^2(x) - 1
                    if name == 'my_func':  # placeholder
                        expr = obj(x)
                        simplified = sp.simplify(expr)
                        if simplified != expected:
                            issues.append({
                                "line": 0,
                                "type": "identity_mismatch",
                                "detail": f"{name} violates identity: {expr} != {expected}"
                            })
                except Exception:
                    pass
    except Exception as e:
        issues.append({"line": 0, "type": "exec_error", "detail": str(e)})

    return {
        "status": "clean" if not issues else "dirty",
        "issues": issues
    }

# Example usage:
# report = verify_python_math(open("output_code_architect_5.py").read())