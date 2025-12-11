# Full Stack Test Guide
**前后端完整测试指南**

## 测试步骤

### 方法 1: 使用自动化测试脚本（推荐）

1. **运行完整测试脚本**：
   ```batch
   scripts\test_full_stack.bat
   ```
   
   这个脚本会：
   - 检查后端是否运行
   - 如果没有运行，自动启动后端
   - 测试所有 API 端点
   - 检查前端文件
   - 在浏览器中打开前端

### 方法 2: 手动测试

#### 步骤 1: 启动后端

**使用 BAT 文件启动**（推荐）：
```batch
scripts\start_backend_auto.bat
```

这个 BAT 文件会：
- 检查 Python 环境
- 创建/激活虚拟环境
- 安装依赖（如果需要）
- 检查端口 8000
- 启动 FastAPI 服务器

**预期输出**：
```
========================================
AI Trader - Backend Auto Start
========================================

[1/6] Checking Python...
Python 3.x.x

[2/6] Checking virtual environment...
Virtual environment found

[3/6] Activating virtual environment...
Virtual environment activated

[4/6] Checking dependencies...
Dependencies already installed

[5/6] Checking port 8000...
Port 8000 is available

[6/6] Starting API server...
========================================
API Server starting on port 8000
API Documentation: http://localhost:8000/docs
Health Check: http://localhost:8000/api/health

Press Ctrl+C to stop the server
========================================
```

#### 步骤 2: 验证后端运行

**方法 A: 使用测试脚本**
```batch
python scripts\test_backend_api.py
```

**方法 B: 手动测试**
```batch
curl http://localhost:8000/api/health
```

或者打开浏览器访问：
- http://localhost:8000/api/health
- http://localhost:8000/docs (API 文档)

#### 步骤 3: 打开前端

**方法 A: 使用测试脚本**
```batch
scripts\test_full_stack.bat
```
脚本会自动在浏览器中打开前端。

**方法 B: 手动打开**
1. 打开文件浏览器
2. 导航到项目根目录
3. 打开 `frontend\monitor.html`

或者直接在浏览器地址栏输入：
```
file:///C:/Users/wenyu/Desktop/investment/LLM AI trader/ai-trader-ollama/frontend/monitor.html
```

#### 步骤 4: 验证前后端连接

在前端页面中：
1. 检查浏览器控制台（F12）是否有错误
2. 查看前端是否能加载数据
3. 测试各个功能按钮

## 测试检查清单

### 后端测试
- [ ] 后端成功启动（端口 8000）
- [ ] Health check 返回 200 OK
- [ ] API 文档可以访问（/docs）
- [ ] Market status API 正常工作
- [ ] System info API 正常工作

### 前端测试
- [ ] 前端页面可以打开
- [ ] 前端能连接到后端 API
- [ ] 没有 CORS 错误
- [ ] 数据能正确显示
- [ ] 实时更新功能正常

### 集成测试
- [ ] 前端可以获取市场状态
- [ ] 前端可以获取投资组合数据
- [ ] 前端可以获取交易历史
- [ ] 前端可以获取 agent 对话记录

## 常见问题

### 问题 1: 端口 8000 已被占用

**解决方案**：
```batch
# 查看占用端口的进程
netstat -ano | findstr ":8000"

# 停止进程（替换 PID 为实际进程 ID）
taskkill /F /PID <PID>
```

或者使用 BAT 文件，它会自动处理端口冲突。

### 问题 2: 前端无法连接到后端

**检查**：
1. 后端是否正在运行
2. `frontend/config.js` 中的 API URL 是否正确
3. 浏览器控制台是否有 CORS 错误

**解决方案**：
- 确保后端运行在 `http://localhost:8000`
- 检查 `config.js` 中的 `development` 配置

### 问题 3: 虚拟环境问题

**解决方案**：
```batch
# 重新创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate.bat

# 安装依赖
pip install -r backend\requirements.txt
```

## 测试结果示例

### 成功的测试输出

```
========================================
Full Stack Integration Test
========================================

[1/5] Checking if backend is already running...
Port 8000 is available

[2/5] Starting backend server...
Starting backend in background window...
Waiting for backend to start (30 seconds max)...
Backend is ready!

[3/5] Testing backend API endpoints...
Health Check: OK
Market Status: OK
Root Endpoint: OK

[4/5] Checking frontend files...
[OK] monitor.html exists
[OK] index.html exists
[OK] config.js exists

[5/5] Opening frontend in browser...
Backend URL: http://localhost:8000
Frontend URL: file:///.../frontend/monitor.html

========================================
Test Summary
========================================

Backend Status: Running on http://localhost:8000
Frontend: Opened in browser

Test completed!
```

## 下一步

测试完成后，你可以：
1. 运行完整的 agent discussion 测试
2. 执行实际的交易周期
3. 查看实时监控面板

---

**最后更新**: 2025-12-11

