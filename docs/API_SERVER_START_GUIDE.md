# API 服务器启动指南

## 问题

如果遇到 `ModuleNotFoundError: No module named 'src'` 错误，说明启动方式不正确。

## 正确的启动方式

### 方法 1: 从 backend 目录启动（推荐）

```bash
cd backend
python -m uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000
```

### 方法 2: 从项目根目录启动

```bash
# 在项目根目录
python -m uvicorn backend.src.api.server:app --reload --host 127.0.0.1 --port 8000
```

### 方法 3: 使用 PowerShell 脚本（最简单）

```powershell
# 在项目根目录运行
.\scripts\restart_api_server.ps1
```

## 验证服务器是否启动成功

1. **检查健康端点**：
   ```bash
   curl http://127.0.0.1:8000/api/health
   ```
   应该返回：`{"status":"ok"}`

2. **检查根端点**：
   ```bash
   curl http://127.0.0.1:8000/
   ```
   应该返回 API 信息和端点列表

3. **打开 API 文档**：
   浏览器访问：`http://127.0.0.1:8000/docs`

## 常见错误

### 错误 1: `ModuleNotFoundError: No module named 'src'`

**原因**：从项目根目录运行，但使用了 `src.api.server` 路径

**解决**：
- 方法 A：先 `cd backend`，然后运行
- 方法 B：使用 `backend.src.api.server` 路径

### 错误 2: `Address already in use`

**原因**：端口 8000 已被占用

**解决**：
```powershell
# 停止所有 Python 进程
.\scripts\stop_all_services_simple.ps1

# 或检查端口占用
Get-NetTCPConnection -LocalPort 8000
```

### 错误 3: `IndentationError`

**原因**：`server.py` 文件有缩进错误

**解决**：已修复，确保使用最新版本的 `server.py`

## 启动后的验证步骤

1. ✅ 服务器启动成功（看到 "Uvicorn running on..."）
2. ✅ `/api/health` 返回 200
3. ✅ `/api/agents/conversations` 返回数据
4. ✅ 前端可以正常连接

## 快速测试命令

```powershell
# 测试 API
python scripts/test_api_server.py

# 检查端点
python scripts/check_api_endpoints.py
```

