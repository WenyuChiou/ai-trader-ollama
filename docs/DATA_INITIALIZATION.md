# 🔄 数据初始化指南

系统需要初始化数据后才能正常运行。本指南说明如何初始化和重置系统数据。

---

## 🚀 快速初始化

### 首次使用

```bash
cd backend
python scripts/init_data.py
```

这会初始化：
- ✅ Portfolio 状态（初始资金 $10,000）
- ✅ Memory 目录结构
- ✅ 交易记录日志文件

### 强制初始化（不询问）

```bash
python scripts/init_data.py --force
```

---

## 📋 初始化选项

### 只重置 Portfolio

如果只想重置投资组合（保留历史记忆）：

```bash
python scripts/init_data.py --reset-portfolio
```

### 自定义初始资金

```bash
python scripts/init_data.py --initial-cash 50000.0
```

---

## 📁 初始化的数据

### 1. Portfolio 状态

**文件**: `backend/data/logs/portfolio_state.json`

**内容**:
```json
{
  "cash": 10000.0,
  "initial_value": 10000.0,
  "positions": {},
  "last_updated": "2025-01-28T10:00:00",
  "initialized_at": "2025-01-28T10:00:00"
}
```

### 2. Memory 目录

**目录**: `backend/data/logs/memory/`

**结构**:
```
memory/
├── daily/          # 每日记忆
├── weekly/         # 每周记忆
├── monthly/        # 每月记忆
└── index/          # 索引文件
    └── daily_index.json
```

### 3. 交易记录日志

**文件**:
- `trades.jsonl` - 交易记录
- `pending_orders.jsonl` - 挂单记录
- `filled_orders.jsonl` - 成交记录
- `equity_history.jsonl` - 净值历史
- `real_time_snapshots.jsonl` - 实时快照
- `monitoring.jsonl` - 监控日志
- `discussion_actions.jsonl` - 讨论记录

---

## 🔄 重新初始化

### 重置所有数据

如果需要完全重置系统：

```bash
python scripts/init_data.py --force
```

⚠️ **警告**: 这会清空所有现有数据！

### 重置前备份

初始化脚本会自动备份旧数据：

- **Memory**: 备份到 `memory_backup_YYYYMMDD_HHMMSS/`
- **日志文件**: 备份为 `*.backup_YYYYMMDD_HHMMSS`

---

## 🧪 初始化后验证

### 检查文件

```bash
# Windows
dir backend\data\logs\portfolio_state.json
dir backend\data\logs\memory

# Linux/Mac
ls -la backend/data/logs/portfolio_state.json
ls -la backend/data/logs/memory/
```

### 运行测试

```bash
cd backend

# 测试 Portfolio 加载
python -c "from src.data.portfolio import Portfolio; import json; from pathlib import Path; state = json.load(open('data/logs/portfolio_state.json')); print('Portfolio loaded:', state['cash'])"

# 运行一次交易循环（可选）
python scripts/run_daily_trading.py
```

---

## 🔧 手动初始化

如果需要手动初始化某些部分：

### 手动创建 Portfolio

```python
from src.data.portfolio import Portfolio
import json
from pathlib import Path
from datetime import datetime

portfolio = Portfolio(cash=10000.0, initial_value=10000.0)

state = {
    "cash": portfolio.cash,
    "initial_value": portfolio.initial_value,
    "positions": {},
    "last_updated": datetime.now().isoformat(),
}

state_file = Path("data/logs/portfolio_state.json")
state_file.parent.mkdir(parents=True, exist_ok=True)
with state_file.open("w") as f:
    json.dump(state, f, indent=2)
```

### 手动创建 Memory 目录

```bash
mkdir -p backend/data/logs/memory/{daily,weekly,monthly,index}
```

---

## ⚠️ 注意事项

1. **备份重要数据**: 初始化前确保已备份重要数据
2. **初始资金**: 默认 $10,000，可根据需要调整
3. **历史记忆**: 重置会清空所有历史记忆，请谨慎操作
4. **交易记录**: 重置会清空所有交易记录

---

## 🆘 故障排除

### 初始化失败

**错误**: `Permission denied` 或文件无法创建

**解决**:
- 检查目录权限
- 确认磁盘空间足够
- Windows: 以管理员权限运行

### Portfolio 状态丢失

**症状**: 运行交易时提示 Portfolio 状态不存在

**解决**:
```bash
python scripts/init_data.py --reset-portfolio
```

---

## 📝 初始化检查清单

初始化后验证：

- [ ] `portfolio_state.json` 存在且格式正确
- [ ] Memory 目录结构完整
- [ ] 所有日志文件已创建
- [ ] 可以成功运行 `run_daily_trading.py`
- [ ] API 可以读取 Portfolio 状态

---

**初始化完成后的下一步**:
1. 运行一次交易循环: `python scripts/run_daily_trading.py`
2. 启动 API: `uvicorn src.api.server:app --reload`
3. 打开监控界面: `http://localhost:5173`

