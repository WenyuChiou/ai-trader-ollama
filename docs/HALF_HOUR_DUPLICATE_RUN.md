# 半小时内运行两次 Trading Cycle 的预期行为

## 📋 场景说明

如果在**30分钟内**运行两次完整的 trading cycle，系统会有以下行为：

---

## ✅ 预期结果

### 1. **记忆工具调用** 🧠

**第一次运行**：
- ✅ Market Analyst **强制调用** `get_recent_memories`（系统自动添加）
- ✅ 日志显示：`[MEMORY] 🔧 FORCING memory tool call: get_recent_memories`
- ✅ 获取最近5天的记忆（如果有的话）

**第二次运行**（30分钟内）：
- ✅ Market Analyst **再次强制调用** `get_recent_memories`
- ✅ 这次会包含**第一次运行**的记忆（如果已经保存）
- ✅ 记忆内容会更新，包含两次运行的分析结果

**结论**：✅ 两次运行都会调用记忆工具，第二次会看到第一次的结果

---

### 2. **订单创建** 📝

**保护机制**：
- ✅ 系统会检查今天是否已经有 **pending** 或 **filled** 订单
- ✅ 如果已有订单，**不会创建新订单**（防止重复）

**第一次运行**：
- ✅ 如果市场开放且没有现有订单 → **创建订单**
- ✅ 订单保存到 `pending_orders.jsonl`

**第二次运行**（30分钟内）：
- ⚠️ 检测到已有 pending 订单 → **跳过订单创建**
- ✅ 日志显示：`[TRADING CYCLE] ⚠️ Today already has orders (filled or pending). Skipping new order creation to prevent hourly duplicates.`
- ✅ 但**分析仍然会执行**（agents 仍然会分析市场）

**结论**：✅ 第二次运行**不会创建重复订单**，但会执行完整的分析

---

### 3. **净值记录** 💰

**记录行为**：
- ✅ 每次 trading cycle **都会记录**净值快照
- ✅ **所有时间戳都会保留**（不再按日期去重）
- ✅ 记录到 `equity_history.jsonl`

**第一次运行**：
- ✅ 记录净值快照（timestamp: `2025-11-18T10:00:00.000Z`）

**第二次运行**（30分钟后）：
- ✅ 再次记录净值快照（timestamp: `2025-11-18T10:30:00.000Z`）
- ✅ **两条记录都会保留**（即使同一天）

**结论**：✅ 两次运行会产生**两条独立的净值记录**，时间戳不同

---

### 4. **记忆保存** 📚

**保存行为**：
- ✅ 每次 trading cycle **都会保存**完整的记忆快照
- ✅ 保存到 `memory/daily/YYYY-MM-DD.json`

**第一次运行**：
- ✅ 保存记忆到 `memory/daily/2025-11-18.json`（如果文件不存在）
- ⚠️ 如果文件已存在，**会覆盖**（同一天只有一份完整记忆）

**第二次运行**（30分钟内）：
- ⚠️ **覆盖**同一天的记忆文件
- ✅ 包含第二次运行的所有分析结果
- ✅ 索引会更新（`memory/index/daily_index.json`）

**结论**：⚠️ 同一天的记忆会**被覆盖**，只保留最后一次运行的完整记忆

---

### 5. **聊天记录** 💬

**记录行为**：
- ✅ 每次运行的所有 agent 对话都会**追加**到 `discussion_actions.jsonl`
- ✅ **不会覆盖**，只会追加

**第一次运行**：
- ✅ 记录所有 agent 的分析和讨论
- ✅ 追加到文件末尾

**第二次运行**（30分钟内）：
- ✅ **再次追加**所有 agent 的分析和讨论
- ✅ 文件会包含两次运行的完整对话

**结论**：✅ 两次运行的所有对话都会**保留**，按时间顺序追加

---

## 📊 总结表格

| 项目 | 第一次运行 | 第二次运行（30分钟内） | 结果 |
|------|-----------|---------------------|------|
| **记忆工具调用** | ✅ 强制调用 | ✅ 强制调用 | ✅ 两次都调用 |
| **订单创建** | ✅ 创建（如果无现有订单） | ❌ 跳过（检测到已有订单） | ✅ 防止重复 |
| **净值记录** | ✅ 记录 | ✅ 记录 | ✅ 两条记录都保留 |
| **记忆保存** | ✅ 保存 | ⚠️ 覆盖同一天文件 | ⚠️ 只保留最后一次 |
| **聊天记录** | ✅ 追加 | ✅ 追加 | ✅ 两次都保留 |

---

## 🎯 实际示例

假设在 **10:00** 和 **10:15** 各运行一次：

### 第一次运行（10:00）
```
[MEMORY] 🔧 FORCING memory tool call: get_recent_memories
[MEMORY] ✅ Memory tool get_recent_memories retrieved 3 records
[TRADING CYCLE] ✅ Market is open and no existing orders - will create new orders
[EQUITY] Recorded daily equity for 2025-11-18: $10,000.00
[MEMORY] Saved daily memory for 2025-11-18
```

**生成的文件**：
- `pending_orders.jsonl`: 1条订单
- `equity_history.jsonl`: 1条记录（timestamp: `2025-11-18T10:00:00.000Z`）
- `memory/daily/2025-11-18.json`: 完整记忆
- `discussion_actions.jsonl`: 追加对话记录

### 第二次运行（10:15）
```
[MEMORY] 🔧 FORCING memory tool call: get_recent_memories
[MEMORY] ✅ Memory tool get_recent_memories retrieved 4 records (包含第一次运行的记忆)
[TRADING CYCLE] ⚠️ Today already has orders (filled or pending). Skipping new order creation to prevent hourly duplicates.
[EQUITY] Recorded daily equity for 2025-11-18: $10,050.00
[MEMORY] Saved daily memory for 2025-11-18 (覆盖第一次的记忆)
```

**生成的文件**：
- `pending_orders.jsonl`: **仍然是1条订单**（没有新增）
- `equity_history.jsonl`: **2条记录**（timestamp: `10:00:00Z` 和 `10:15:00Z`）
- `memory/daily/2025-11-18.json`: **覆盖**为第二次运行的记忆
- `discussion_actions.jsonl`: **追加**第二次运行的对话

---

## ⚠️ 注意事项

1. **订单保护**：系统会防止重复创建订单，这是**正常行为**
2. **记忆覆盖**：同一天的记忆会被覆盖，如果需要保留每次运行的记忆，可以考虑：
   - 修改记忆文件名包含时间戳
   - 或者使用 JSONL 格式追加而不是覆盖
3. **净值记录**：所有时间戳都会保留，这是**预期行为**
4. **聊天记录**：所有对话都会保留，可以完整追溯历史

---

## 🔍 验证方法

运行检查脚本验证数据：
```powershell
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend"
python scripts/check_memory_equity.py
```

查看具体记录：
```powershell
# 查看净值记录（应该看到两条）
Get-Content data\logs\equity_history.jsonl | Select-Object -Last 2

# 查看聊天记录（应该看到两次运行的所有对话）
Get-Content data\logs\discussion_actions.jsonl | Select-Object -Last 20

# 查看订单（应该只有一条）
Get-Content data\logs\pending_orders.jsonl
```

