#!/usr/bin/env python3
"""Check syntax of all main Python files"""
import py_compile
import sys
import os
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Get project root
project_root = Path(__file__).parent.parent
backend_src = project_root / "backend" / "src"

# Main files to check
main_files = [
    "orchestrator/trading_cycle.py",
    "agents/multi_analyst_system.py",
    "agents/multi_analyst_system_parallel.py",
    "agents/trader_agent.py",
    "api/server.py",
    "agents/analysts/market_analyst_handler.py",
    "agents/analysts/technical_analyst_handler.py",
    "agents/analysts/fundamental_analyst_handler.py",
    "agents/analysts/sentiment_analyst_handler.py",
    "agents/risk_analyst_llm.py",
]

errors = []
for rel_path in main_files:
    file_path = backend_src / rel_path
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        continue
    try:
        py_compile.compile(str(file_path), doraise=True)
        print(f"[OK] {rel_path}")
    except py_compile.PyCompileError as e:
        error_msg = f"[ERROR] {rel_path}: {e}"
        print(error_msg)
        errors.append(error_msg)
    except Exception as e:
        error_msg = f"[ERROR] {rel_path}: {e}"
        print(error_msg)
        errors.append(error_msg)

if errors:
    print(f"\n[FAILED] Found {len(errors)} syntax errors!")
    sys.exit(1)
else:
    print(f"\n[SUCCESS] All {len(main_files)} files compiled successfully!")
    sys.exit(0)

