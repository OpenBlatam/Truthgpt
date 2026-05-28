import ast, sympy as sp

def verify_file(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read())
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            if not has_zero_guard(node.right):
                issues.append({"line": node.lineno, "type": "division_by_zero"})
        # add symbolic checks (simplify expression vs reference)
    status = "clean" if not issues else "dirty"
    return {"file": filepath, "issues": issues, "status": status}

def has_zero_guard(expr_node):
    # simple check for 'if denom != 0'
    return False  # placeholder