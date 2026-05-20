import sys
import os

# Add project root to path
project_root = os.path.abspath("c:/blatam-academy/agents/backend/onyx/server/features/Frontier-Model-run/scripts/TruthGPT-main")
if project_root not in sys.path:
    sys.path.append(project_root)
    
# Also add optimization_core to path to resolve absolute imports within it if necessary
opt_core_path = os.path.join(project_root, "optimization_core")
if opt_core_path not in sys.path:
    sys.path.append(opt_core_path)

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
