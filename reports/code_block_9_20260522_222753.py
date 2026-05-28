{
  "audit_report": {
    "total_files": 3,
    "results": [
      {
        "file": "output_system_agent_7_1779472952.py",
        "status": "clean",
        "issues": []
      },
      {
        "file": "output_code_architect_5_1779473342.py",
        "status": "dirty",
        "issues": [
          {"line": 42, "type": "domain_error", "detail": "sqrt(x) used without guard"},
          {"line": 55, "type": "division_by_zero", "detail": "Literal 0 divisor in density = mass / 0"}
        ]
      },
      {
        "file": "output_math_verifier_6_1779473026.py",
        "status": "dirty",
        "issues": [
          {"line": 78, "type": "domain_error", "detail": "log(1e-20) results in -inf without clamping"}
        ]
      }
    ],
    "error_density": 0.67,
    "recommended_actions": ["Add input validation", "Replace constant zero divisor", "Add domain checks for sqrt and log"]
  }
}