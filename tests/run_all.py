#!/usr/bin/env python3
import subprocess, sys

SCRIPTS = [
    "tests/test_00_config.py",
    "tests/test_01_market_batch_vix.py",
    "tests/test_02_discussion_rounds.py",
    "tests/test_03_trading_cycle_e2e.py",
]

def run(cmd):
    print("\n" + "="*80)
    print(f"$ {sys.executable} {cmd}")
    print("="*80)
    code = subprocess.call([sys.executable, cmd])
    if code not in (0, 2):
        print(f"[FAIL] {cmd} exited with {code}")
    return code

def main():
    overall = 0
    for c in SCRIPTS:
        code = run(c)
        overall = overall or code
    print("\n[RUN-ALL] Done.")
    sys.exit(overall)

if __name__ == "__main__":
    main()
