# Run Loop 500 错误调试指南

## 问题现象

前端调用 `POST /api/trading/run-loop` 返回 500 错误。

## 可能原因

### 1. `execute_daily_trade` 执行失败
- LLM 调用失败
- 数据获取失败
- 依赖缺失

### 2. 导入错误
- 模块路径问题
- 依赖未安装

### 3. 配置错误
- `config.json` 格式错误
- 股票清单为空

## 调试步骤

### 步骤 1: 查看后端日志

查看运行 API 的终端窗口，查找：
- `[Run Loop] 开始执行交易循环...`
- `[Run Loop] 异常: ...`
- `[Run Loop] Traceback: ...`

### 步骤 2: 检查常见错误

#### 错误 1: ModuleNotFoundError
```
ModuleNotFoundError: No module named 'xxx'
```
**解决**: 运行 `pip install -r backend/requirements.txt`

#### 错误 2: Ollama 连接失败
```
ConnectionError: Failed to connect to Ollama
```
**解决**: 确保 `ollama serve` 正在运行

#### 错误 3: 数据文件缺失
```
FileNotFoundError: portfolio_state.json
```
**解决**: 运行 `python backend/scripts/init_data.py`

### 步骤 3: 手动测试

```bash
cd backend
python -c "from src.orchestrator.trading_cycle import execute_daily_trade; print('Import OK')"
```

如果导入失败，检查 Python 路径和依赖。

### 步骤 4: 检查 API 响应

```bash
curl -X POST http://127.0.0.1:8000/api/trading/run-loop
```

查看返回的错误信息。

## 已添加的改进

### 1. 更详细的日志
- ✅ 添加 `[Run Loop]` 前缀日志
- ✅ 打印异常堆栈跟踪
- ✅ 记录错误响应内容

### 2. 更好的错误处理
- ✅ 允许同一天多次运行（用于测试）
- ✅ 返回详细的错误信息
- ✅ 前端显示错误提示

### 3. 前端错误显示
- ✅ 显示错误消息
- ✅ 记录到控制台
- ✅ 用户友好的提示

## 下一步

1. **重启 API** 以加载新的错误处理代码
2. **再次尝试** Run Loop
3. **查看后端日志** 获取详细错误信息
4. **根据错误信息** 修复问题

## 常见解决方案

### 如果看到 "ModuleNotFoundError"
```bash
cd backend
pip install -r requirements.txt
```

### 如果看到 "Ollama connection failed"
```bash
# 确保 Ollama 正在运行
ollama serve
```

### 如果看到 "Portfolio not initialized"
```bash
cd backend
python scripts/init_data.py
```

### 如果看到 "Config error"
检查 `backend/config/config.json` 格式是否正确。

