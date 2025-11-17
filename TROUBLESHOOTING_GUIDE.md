# 故障排除指南

## 问题：改动没有生效

### 症状
1. 前端显示 31 个 PENDING 订单（市场关闭时不应该有订单）
2. 对话内容可能还是被截断（有 "|" 分隔符）
3. 执行 system_init 后，对话记录被清空

### 可能的原因

#### 1. 后端服务没有重启 ⚠️ **最可能**
**问题**: 后端代码已修改，但服务还在运行旧代码

**解决方案**:
1. **停止后端服务** (Ctrl+C 或关闭终端)
2. **重新启动后端服务**:
   ```bash
   cd backend
   python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
   ```
3. **等待服务完全启动**（看到 "Application startup complete"）
4. **刷新前端页面**（或硬刷新 Ctrl+Shift+R）

#### 2. 浏览器缓存了旧的前端代码 ⚠️ **常见**
**问题**: 浏览器缓存了旧的 `monitor.html` 文件

**解决方案**:
1. **硬刷新页面**:
   - Windows/Linux: `Ctrl + Shift + R` 或 `Ctrl + F5`
   - Mac: `Cmd + Shift + R`
2. **清除浏览器缓存**:
   - Chrome: 设置 → 隐私和安全 → 清除浏览数据 → 选择"缓存的图片和文件"
   - 或者使用无痕模式测试

#### 3. 代码改动没有保存 ⚠️ **检查**
**问题**: 文件可能没有保存

**验证方法**:
1. 检查文件修改时间
2. 检查 Git 状态（如果有使用 Git）
3. 重新打开文件确认改动存在

#### 4. 31 个 PENDING 订单的问题 ⚠️ **需要清理**
**问题**: 这些订单是在市场关闭时创建的，应该被清理或标记为 FILLED

**解决方案**:
1. **执行 system_init** 清理所有数据（已执行）
2. **检查后端日志**，确认订单创建逻辑：
   - 应该看到: `[TRADING CYCLE] Market is closed. Immediately cancelling X today's pending orders`
   - 或者: `[TRADING CYCLE] ⚠️ WARNING: Market is closed but Trader Agent generated orders!`

### 验证步骤

#### 步骤 1: 确认后端代码已修改
检查以下文件是否包含最新改动：
- `backend/src/orchestrator/trading_cycle.py`: 应该有 "|" 替换逻辑（line 456-458, 518-520, 1804-1806）
- `backend/src/agents/trader_agent.py`: 应该有 "|" 替换逻辑（line 813, 336, 837, 852, 865）

#### 步骤 2: 重启后端服务
```bash
# 停止当前服务（Ctrl+C）
# 然后重新启动
cd backend
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

#### 步骤 3: 清除浏览器缓存并刷新
- 硬刷新: `Ctrl + Shift + R`
- 或使用无痕模式

#### 步骤 4: 执行一次交易周期
1. 点击 "Execute Trading Cycle" 按钮
2. 检查后端日志输出
3. 检查前端是否显示完整对话（没有 "|" 分隔符）

#### 步骤 5: 检查订单状态
- 如果市场关闭，应该看到 0 个 PENDING 订单
- 如果市场开放，订单应该立即标记为 FILLED（不是 PENDING）

### 调试日志

检查后端日志，应该看到：
```
[TRADER] Market is CLOSED. Running analysis only - no trading orders will be generated.
[TRADING CYCLE] Market is closed. Skipping order creation (should_create_orders=False).
[TRADING CYCLE] Coordinator summary length: XXX characters
[TRADING CYCLE] Trader Agent content length: XXX characters
```

如果看到这些日志，说明代码正常工作。

### 如果问题仍然存在

1. **检查文件路径**: 确认修改的文件是正确的文件
2. **检查 Python 导入**: 确认 Python 导入的是修改后的文件
3. **检查 API 响应**: 使用浏览器开发者工具检查 API 返回的数据
4. **检查日志文件**: 查看 `data/logs/discussion_actions.jsonl` 文件内容

