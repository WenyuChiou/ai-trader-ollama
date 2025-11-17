#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 API 服务器是否正常运行
"""
import sys
import io
import requests
import time

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except AttributeError:
        # 如果已经是 TextIOWrapper，跳过
        pass

API_BASE = "http://127.0.0.1:8000"

def test_health_endpoint():
    """测试 /api/health 端点"""
    try:
        print(f"[测试] 检查 {API_BASE}/api/health ...")
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ /api/health 端点正常: {response.json()}")
            return True
        else:
            print(f"❌ /api/health 返回状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到 {API_BASE}")
        print("   提示: 请确保后端服务器正在运行")
        print("   启动命令: cd backend && uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_root_endpoint():
    """测试根端点"""
    try:
        print(f"\n[测试] 检查 {API_BASE}/ ...")
        response = requests.get(f"{API_BASE}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ 根端点正常: {response.json()}")
            return True
        else:
            print(f"❌ 根端点返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_conversations_endpoint():
    """测试 /api/agents/conversations 端点"""
    try:
        print(f"\n[测试] 检查 {API_BASE}/api/agents/conversations ...")
        response = requests.get(f"{API_BASE}/api/agents/conversations?limit=10", timeout=10)
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            print(f"✅ /api/agents/conversations 端点正常: 找到 {count} 条对话")
            return True
        else:
            print(f"❌ /api/agents/conversations 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("API 服务器连接测试")
    print("=" * 50)
    print()
    
    # 等待一下，确保服务器有时间启动
    time.sleep(1)
    
    results = []
    results.append(("健康检查", test_health_endpoint()))
    results.append(("根端点", test_root_endpoint()))
    results.append(("对话端点", test_conversations_endpoint()))
    
    print()
    print("=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✅ 所有测试通过！服务器运行正常。")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败。请检查服务器是否正常运行。")
        sys.exit(1)

