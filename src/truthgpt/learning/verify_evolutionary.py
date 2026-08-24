import sys
import os
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Add project root and src to path
curr_dir = Path(__file__).resolve().parent
src_dir = curr_dir.parent
root_dir = src_dir.parent

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def verify():
    try:
        from truthgpt.learning.evolutionary_computing import example_evolutionary_computing
        print("✅ Successfully imported evolutionary_computing package")
        optimizer = example_evolutionary_computing()
        print("✅ Verification successful!")
        return True
    except Exception as e:
        print("❌ Verification failed: " + str(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify()
    if not success:
        sys.exit(1)
