#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 API 端点是否完整
对比前端调用的端点和后端实现的端点
"""
import sys
import io
import re
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def extract_backend_endpoints():
    """从 server.py 提取所有端点"""
    server_file = Path(__file__).parent.parent / "backend" / "src" / "api" / "server.py"
    
    if not server_file.exists():
        print(f"❌ 找不到 server.py: {server_file}")
        return set()
    
    endpoints = set()
    with server_file.open('r', encoding='utf-8') as f:
        content = f.read()
        # 匹配 @app.get("/path") 或 @app.post("/path")
        pattern = r'@app\.(get|post|put|delete)\(["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)
        for method, path in matches:
            endpoints.add(f"{method.upper()} {path}")
    
    return endpoints

def extract_frontend_endpoints():
    """从 monitor.html 提取所有调用的 API 端点"""
    frontend_file = Path(__file__).parent.parent / "frontend" / "monitor.html"
    
    if not frontend_file.exists():
        print(f"❌ 找不到 monitor.html: {frontend_file}")
        return set()
    
    endpoints = set()
    with frontend_file.open('r', encoding='utf-8') as f:
        content = f.read()
        # 匹配 fetch(`${getApiBase()}/api/...`) 或类似模式
        patterns = [
            r'fetch\([^`]*`[^`]*\/api\/([^`\?\'"]+)',
            r'["\']\/api\/([^"\'\?]+)',
            r'getApiBase\(\)\s*\+\s*["\']\/api\/([^"\'\?]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # 清理路径（移除查询参数等）
                path = match.split('?')[0].split("'")[0].split('"')[0].strip()
                if path:
                    # 尝试推断 HTTP 方法
                    method = "GET"  # 默认
                    if 'POST' in content[max(0, content.find(match)-100):content.find(match)]:
                        method = "POST"
                    elif 'PUT' in content[max(0, content.find(match)-100):content.find(match)]:
                        method = "PUT"
                    elif 'DELETE' in content[max(0, content.find(match)-100):content.find(match)]:
                        method = "DELETE"
                    
                    endpoints.add(f"{method} /api/{path}")
    
    return endpoints

def main():
    print("=" * 60)
    print("API 端点检查")
    print("=" * 60)
    print()
    
    # 提取端点
    print("正在提取端点...")
    backend_endpoints = extract_backend_endpoints()
    frontend_endpoints = extract_frontend_endpoints()
    
    print(f"后端实现的端点: {len(backend_endpoints)}")
    print(f"前端调用的端点: {len(frontend_endpoints)}")
    print()
    
    # 显示后端端点
    print("=" * 60)
    print("后端实现的端点:")
    print("=" * 60)
    for endpoint in sorted(backend_endpoints):
        print(f"  ✅ {endpoint}")
    print()
    
    # 显示前端端点
    print("=" * 60)
    print("前端调用的端点:")
    print("=" * 60)
    for endpoint in sorted(frontend_endpoints):
        print(f"  📱 {endpoint}")
    print()
    
    # 检查缺失的端点
    print("=" * 60)
    print("缺失的端点（前端调用但后端未实现）:")
    print("=" * 60)
    missing = frontend_endpoints - backend_endpoints
    if missing:
        for endpoint in sorted(missing):
            print(f"  ❌ {endpoint}")
    else:
        print("  ✅ 所有前端调用的端点都已实现")
    print()
    
    # 检查未使用的端点
    print("=" * 60)
    print("未使用的端点（后端实现但前端未调用）:")
    print("=" * 60)
    unused = backend_endpoints - frontend_endpoints
    if unused:
        for endpoint in sorted(unused):
            print(f"  ⚠️  {endpoint}")
    else:
        print("  ✅ 所有后端端点都被使用")
    print()
    
    # 总结
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print(f"后端端点数: {len(backend_endpoints)}")
    print(f"前端端点数: {len(frontend_endpoints)}")
    print(f"缺失端点数: {len(missing)}")
    print(f"未使用端点数: {len(unused)}")
    
    if missing:
        print("\n⚠️  需要添加以下端点:")
        for endpoint in sorted(missing):
            print(f"   - {endpoint}")
        return 1
    else:
        print("\n✅ 所有必需的端点都已实现！")
        return 0

if __name__ == "__main__":
    sys.exit(main())

