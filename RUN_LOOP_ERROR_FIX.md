# Run Loop 500 错误修复指南

## 问题确认

**是的，`run-loop` 返回 500 错误会导致对话无法生成！**

原因：
1. `run-loop` 调用 `execute_daily_trade()`
2. `execute_daily_trade()` 生成对话并写入 `discussion_actions.jsonl`
3. 如果 `run-loop` 失败，`execute_daily_trade()` 不会执行
4. 因此对话文件为空，前端无法显示对话

## 诊断步骤

### 步骤 1: 运行诊断工具

```powershell
cd backend
python diagnose_run_loop_error.py
```

这个工具会检查：
- ✅ 模块导入是否正常
- ✅ 配置文件是否存在
- ✅ 投资组合状态文件是否存在
- ✅ Ollama 是否连接
- ✅ 能否执行交易循环

### 步骤 2: 查看后端 API 日志

**查看运行 API 的终端窗口**，查找以下日志：

```
[Run Loop] 开始执行交易循环...
[Run Loop] execute_trading_cycle 返回类型: ...
[Run Loop] 异常: ...
[Run Loop] Traceback: ...
```

这些日志会显示具体的错误原因。

### 步骤 3: 检查常见错误

#### 错误 1: ModuleNotFoundError

**症状**: 
```
ModuleNotFoundError: No module named 'xxx'
```

**解决**:
```bash
cd backend
pip install -r requirements.txt
```

#### 错误 2: Ollama 连接失败

**症状**:
```
ConnectionError: Failed to connect to Ollama
```

**解决**:
```bash
# 确保 Ollama 正在运行
ollama serve

# 在另一个终端验证
curl http://localhost:11434/api/tags
```

#### 错误 3: 配置文件错误

**症状**:
```
KeyError: 'universe'
JSONDecodeError: ...
```

**解决**:
检查 `backend/config/config.json` 格式是否正确：
```json
{
  "universe": ["NVDA", "MSFT", ...],
  "llm": {
    "default_model": "llama3.1",
    "ollama_host": "http://localhost:11434"
  }
}
```

#### 错误 4: 投资组合未初始化

**症状**:
```
FileNotFoundError: portfolio_state.json
```

**解决**:
```bash
cd backend
python scripts/init_data.py
```

#### 错误 5: yfinance 数据获取失败

**症状**:
```
YFPricesMissingError: No data for ...
```

**解决**:
- 检查网络连接
- 等待一段时间后重试
- 或使用模拟数据模式

## 快速修复流程

### 1. 运行诊断

```powershell
cd backend
python diagnose_run_loop_error.py
```

### 2. 根据诊断结果修复

- **如果模块导入失败**: `pip install -r requirements.txt`
- **如果 Ollama 连接失败**: 启动 `ollama serve`
- **如果配置文件错误**: 检查 `config/config.json`
- **如果投资组合未初始化**: 运行 `python scripts/init_data.py`

### 3. 重启 API

```powershell
cd backend\scripts
powershell -ExecutionPolicy Bypass -File .\restart_api.ps1
```

### 4. 再次尝试 Run Loop

在前端点击 "Run Loop"，查看：
- 前端是否显示成功消息
- 后端日志中的详细错误信息
- 对话是否开始生成

## 已改进的内容

### 1. 后端错误处理
- ✅ 添加详细的 `[Run Loop]` 日志
- ✅ 返回完整的错误堆栈跟踪
- ✅ 允许同一天多次运行（用于测试）

### 2. 前端错误显示
- ✅ 显示详细的错误信息
- ✅ 显示堆栈跟踪（如果有）
- ✅ 提供修复建议

### 3. 诊断工具
- ✅ 创建了 `diagnose_run_loop_error.py`
- ✅ 自动检查所有常见问题
- ✅ 提供修复建议

## 验证修复

修复后，验证以下内容：

1. **Run Loop 成功执行**
   - 前端显示 "交易循环执行成功！"
   - 后端日志显示 `[Run Loop] 交易循环执行成功`

2. **对话开始生成**
   - 检查 `backend/data/logs/discussion_actions.jsonl`
   - 文件应该有新内容
   - 前端应该显示对话

3. **交易记录生成**
   - 检查 `backend/data/logs/trades.jsonl`
   - 如果有订单，应该有交易记录

4. **投资组合更新**
   - 检查 `backend/data/logs/portfolio_state.json`
   - 如果有交易，现金和持仓应该更新

## 下一步

1. **运行诊断工具**: `python backend/diagnose_run_loop_error.py`
2. **查看诊断结果**: 根据提示修复问题
3. **重启 API**: 使用重启脚本
4. **再次尝试**: 点击 "Run Loop" 并观察结果

如果问题仍然存在，请分享：
- 诊断工具的输出
- 后端 API 终端中的 `[Run Loop]` 日志
- 前端浏览器控制台的完整错误信息

