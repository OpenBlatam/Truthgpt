def auto_heal(filepath, issues):
    if issues:
        # re‑invoke code_architect with error context
        refined_prompt = f"Fix math errors in {filepath}: {issues}"
        corrected_code = call_llm(refined_prompt)
        add_regression_test(issues)
        write_file(filepath, corrected_code)