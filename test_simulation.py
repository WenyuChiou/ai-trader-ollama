#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试10月模拟功能"""
import sys
import io
import requests
import json
import time

# 强制 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("测试10月模拟功能")
print("=" * 60)
print()

# 1. 检查API服务器
print("[1] 检查API服务器...")
try:
    r = requests.get(f"{API_BASE}/", timeout=3)
    if r.status_code == 200:
        print(f"  ✅ API服务器正常 (版本: {r.json().get('version', 'Unknown')})")
    else:
        print(f"  ❌ API服务器返回错误: {r.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ API服务器无法连接: {e}")
    print("  ⚠️  请确保API服务器正在运行")
    sys.exit(1)

print()

# 2. 检查模拟状态
print("[2] 检查当前模拟状态...")
try:
    r = requests.get(f"{API_BASE}/api/trading/simulate-status", timeout=3)
    if r.status_code == 200:
        status = r.json().get("status", {})
        running = status.get("running", False)
        print(f"  运行中: {running}")
        if running:
            print(f"  当前天数: {status.get('current_day', 0)}/{status.get('total_days', 0)}")
            print("  先停止模拟...")
            r2 = requests.post(f"{API_BASE}/api/trading/stop-simulation", timeout=3)
            if r2.status_code == 200:
                print("  ✅ 模拟已停止")
                time.sleep(1)
            else:
                print(f"  ⚠️  停止模拟失败: {r2.status_code}")
        else:
            print("  ✅ 模拟未运行，可以启动")
    else:
        print(f"  ❌ 无法获取模拟状态: {r.status_code}")
except Exception as e:
    print(f"  ⚠️  检查状态失败: {e}")

print()

# 3. 启动模拟
print("[3] 启动10月模拟...")
try:
    r = requests.post(f"{API_BASE}/api/trading/simulate-october", json={}, timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"  ✅ 模拟启动成功")
        print(f"  消息: {data.get('message', 'N/A')}")
        if "simulation_status" in data:
            status = data["simulation_status"]
            print(f"  状态: running={status.get('running')}, started_at={status.get('started_at')}")
    elif r.status_code == 400:
        data = r.json()
        print(f"  ❌ 启动失败: {data.get('error', 'Unknown error')}")
        print("  可能原因: 模拟已在运行中")
    else:
        print(f"  ❌ 启动失败: HTTP {r.status_code}")
        print(f"  响应: {r.text[:200]}")
except Exception as e:
    print(f"  ❌ 启动模拟异常: {e}")

print()

# 4. 等待并检查进度
print("[4] 等待5秒后检查模拟进度...")
time.sleep(5)
try:
    r = requests.get(f"{API_BASE}/api/trading/simulate-status", timeout=3)
    if r.status_code == 200:
        status = r.json().get("status", {})
        print(f"  运行中: {status.get('running', False)}")
        print(f"  当前天数: {status.get('current_day', 0)}/{status.get('total_days', 0)}")
        print(f"  开始时间: {status.get('started_at', 'N/A')}")
        if status.get('error'):
            print(f"  错误: {status.get('error')}")
except Exception as e:
    print(f"  ⚠️  检查进度失败: {e}")

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
print()
print("下一步:")
print("1. 刷新浏览器页面查看模拟进度")
print("2. 检查浏览器控制台是否有错误")
print("3. 查看对话和净值是否正常更新")

