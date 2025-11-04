# 文件整理说明

## 文件分类

### 📚 文档文件（保留）

#### 核心文档
- `README.md` - 主文档（项目根目录）
- `API_ENDPOINTS.md` - API 端点完整文档
- `FRONTEND_BACKEND_INTEGRATION.md` - 前后端集成验证文档

#### 流程文档
- `PORTFOLIO_UPDATE_FLOW.md` - 投资组合更新流程说明
- `FIX_SIMULATION_CONVERSATIONS.md` - 模拟对话问题修复指南

### 🧪 测试文件（保留，用于开发调试）

#### 功能测试
- `test_api_portfolio_endpoint.py` - API 端点测试
- `test_portfolio_update.py` - 投资组合更新测试
- `test_full_workflow.py` - 完整工作流测试
- `test_multi_day_workflow.py` - 多天工作流测试
- `test_october_simulation.py` - 10月模拟测试
- `test_simulation_conversations.py` - 模拟对话测试

#### 诊断工具
- `check_simulation_status.py` - 模拟状态诊断脚本

### 🗑️ 可清理文件（考虑删除）

#### 临时模拟脚本（已整合到主流程）
- `simulate_weekly_trading.py` - 可以删除（功能已整合）
- `simulate_last_week.py` - 可以删除（功能已整合）
- `simulate_weekly_pending_orders.py` - 可以删除（功能已整合）
- `simulate_monthly_llm_comparison.py` - 可以删除（功能已整合）

#### 旧测试文件（已整合）
- `test_multiple_dates.py` - 可以删除（功能已整合到 test_multi_day_workflow.py）
- `test_trading_loop_direct.py` - 可以删除（功能已整合）

### 📝 脚本文件（保留）

#### 核心脚本
- `scripts/init_data.py` - 数据初始化
- `scripts/start_api_background.ps1` - 启动 API
- `scripts/restart_api.ps1` - 重启 API
- `scripts/run_daily_trading.py` - 每日交易
- `scripts/simulate_october_history.py` - 10月模拟

#### 工具脚本
- `scripts/check_api_status.ps1` - 检查 API 状态
- `scripts/check_port.ps1` - 检查端口
- `scripts/show_discussion_rounds.py` - 显示讨论轮次

#### 调度脚本
- `scripts/schedule_daily_task.ps1` - 每日任务调度
- `scripts/schedule_hourly_update.ps1` - 每小时更新
- `scripts/setup_all.ps1` - 一键设置

## 推荐清理操作

### 选项 1: 保守清理（推荐）
只删除明确不再使用的文件：
```bash
# 删除临时模拟脚本
rm backend/simulate_weekly_trading.py
rm backend/simulate_last_week.py
rm backend/simulate_weekly_pending_orders.py
rm backend/simulate_monthly_llm_comparison.py
```

### 选项 2: 完整清理
删除所有临时文件和旧测试文件：
```bash
# 删除临时模拟脚本
rm backend/simulate_*.py

# 删除旧测试文件
rm backend/test_multiple_dates.py
rm backend/test_trading_loop_direct.py
```

## 文件结构建议

### 当前结构（保留）
```
backend/
├── src/                    # 源代码
├── scripts/               # 脚本文件
├── config/                # 配置文件
├── prompts/               # Prompt 模板
├── data/                  # 数据文件（.gitignore）
├── tests/                 # 单元测试
├── *.py                   # 测试和工具脚本
├── *.md                   # 文档文件
└── requirements.txt       # 依赖
```

### 可选改进（未来）
```
backend/
├── src/                    # 源代码
├── scripts/               # 脚本文件
├── config/                # 配置文件
├── prompts/               # Prompt 模板
├── data/                  # 数据文件（.gitignore）
├── tests/                 # 单元测试
├── docs/                  # 文档（如果需要）
│   ├── API_ENDPOINTS.md
│   └── INTEGRATION.md
└── requirements.txt       # 依赖
```

## 注意事项

1. **不要删除** `check_simulation_status.py` - 这是有用的诊断工具
2. **不要删除** 测试文件 - 用于开发和调试
3. **不要删除** 文档文件 - 包含重要信息
4. **可以删除** 临时模拟脚本 - 功能已整合到主流程

## Git 忽略建议

确保 `.gitignore` 包含：
```
backend/data/logs/**
backend/data/memory/**
backend/__pycache__/**
backend/src/**/__pycache__/**
*.pyc
*.pyo
```

