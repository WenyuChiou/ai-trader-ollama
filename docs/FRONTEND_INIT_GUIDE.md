# 前端初始化指南

## 初始化流程

### 1. 用户触发初始化

点击前端的 "⚙️ Initialize" 按钮，触发 `initSystem()` 函数。

### 2. 安全检查

- **只读模式检查**: 如果在只读模式下，禁止初始化
- **冲突检查**: 检查是否有正在进行的操作（交易、自动交易等）
- **二次确认**: 用户需要确认两次才能执行初始化

### 3. 停止所有操作

- 停止自动交易定时器
- 重置执行状态标志
- 重置按钮状态

### 4. 调用后端API

```javascript
POST /api/system/init?force=true
```

### 5. 后端处理

**删除的文件**:
- `portfolio_state.json`
- `pending_orders.jsonl`
- `filled_orders.jsonl`
- `equity_history.jsonl`
- `discussion_actions.jsonl`

**保留的内容**:
- `memory/` 目录（Agent学习数据）
- `.gitkeep` 文件
- 备份文件（自动清理7天前的旧备份）

**自动备份**:
- 如果存在 `portfolio_state.json`，会自动创建备份
- 备份文件名: `portfolio_state_backup_YYYYMMDD_HHMMSS.json`

### 6. 前端清空缓存

初始化成功后，前端会清空所有缓存：

```javascript
window.currentPortfolio = null;
window.currentConversations = [];
window.toolResultsByCategory = null;
window.lastTradesData = [];
window.lastEquityData = [];
window.lastBackendStatus = null;
window.lastSystemInfo = null;
window.newsData = [];
```

### 7. 重置UI状态

- **订单状态**: 重置为 0 pending, 0 filled
- **对话状态**: 重置为 Idle
- **对话显示**: 清空对话内容
- **新闻数据**: 清空新闻缓存

### 8. 刷新数据

调用 `refreshData(true)` 强制刷新所有数据：
- Portfolio数据
- Equity历史
- 对话记录
- 交易记录
- 后端状态

### 9. 更新自动交易状态

初始化后，自动交易会停止，等待用户手动触发第一次交易。

## 初始化后的状态

### 数据状态

- **Portfolio**: 现金 $10,000，无持仓
- **Orders**: 0 pending, 0 filled
- **Equity History**: 空（新记录会从 $10,000 开始）
- **Conversations**: 空
- **News**: 空

### UI状态

- 所有图表显示空状态
- 订单状态显示 0/0
- 对话显示 "No conversations yet"
- 新闻模态框为空

## 验证初始化

### 检查点

1. **Portfolio显示**: 应该显示 $10,000 现金，0 持仓
2. **订单状态**: 应该显示 0 pending, 0 filled
3. **对话记录**: 应该为空
4. **净值图表**: 应该从 $10,000 开始
5. **新闻数据**: 应该为空

### 使用验证脚本

```bash
# 验证持仓记录一致性
python scripts/verify_portfolio.py
```

## 常见问题

### Q: 初始化后数据没有清空？

**A**: 检查：
1. 后端API是否成功返回 `ok: true`
2. 前端是否正确清空了缓存
3. 浏览器控制台是否有错误

### Q: 初始化后仍然显示旧数据？

**A**: 
1. 强制刷新页面（Ctrl+F5）
2. 检查浏览器缓存
3. 检查 `refreshData()` 是否被正确调用

### Q: 初始化失败？

**A**: 检查：
1. 后端服务是否运行
2. 是否有文件权限问题
3. 查看后端日志

## 相关文件

- `frontend/monitor.html` - 前端初始化逻辑
- `backend/src/api/server.py` - 后端初始化API
- `scripts/verify_portfolio.py` - 持仓验证脚本

