def generate_math_tests(func_code, func_name):
    test_template = f'''
import pytest, math
from {func_name} import {func_name}

def test_{func_name}_identity():
    assert math.isclose({func_name}(math.pi/4), expected, rel_tol=1e-9)

def test_{func_name}_boundary():
    with pytest.raises(ValueError):
        {func_name}(-1)  # domain check
'''
    write_file(f"test_{func_name}.py", test_template)