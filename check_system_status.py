#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查系统状态：后端API、前端、测试脚本
"""
import sys
import io
import requests
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_backend_api():
    """检查后端API"""
    print("\n[1/4] 检查后端API...")
    try:
        r = requests.get('http://127.0.0.1:8000/api/system/info', timeout=2)
        if r.status_code == 200:
            data = r.json()
            llm_model = data.get('llm', {}).get('default_model', 'Unknown')
            print(f"  ✓ 后端API运行中 (端口 8000)")
            print(f"    LLM模型: {llm_model}")
            return True
        else:
            print(f"  ✗ 后端API返回错误: {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ✗ 后端API未运行")
        print("    请启动: cd backend\\scripts && .\\start_api_background.ps1")
        return False
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return False

def check_frontend():
    """检查前端服务器"""
    print("\n[2/4] 检查前端服务器...")
    try:
        r = requests.get('http://localhost:8080/monitor.html', timeout=2)
        if r.status_code == 200:
            print("  ✓ 前端服务器运行中 (端口 8080)")
            print("    访问: http://localhost:8080/monitor.html")
            return True
        else:
            print(f"  ✗ 前端服务器返回错误: {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ✗ 前端服务器未运行")
        print("    请启动: cd frontend && python -m http.server 8080")
        return False
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return False

def check_test_script():
    """检查测试脚本"""
    print("\n[3/4] 检查测试脚本...")
    script_path = Path("backend/scripts/simulate_october_history.py")
    if script_path.exists():
        print(f"  ✓ 测试脚本存在: {script_path}")
        
        # 检查依赖
        backend_dir = Path("backend")
        if backend_dir.exists():
            sys.path.insert(0, str(backend_dir.absolute()))
            try:
                from src.orchestrator.trading_cycle import execute_daily_trade
                print("  ✓ 依赖模块可以导入")
                return True
            except ImportError as e:
                print(f"  ✗ 依赖模块导入失败: {e}")
                return False
        else:
            print("  ✗ backend目录不存在")
            return False
    else:
        print(f"  ✗ 测试脚本不存在: {script_path}")
        return False

def check_logs_directory():
    """检查日志目录"""
    print("\n[4/4] 检查日志目录...")
    logs_dir = Path("backend/data/logs")
    if logs_dir.exists():
        print(f"  ✓ 日志目录存在: {logs_dir.absolute()}")
        
        # 检查关键文件
        convo_file = logs_dir / "discussion_actions.jsonl"
        portfolio_file = logs_dir / "portfolio_state.json"
        
        print(f"    对话文件: {'存在' if convo_file.exists() else '不存在'}")
        print(f"    组合文件: {'存在' if portfolio_file.exists() else '不存在'}")
        
        if convo_file.exists():
            with convo_file.open('r', encoding='utf-8') as f:
                lines = [l for l in f if l.strip()]
                print(f"    对话记录: {len(lines)} 条")
        
        return True
    else:
        print(f"  ✗ 日志目录不存在: {logs_dir}")
        print("    将在首次运行时自动创建")
        return True  # 这不是错误，会自动创建

def main():
    print("=" * 60)
    print("  系统状态检查")
    print("=" * 60)
    
    results = {
        "backend": check_backend_api(),
        "frontend": check_frontend(),
        "test_script": check_test_script(),
        "logs": check_logs_directory()
    }
    
    print("\n" + "=" * 60)
    print("  检查总结")
    print("=" * 60)
    
    all_ok = all(results.values())
    
    if results["backend"]:
        print("  ✓ 后端API: 运行中")
    else:
        print("  ✗ 后端API: 未运行")
    
    if results["frontend"]:
        print("  ✓ 前端服务器: 运行中")
    else:
        print("  ✗ 前端服务器: 未运行")
    
    if results["test_script"]:
        print("  ✓ 测试脚本: 就绪")
    else:
        print("  ✗ 测试脚本: 不可用")
    
    if results["logs"]:
        print("  ✓ 日志目录: 就绪")
    else:
        print("  ✗ 日志目录: 有问题")
    
    print()
    
    if all_ok:
        print("  ✓ 所有组件就绪！可以开始测试")
        print("\n  运行测试:")
        print("    cd backend")
        print("    python scripts/simulate_october_history.py")
    else:
        print("  ⚠️  部分组件未就绪")
        print("\n  需要启动的组件:")
        if not results["backend"]:
            print("    - 后端API: cd backend\\scripts && .\\start_api_background.ps1")
        if not results["frontend"]:
            print("    - 前端服务器: cd frontend && python -m http.server 8080")
    
    print()

if __name__ == "__main__":
    main()

