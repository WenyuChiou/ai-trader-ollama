# 前端 vs 测试脚本差异分析

## 🔍 问题：为什么前端和测试脚本的结果不一样？

### 调用路径对比

#### 1. **测试脚本** (`backend/scripts/test_all_scenarios.py`)

```python
# 第117行
result = execute_daily_trade(
    start="2025-11-12",      # ✅ 指定日期
    end="2025-11-12",        # ✅ 指定日期
    tool_budget=6,           # ✅ 硬编码：6
    min_tools=3              # ✅ 硬编码：3
)
```

**特点**：
- ✅ 使用**固定日期**（2025-11-12）
- ✅ `tool_budget=6`（硬编码）
- ✅ `min_tools=3`（硬编码）
- ✅ 直接调用函数，不经过 API

---

#### 2. **前端/API** (`/api/trading/execute-trade`)

```python
# backend/src/api/server.py 第619行
result = execute_daily_trade(
    rounds=rounds,                    # 从 config.json 读取（默认3）
    auto_tools=True,                  # 硬编码：True
    tool_budget=tool_budget,          # 从 config.json 读取（默认15）
    universe=universe                 # 从 config.json 读取
    # ❌ 没有传入 start 和 end
    # ❌ 没有传入 min_tools
)
```

**特点**：
- ❌ **没有传入 `start` 和 `end`** → 使用 `_default_window()`（今天往前180天）
- ✅ `tool_budget` 从 `config.json` 读取（`discussion_tool_budget: 15`）
- ❌ **没有传入 `min_tools`** → 使用函数默认值 `min_tools=3`
- ✅ 经过 API 层，可能有额外的处理

---

## 📊 关键差异总结

| 参数 | 测试脚本 | 前端/API | 影响 |
|------|---------|---------|------|
| **日期范围** | `start="2025-11-12"`<br>`end="2025-11-12"` | 使用 `_default_window()`<br>（今天往前180天） | ⚠️ **数据不同**：测试用历史数据，前端用实时数据 |
| **tool_budget** | `6`（硬编码） | `15`（从 config.json 读取） | ⚠️ **工具调用预算不同** |
| **min_tools** | `3`（硬编码） | `3`（函数默认值） | ✅ 相同 |
| **调用方式** | 直接函数调用 | 通过 API endpoint | ⚠️ **可能有额外处理** |

---

## 🔧 `execute_daily_trade` 函数默认行为

```python
def execute_daily_trade(
    *,
    start: str | None = None,        # 默认 None
    end: str | None = None,           # 默认 None
    universe: List[str] | None = None,
    rounds: int = 3,                  # 默认 3
    auto_tools: bool = True,
    tool_budget: int = 8,             # 默认 8（但 API 传入的是 15）
    min_tools: int = 3,               # 默认 3
    ...
):
    # 如果 start 和 end 都是 None，使用默认窗口
    if start is None and end is None:
        start, end = _default_window()  # 今天往前180天
```

---

## ⚠️ 发现的问题

### 问题 1: API 没有传入 `min_tools`

**当前代码** (`backend/src/api/server.py:619`):
```python
result = execute_daily_trade(
    rounds=rounds,
    auto_tools=True,
    tool_budget=tool_budget,
    universe=universe
    # ❌ 缺少 min_tools 参数
)
```

**影响**：
- 虽然函数默认值是 `min_tools=3`，但应该从 config.json 读取以保持一致性

### 问题 2: API 没有传入日期参数

**当前代码** (`backend/src/api/server.py:619`):
```python
result = execute_daily_trade(
    # ❌ 没有传入 start 和 end
    # 会使用 _default_window()（今天往前180天）
)
```

**影响**：
- 测试脚本使用固定日期（2025-11-12），API 使用实时日期范围
- 可能导致数据不一致

### 问题 3: tool_budget 不一致

- 测试脚本：`tool_budget=6`
- API：`tool_budget=15`（从 config.json 读取）

**影响**：
- 工具调用行为可能不同

---

## 🔧 建议修复

### 修复 1: API 应该从 config.json 读取 `min_tools`

```python
# backend/src/api/server.py
config = load_trading_config()
universe = config["universe"]
tool_budget = config["discussion_tool_budget"]  # 或 config.get("discussion_tool_budget", 15)
rounds = config["discussion_rounds"]  # 或 config.get("discussion_rounds", 3)
min_tools = config.get("discussion_min_tools", 3)  # 新增：从 config 读取

result = execute_daily_trade(
    rounds=rounds,
    auto_tools=True,
    tool_budget=tool_budget,
    min_tools=min_tools,  # 新增
    universe=universe
)
```

### 修复 2: 统一日期处理逻辑

**选项 A**: API 也使用固定日期（用于测试）
```python
# 如果需要在 API 中测试固定日期
test_date = request.json.get("test_date")  # 可选参数
if test_date:
    start = end = test_date
else:
    start = end = None  # 使用默认窗口
```

**选项 B**: 测试脚本也使用实时日期
```python
# 测试脚本改为使用实时日期
from datetime import date
today = date.today().isoformat()
result = execute_daily_trade(
    start=today,
    end=today,
    ...
)
```

---

## 📝 关于 Summary 问题的额外说明

**Summary 问题**（`decision.summary` 返回 `no_op`）：
- ✅ **已修复**：在 `trader_agent.py` 中修复了 prompt 变量传递问题
- ✅ **影响范围**：无论是测试脚本还是 API，都使用相同的 `run_trader()` 函数
- ✅ **修复后**：前端和测试脚本应该都会得到正确的 summary

**验证方法**：
1. 重新运行测试脚本，检查 `decision.summary` 是否正常
2. 通过前端执行交易循环，检查 `decision.summary` 是否正常

---

## 🎯 总结

**主要差异**：
1. **日期范围**：测试用固定日期，API 用实时日期
2. **tool_budget**：测试用6，API 用15
3. **调用方式**：测试直接调用，API 通过 HTTP

**Summary 问题**：
- ✅ 已修复（prompt 变量传递问题）
- ✅ 影响所有调用路径（测试和 API 都使用相同的 `run_trader()` 函数）

**建议**：
- 统一配置参数（从 config.json 读取）
- 考虑在 API 中添加可选的 `test_date` 参数用于测试

