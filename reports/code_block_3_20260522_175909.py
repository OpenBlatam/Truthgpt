def verify_math_in_file(filepath):
    tree = ast.parse(read_file(filepath))
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and is_potential_division_by_zero(node):
            issues.append({"type": "division_by_zero", "line": node.lineno})
        # add symbolic checks using sympy when possible
    return {"file": filepath, "issues": issues, "status": "clean" if not issues else "dirty"}