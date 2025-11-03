#!/usr/bin/env python3
"""
Run all important tests in the tests/ directory
"""
import subprocess, sys
from pathlib import Path

# Get tests directory
TESTS_DIR = Path(__file__).parent

SCRIPTS = [
    "test_00_config.py",              # Config validation
    "test_01_market_batch_vix.py",    # Market data fetching
    "test_02_discussion_rounds.py",   # Discussion rounds
    "test_03_trading_cycle_e2e.py",  # End-to-end trading cycle
    "test_04_discussion_tools.py",   # Discussion tools usage
    "test_05_full_trading_loop.py",  # Full trading loop with multi-stock portfolio
    "test_06_trading_loop.py",       # Minimal trading loop
    "test_07_all_agents.py",         # All agents validation
    "test_08_trading_cycle_agents.py",  # Trading cycle agents
    "test_09_tools_consolidated.py", # Consolidated tool tests
]

def run(test_file):
    """Run a test file from the tests/ directory"""
    print("\n" + "="*80)
    test_path = TESTS_DIR / test_file
    print(f"$ {sys.executable} {test_path}")
    print("="*80)
    
    # Change to backend directory to run tests
    import os
    backend_dir = TESTS_DIR.parent
    old_cwd = os.getcwd()
    try:
        os.chdir(backend_dir)
        code = subprocess.call([sys.executable, str(test_path)])
        if code not in (0, 2):
            print(f"[FAIL] {test_file} exited with {code}")
    finally:
        os.chdir(old_cwd)
    return code

def main():
    print("="*80)
    print(" RUNNING ALL TESTS")
    print("="*80)
    print(f"\nFound {len(SCRIPTS)} test files to run")
    
    overall = 0
    passed = 0
    failed = 0
    
    for test_file in SCRIPTS:
        test_path = TESTS_DIR / test_file
        if not test_path.exists():
            print(f"\n[SKIP] {test_file} - File not found")
            continue
        
        code = run(test_file)
        if code == 0:
            passed += 1
        else:
            failed += 1
        overall = overall or code
    
    print("\n" + "="*80)
    print(" TEST RUN SUMMARY")
    print("="*80)
    print(f"\nTotal: {len(SCRIPTS)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("\n[RUN-ALL] Done.")
    
    sys.exit(overall)

if __name__ == "__main__":
    main()
