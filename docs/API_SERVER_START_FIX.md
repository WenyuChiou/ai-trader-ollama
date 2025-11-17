# API 服务器启动错误修复

## 错误信息

```
ModuleNotFoundError: No module named 'src'
```

## 原因

从项目根目录运行 uvicorn，但 `src` 模块在 `backend` 目录下。

## 解决方案

### 方法 1: 使用重启脚本（推荐）

```powershell
.\scripts\restart_api_server.ps1
```

这个脚本会：
1. 停止所有现有的 uvicorn 进程
2. 切换到 `backend` 目录
3. 启动新的 API 服务器

### 方法 2: 手动启动

```powershell
cd backend
python -m uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000
```

### 方法 3: 从项目根目录运行（使用完整路径）

```powershell
python -m uvicorn backend.src.api.server:app --reload --host 127.0.0.1 --port 8000
```

## 验证

启动后，访问以下 URL 验证服务器是否正常运行：

- **API 根路径**: http://127.0.0.1:8000/
- **API 文档**: http://127.0.0.1:8000/docs
- **健康检查**: http://127.0.0.1:8000/api/health

## 注意事项

⚠️ **重要**: 必须从 `backend` 目录运行，或者使用完整路径 `backend.src.api.server:app`

✅ **推荐**: 使用 `.\scripts\restart_api_server.ps1` 脚本，它会自动处理所有步骤

