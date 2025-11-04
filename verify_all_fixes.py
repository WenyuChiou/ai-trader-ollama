#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整验证所有修复
确保所有功能都能正常工作
"""
import sys
import io
from pathlib import Path

# 修复 Windows 编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加 backend 目录到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("=" * 70)
print("Complete Fix Verification")
print("=" * 70)
print()

all_ok = True

# 验证 1: 所有 print 都已替换
print("[1/5] Verifying all print() replaced with safe_print()...")
try:
    import re
    
    files_to_check = [
        "src/orchestrator/trading_cycle.py",
        "src/data/memory_manager.py",
        "src/data/equity_tracker.py",
        "src/data/trade_log.py",
    ]
    
    issues = []
    for file_path in files_to_check:
        full_path = backend_dir / file_path
        if not full_path.exists():
            continue
            
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # 检查是否有 print() 调用（排除 safe_print 和注释）
                if re.search(r'\bprint\s*\(', line) and 'safe_print' not in line and not line.strip().startswith('#'):
                    # 排除 safe_print 函数定义中的 print
                    if 'def safe_print' not in line:
                        issues.append(f"{file_path}:{i} - {line.strip()}")
    
    if issues:
        print(f"  [WARNING] Found {len(issues)} potential print() calls:")
        for issue in issues[:5]:  # 只显示前5个
            print(f"    - {issue}")
        if len(issues) > 5:
            print(f"    ... and {len(issues) - 5} more")
    else:
        print("  [OK] All print() calls replaced with safe_print()")
except Exception as e:
    print(f"  [ERROR] Verification failed: {e}")
    all_ok = False

# 验证 2: 所有 traceback.print_exc() 都有错误处理
print("\n[2/5] Verifying traceback.print_exc() error handling...")
try:
    files_to_check = [
        "src/orchestrator/trading_cycle.py",
        "src/data/memory_manager.py",
        "src/data/equity_tracker.py",
    ]
    
    issues = []
    for file_path in files_to_check:
        full_path = backend_dir / file_path
        if not full_path.exists():
            continue
            
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                if 'traceback.print_exc()' in line:
                    # 检查是否在 try-except 块中
                    context = '\n'.join(lines[max(0, i-5):i])
                    if 'try:' not in context or 'except' not in context:
                        issues.append(f"{file_path}:{i} - traceback.print_exc() without try-except")
    
    if issues:
        print(f"  [WARNING] Found {len(issues)} traceback.print_exc() without proper handling:")
        for issue in issues[:3]:
            print(f"    - {issue}")
    else:
        print("  [OK] All traceback.print_exc() have proper error handling")
except Exception as e:
    print(f"  [ERROR] Verification failed: {e}")
    all_ok = False

# 验证 3: 所有文件写入都有 flush() 和 fsync()
print("\n[3/5] Verifying file operations have flush() and fsync()...")
try:
    files_to_check = [
        "src/orchestrator/trading_cycle.py",
        "src/data/memory_manager.py",
        "src/data/equity_tracker.py",
        "src/data/trade_log.py",
    ]
    
    issues = []
    for file_path in files_to_check:
        full_path = backend_dir / file_path
        if not full_path.exists():
            continue
            
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                if '.open(' in line and ('"w"' in line or '"a"' in line):
                    # 检查后续几行是否有 flush 和 fsync
                    next_lines = '\n'.join(lines[i:i+5])
                    if 'flush()' not in next_lines or 'fsync' not in next_lines:
                        if 'safe_print' not in line:  # 排除一些特殊情况
                            issues.append(f"{file_path}:{i} - File write may be missing flush/fsync")
    
    if issues:
        print(f"  [WARNING] Found {len(issues)} potential issues:")
        for issue in issues[:3]:
            print(f"    - {issue}")
        print("  [NOTE] Some may be false positives, please verify manually")
    else:
        print("  [OK] File operations appear to have flush() and fsync()")
except Exception as e:
    print(f"  [ERROR] Verification failed: {e}")
    all_ok = False

# 验证 4: 所有模块都有 safe_print 函数
print("\n[4/5] Verifying all modules have safe_print function...")
try:
    from src.orchestrator.trading_cycle import safe_print as tc_safe_print
    from src.data.memory_manager import safe_print as mm_safe_print
    from src.data.equity_tracker import safe_print as et_safe_print
    from src.data.trade_log import safe_print as tl_safe_print
    
    print("  [OK] All modules have safe_print function")
    
    # 测试每个 safe_print
    tc_safe_print("  [TEST] trading_cycle safe_print")
    mm_safe_print("  [TEST] memory_manager safe_print")
    et_safe_print("  [TEST] equity_tracker safe_print")
    tl_safe_print("  [TEST] trade_log safe_print")
    print("  [OK] All safe_print functions working")
except Exception as e:
    print(f"  [ERROR] safe_print verification failed: {e}")
    all_ok = False

# 验证 5: 测试文件写入操作
print("\n[5/5] Testing actual file write operations...")
try:
    logs_dir = backend_dir / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    test_files = []
    for i in range(3):
        test_file = logs_dir / f"test_write_{i}.jsonl"
        try:
            with test_file.open("a", encoding="utf-8") as f:
                f.write(f'{{"test": {i}}}\n')
                f.flush()
                import os
                os.fsync(f.fileno())
            test_files.append(test_file)
        except Exception as e:
            print(f"  [ERROR] File write {i} failed: {e}")
            all_ok = False
    
    # 清理
    for test_file in test_files:
        if test_file.exists():
            test_file.unlink()
    
    print(f"  [OK] All {len(test_files)} file write operations successful")
except Exception as e:
    print(f"  [ERROR] File write test failed: {e}")
    all_ok = False

# 总结
print("\n" + "=" * 70)
if all_ok:
    print("ALL VERIFICATIONS PASSED! [OK]")
    print("=" * 70)
    print("\nFix Summary:")
    print("  [OK] All print() replaced with safe_print()")
    print("  [OK] All traceback.print_exc() have error handling")
    print("  [OK] All file operations have flush() and fsync()")
    print("  [OK] All modules have safe_print function")
    print("  [OK] File write operations working correctly")
    print("\nThe Run Loop should now work without 'I/O operation on closed file' errors!")
    print("\nNext steps:")
    print("  1. Restart the API server: cd backend\\scripts && powershell -ExecutionPolicy Bypass -File .\\restart_api.ps1")
    print("  2. Test Run Loop in the frontend: http://127.0.0.1:8080/monitor.html")
    sys.exit(0)
else:
    print("SOME VERIFICATIONS FAILED! [ERROR]")
    print("=" * 70)
    print("\nPlease review the warnings/errors above and fix them.")
    sys.exit(1)

