# 重要文件说明

## 📁 核心测试文件

### `test_scenarios.py` ⭐ 主要测试文件
- 场景测试（5个真实场景）
- 多日模拟测试
- 包含 summary 质量验证
- **保留**

### `quick_test_news.py` ⭐ 新闻工具快速测试
- 快速测试新闻工具功能
- 验证新闻源可用性
- **保留**

## 🔧 实用工具脚本

### `check_*.py` - 检查脚本
- `check_cash_vs_orders.py` - 检查现金与订单
- `check_holdings_vs_orders.py` - 检查持仓与订单
- `check_pending_orders_detail.py` - 检查待处理订单详情
- **保留**（用于调试和验证）

### `analyze_all_orders.py` - 订单分析
- 分析所有订单（pending 和 filled）
- **保留**

### `run_full_workflow.py` - 完整工作流程
- 运行完整交易周期
- **保留**

## 📚 重要文档

### `README.md` - 项目说明
- **保留**

### `POSITION_INFO_ENHANCEMENT.md` - 持仓信息增强说明
- **保留**（重要功能文档）

### `WORKFLOW_OPTIMIZATION_SUMMARY.md` - 工作流程优化总结
- **保留**（重要功能文档）

### `IMPORTANT_FILES.md` - 本文件
- 重要文件说明
- **保留**

## 🗑️ 已删除的文件

以下文件已删除（临时测试文件和分析报告）：
- ✅ 临时新闻测试文件（`test_news_*.py`, `test_all_rss_feeds.py`）
- ✅ 临时分析报告（`*_ANALYSIS.md`, `*_FINDINGS.md`, `*_SUMMARY.md`）
- ✅ 重复的测试文件（`test_*_*.py` 多个）
- ✅ 测试结果 JSON 文件
- ✅ 模拟脚本（`simulate_*.py`）
- ✅ 演示脚本（`run_workflow_demo.py`）

## 💡 使用建议

### 测试场景
```powershell
cd backend
python test_scenarios.py
```

### 测试新闻工具
```powershell
cd backend
python quick_test_news.py
```

### 检查订单和现金
```powershell
cd backend
python check_cash_vs_orders.py
python check_holdings_vs_orders.py
python check_pending_orders_detail.py
```

### 分析所有订单
```powershell
cd backend
python analyze_all_orders.py
```

### 运行完整工作流程
```powershell
cd backend
python run_full_workflow.py
```

