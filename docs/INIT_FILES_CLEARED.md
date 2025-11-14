# 初始化会清空的文件清单

## 初始化操作说明

当点击"初始化系统"按钮时，以下文件会被清空或重置：

### 会被清空的文件

所有文件位于：`data/logs/` 目录

1. **equity_history.jsonl** - 净值历史记录
   - 会被清空
   - 初始化后会重新创建第一条记录（初始净值：$10,000）

2. **filled_orders.jsonl** - 已成交订单记录
   - 会被清空
   - 所有历史交易记录都会丢失

3. **pending_orders.jsonl** - 待处理订单
   - 会被清空
   - 所有未成交的订单都会被删除

4. **trades.jsonl** - 交易记录
   - 会被清空
   - 所有交易历史都会丢失

5. **real_time_snapshots.jsonl** - 实时快照
   - 会被清空
   - 所有历史快照都会丢失

6. **monitoring.jsonl** - 监控日志
   - 会被清空

7. **discussion_actions.jsonl** - 对话记录
   - 会被清空
   - 初始化后会重新创建（空文件）

8. **last_trade_date.txt** - 最后交易日期
   - 会被删除

9. **events.jsonl** - 事件日志
   - 会被清空

10. **demo_prices.json** - 演示价格缓存
    - 会被清空

11. **workflow_summary.json** - 工作流摘要
    - 会被清空

12. **所有 memory_*.jsonl 文件** - 内存文件
    - 会被清空
    - 包括：`memory_*.jsonl`, `memory_weekly_*.jsonl`
    - 包括：`memory/daily/*.json`, `memory/weekly/*.json`, `memory/monthly/*.json`, `memory/index/*.json`

### 会被重置的文件

1. **portfolio_state.json** - 投资组合状态
   - 会被重置为初始状态：
     ```json
     {
       "cash": 10000.0,
       "initial_value": 10000.0,
       "total_value": 10000.0,
       "positions": {}
     }
     ```
   - 如果有持仓，会先创建备份文件：`portfolio_state_backup_YYYYMMDD_HHMMSS.json`

### 会被保留的文件

1. **portfolio_state_backup_*.json** - 备份文件
   - 如果有持仓，初始化前会自动创建备份
   - 备份文件不会被删除（除非手动删除）

### 初始化后的状态

- 现金：$10,000
- 持仓：无
- 净值历史：只有一条初始记录（$10,000）
- 所有交易历史：清空
- 所有对话记录：清空
- 所有订单记录：清空

### ⚠️ 重要提示

1. **初始化是不可逆的操作**，所有历史数据都会丢失
2. 如果有持仓，系统会自动创建备份文件
3. 初始化后，第一次交易必须手动触发（不会自动执行）
4. 自动交易会在第一次手动交易后恢复正常

### 验证初始化结果

初始化后，可以通过以下方式验证：

1. 检查 `data/logs/portfolio_state.json`：
   - `cash` 应该是 `10000.0`
   - `positions` 应该是空对象 `{}`

2. 检查 `data/logs/equity_history.jsonl`：
   - 应该只有一条记录
   - `total_value` 应该是 `10000.0`

3. 检查其他文件：
   - `filled_orders.jsonl` 应该是空的或不存在
   - `pending_orders.jsonl` 应该是空的或不存在
   - `discussion_actions.jsonl` 应该是空的（但文件存在）

