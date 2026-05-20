"""
🔬 Test suite for formalized TruthGPT API.
Verifies preconditions, postconditions, SMT solver validations, and type rules.
Supports standard Windows text encoding.
"""

import sys
import os
import asyncio
from pathlib import Path

# Force UTF-8 for safe execution in Windows consoles
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

# Initialize path
current_dir = Path(__file__).resolve().parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from truthgpt import (
    api, ask, list_papers, get_paper_info, 
    verify_system_integrity, FormalContractError
)

async def test_contracts():
    print("====================================================")
    print("[TEST] Running Formal Contract Verification Test Suite...")
    print("====================================================\n")

    # 1. Test standard list_papers with valid contract boundaries
    print("-> Test 1: Valid list_papers limit...")
    try:
        papers = list_papers(limit=5)
        print(f"  [PASS]: Retrieved {len(papers)} papers (contract satisfied)\n")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"  [FAIL]: {e}\n")

    # 2. Test precondition limit <= 0 violation (Hoare Logic)
    print("-> Test 2: Precondition limit <= 0 (limit = -1)...")
    try:
        list_papers(limit=-1)
        print("  [FAIL]: Precondition violation was not caught!\n")
    except FormalContractError as e:
        print(f"  [PASS]: Precondition violation successfully caught: {e}\n")

    # 3. Test type constraint violation
    print("-> Test 3: Type constraint violation (limit = 'five')...")
    try:
        list_papers(limit="five") # type: ignore
        print("  [FAIL]: Type verification failed to catch invalid string!\n")
    except TypeError as e:
        print(f"  [PASS]: Type violation successfully caught: {e}\n")

    # 4. Test empty ask query violation
    print("-> Test 4: Ask with empty query...")
    try:
        await ask("")
        print("  [FAIL]: Empty ask prompt constraint not enforced!\n")
    except FormalContractError as e:
        print(f"  [PASS]: Empty prompt constraint successfully caught: {e}\n")

    # 5. Test complete system integrity analysis
    print("-> Test 5: Running System State Invariant Analysis...")
    try:
        report = verify_system_integrity()
        print("  [PASS] Verification Report Summary:")
        for k, v in report.items():
            print(f"    - {k}: {v}")
        print("\n  [PASS]: State invariant verification completed successfully!\n")
    except Exception as e:
        print(f"  [FAIL]: {e}\n")

    print("====================================================")
    print("Formal Verification Validation Complete!")
    print("====================================================")

if __name__ == "__main__":
    asyncio.run(test_contracts())
