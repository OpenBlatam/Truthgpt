import sys
import os

from pathlib import Path

# Add project root and optimization core to path dynamically
curr_file = Path(__file__).resolve()
project_root = curr_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
opt_core = curr_file.parent.parent
if str(opt_core) not in sys.path:
    sys.path.insert(0, str(opt_core))


try:
    from optimization_core.learning.evolutionary_computing import example_evolutionary_computing
    
    print("✅ Successfully imported evolutionary_computing package")
    
    optimizer = example_evolutionary_computing()
    
    print("✅ Verification successful!")
except Exception as e:
    print("X Verification failed: " + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
