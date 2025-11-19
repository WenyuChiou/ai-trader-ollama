# 测试脚本使用指南

## 概述

为了避免测试时覆盖交易记录，我们创建了独立的测试脚本。

## 脚本列表

### 1. `scripts/test_news_tools.py` - 新闻工具测试

**用途**: 独立测试新闻工具，不运行交易循环

**特点**:
- ✅ 只测试新闻工具功能
- ✅ 不会覆盖任何交易记录或持仓数据
- ✅ 不会运行交易循环
- ✅ 测试结果保存到 `data/logs/news_test_results.json`

**使用方法**:
```bash
# 从项目根目录运行
python scripts/test_news_tools.py
```

**测试内容**:
- `news_scan`: 关键词搜索新闻
- `plan_and_scan_news`: LLM生成查询并搜索新闻
- `fetch_jin10_news`: 从金十数据获取新闻

**输出**:
- 控制台显示测试结果
- 测试结果保存到 `data/logs/news_test_results.json`

---

### 2. `scripts/verify_portfolio.py` - 持仓记录验证

**用途**: 验证 `portfolio_state.json` 和 `equity_history.jsonl` 的一致性

**特点**:
- ✅ 只读操作，不会修改任何数据
- ✅ 检查持仓、现金、总价值的一致性
- ✅ 显示详细的差异报告

**使用方法**:
```bash
# 从项目根目录运行
python scripts/verify_portfolio.py
```

**检查内容**:
1. 数据加载: 检查文件是否存在
2. 基本信息: 显示时间戳、现金、总价值、持仓数量
3. 持仓比较: 比较两个文件的持仓差异
4. 现金一致性: 检查现金是否一致
5. 总价值一致性: 检查总价值是否一致

**输出示例**:
```
============================================================
持仓记录验证
============================================================

1. 加载数据...
✅ 数据加载成功

2. 基本信息:
   portfolio_state.json:
     - 时间戳: 2025-11-18T21:55:02.516Z
     - 现金: $13.20
     - 总价值: $9997.48
     - 持仓数量: 10

   equity_history.jsonl (最新记录):
     - 日期: 2025-11-18
     - 现金: $13.20
     - 总价值: $9997.48
     - 持仓数量: 10

3. 持仓比较:
   共同持仓: 10 个
     符号: AAPL, AMZN, BKR, MAR, NVDA, PSQ, SQQQ, SPXL, TQQQ, TSLA

4. 现金一致性:
   ✅ 现金一致 (差异: $0.00)

5. 总价值一致性:
   ✅ 总价值一致 (差异: $0.00)

6. 验证总结:
   ✅ 持仓记录一致
```

---

## 重要提示

### ⚠️ 不要使用 `scripts/run_daily_trading.py` 进行测试

**原因**:
- `run_daily_trading.py` 会运行完整的交易循环
- 会覆盖 `portfolio_state.json`
- 会创建新的交易记录
- 会影响持仓数据

**正确做法**:
- 测试新闻工具: 使用 `scripts/test_news_tools.py`
- 验证持仓: 使用 `scripts/verify_portfolio.py`
- 实际交易: 使用 `scripts/run_daily_trading.py`

---

## 文件位置

所有脚本都在 `scripts/` 目录下：
```
ai-trader-ollama/
├── scripts/
│   ├── test_news_tools.py      # 新闻工具测试
│   ├── verify_portfolio.py      # 持仓验证
│   └── run_daily_trading.py     # 实际交易（不要用于测试）
└── data/
    └── logs/
        ├── portfolio_state.json
        ├── equity_history.jsonl
        └── news_test_results.json  # 测试结果
```

---

## 故障排除

### 问题1: ModuleNotFoundError

**错误**: `ModuleNotFoundError: No module named 'src'`

**解决**: 确保从项目根目录运行脚本：
```bash
cd ai-trader-ollama
python scripts/test_news_tools.py
```

### 问题2: UnicodeEncodeError (Windows)

**错误**: `UnicodeEncodeError: 'cp950' codec can't encode character`

**解决**: 脚本已包含UTF-8编码支持，如果仍有问题，设置环境变量：
```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/test_news_tools.py
```

### 问题3: 文件未找到

**错误**: `portfolio_state.json 不存在或无法加载`

**解决**: 检查文件路径：
```bash
# Windows PowerShell
Test-Path "data\logs\portfolio_state.json"

# Linux/Mac
test -f data/logs/portfolio_state.json
```

---

## 最佳实践

1. **测试前备份**: 重要数据测试前先备份
2. **使用独立脚本**: 测试时使用独立的测试脚本
3. **验证结果**: 测试后验证数据一致性
4. **记录测试**: 保存测试结果以便后续分析

