# 测试套件文档

**语言**: [English](README.md) | [中文版](README_zh.md)

---

## 概述

本目录包含 AI-Trader Ollama 系统的完整测试套件。所有测试按类型组织，遵循 pytest 约定。

## 目录结构

```
tests/
├── integration/             # 系统组件的集成测试
│   ├── test_agent_architecture.py  # 代理系统测试
│   ├── test_portfolio.py            # 投资组合管理测试
│   ├── test_memory.py               # 内存系统测试
│   ├── test_api.py                  # API 端点测试
│   ├── test_analysis_targets.py    # 分析目标验证测试
│   └── test_trading_cycle_quick.py  # 快速交易循环测试（订单记录）
├── e2e/                     # 端到端测试
│   └── test_frontend.py             # 前端集成测试
├── utils/                   # 测试工具和辅助函数
│   └── test_helpers.py              # 共享测试工具
├── conftest.py              # Pytest 配置和共享 fixtures
├── pytest.ini               # Pytest 设置
├── README.md                # 本文档（英文版）
└── README_zh.md             # 中文版
```

## 前置要求

- Python 3.10 或更高版本
- 已激活虚拟环境
- 已安装依赖：`pip install -r backend/requirements.txt`
- Ollama 正在运行（需要 LLM 的测试）
- 后端 API 正在运行（API 测试）

## 运行测试

### 运行所有测试

```powershell
# 从项目根目录运行
pytest tests/ -v

# 或显示更多详细信息
pytest tests/ -v --tb=short
```

### 运行特定测试类别

```powershell
# 仅集成测试
pytest tests/integration/ -v

# 仅端到端测试
pytest tests/e2e/ -v

# 特定测试文件
pytest tests/integration/test_portfolio.py -v

# 特定测试函数
pytest tests/integration/test_portfolio.py::test_portfolio_creation -v
```

### 运行覆盖率测试

```powershell
# 如果尚未安装 pytest-cov，请先安装
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest tests/ --cov=backend/src --cov-report=html --cov-report=term-missing

# 查看 HTML 覆盖率报告
# 在浏览器中打开 htmlcov/index.html
```

### 并行运行测试

```powershell
# 如果尚未安装 pytest-xdist，请先安装
pip install pytest-xdist

# 并行运行测试（4 个工作进程）
pytest tests/ -n 4 -v
```

## 测试分类

### 集成测试 (`tests/integration/`)

**目的**：测试组件交互和系统集成

**测试文件**：
- `test_agent_architecture.py` - 测试代理系统、工具调用和协调
- `test_portfolio.py` - 测试投资组合管理、持仓跟踪和 P&L 计算
- `test_memory.py` - 测试内存系统、RAG 功能和内存检索
- `test_api.py` - 测试 API 端点、数据解析和响应格式
- `test_analysis_targets.py` - 测试分析目标验证（持仓、推荐股票、指数）
- `test_trading_cycle_quick.py` - **关键**：快速交易循环测试，用于订单记录验证

**特点**：
- 尽可能使用真实依赖
- 执行时间适中
- 可能需要 Ollama（LLM 相关测试）
- 可能需要 API 服务器（API 测试）

### 端到端测试 (`tests/e2e/`)

**目的**：测试从开始到结束的完整工作流程

**测试文件**：
- `test_frontend.py` - 测试前端集成、数据显示和用户交互

**特点**：
- 使用真实系统组件
- 执行时间较长
- 需要完整的系统设置（API 服务器、前端）
- 测试完整的用户工作流程

### 测试工具 (`tests/utils/`)

**目的**：测试的共享工具和辅助函数

**文件**：
- `test_helpers.py` - 通用测试函数、fixtures 和工具

## 测试 Fixtures

通用 fixtures 定义在 `tests/conftest.py` 中：

- `test_data_dir` - 测试数据目录路径
- `logs_dir` - 日志目录路径
- `test_portfolio_state` - 用于测试的示例投资组合状态
- `sample_market_data` - 用于测试的示例市场数据
- `sample_positions` - 用于测试的示例持仓

## 编写测试

### 集成测试示例

```python
def test_portfolio_creation():
    """测试投资组合创建和初始化"""
    from src.data.portfolio import Portfolio
    
    portfolio = Portfolio(initial_cash=10000.0)
    
    assert portfolio.cash == 10000.0
    assert portfolio.total_value == 10000.0
    assert len(portfolio._positions) == 0
```

### API 测试示例

```python
def test_api_health_endpoint(client):
    """测试 API 健康检查端点"""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

### 最佳实践

1. **使用描述性名称**：测试函数名称应清楚描述正在测试的内容
2. **Arrange-Act-Assert**：使用清晰的部分构建测试
3. **隔离测试**：每个测试应该独立，不依赖其他测试
4. **使用 Fixtures**：通过 fixtures 重用通用设置代码
5. **模拟外部依赖**：尽可能模拟外部 API 和服务
6. **清理**：测试完成后清理测试数据

## 测试状态

### 当前状态（主分支）

✅ **约 28 个测试通过**（100% 通过率）

**测试分类**：
- **集成测试**：约 25 个测试通过
  - 代理架构：6 个测试 ✅
  - 投资组合管理：7 个测试 ✅
  - 内存系统：5 个测试 ✅
  - API 端点：5 个测试 ✅
  - 分析目标：1 个测试 ✅
  - 交易循环快速测试：1 个测试 ✅（订单记录验证）
- **E2E 测试**：4/4 通过
  - 前端集成：4 个测试 ✅

### 测试覆盖率

当前测试覆盖率重点关注：
- 核心功能（投资组合、代理、内存）
- API 端点
- 数据一致性
- 系统集成

可能需要额外测试的领域：
- 边缘情况和错误处理
- 性能和负载测试
- 长期运行场景

## 持续集成

测试可以集成到 CI/CD 管道中：

```yaml
# GitHub Actions 工作流示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r backend/requirements.txt
      - run: pytest tests/ -v
```

## 故障排除

### 问题：ModuleNotFoundError

**错误**：`ModuleNotFoundError: No module named 'src'`

**解决方案**：确保从项目根目录运行测试：
```powershell
cd ai-trader-ollama
pytest tests/ -v
```

### 问题：Ollama 连接错误

**错误**：`ConnectionError: Ollama service not available`

**解决方案**：在运行测试前启动 Ollama 服务：
```powershell
ollama serve
```

### 问题：API 服务器未运行

**错误**：`ConnectionError: API server not available`

**解决方案**：在运行 API 测试前启动 API 服务器：
```powershell
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

## 关键测试文件

有关关键测试文件及其优先级的详细信息，请参阅：
- **[关键测试文件指南](../docs/KEY_TEST_FILES.md)** - 关键、重要和支持性测试的完整指南

**快速参考**：
- **关键测试**（部署前运行）：
  - `test_trading_cycle_quick.py` - 订单记录验证
  - `test_portfolio.py` - 投资组合和 P&L 计算
  - `test_agent_architecture.py` - 代理系统和工具

## 相关文档

- [关键测试文件指南](../docs/KEY_TEST_FILES.md) - **关键测试文件和优先级指南** ⭐
- [测试指南](../docs/TESTING.md) - 综合测试文档
- [测试脚本指南](../docs/TEST_SCRIPTS_GUIDE.md) - 独立测试脚本指南
- [测试结果](../docs/TEST_RESULTS.md) - 最新测试执行结果
- [快速入门指南](../docs/QUICK_START.md) - 安装和设置
- [架构文档](../docs/ARCHITECTURE.md) - 系统架构

## 贡献

添加新测试时：

1. 遵循现有的测试结构和命名约定
2. 将测试添加到适当的类别（integration/e2e/utils）
3. 如果添加新的测试类别，请更新此 README
4. 在提交 PR 前确保测试通过
5. 在测试函数中添加文档字符串，说明正在测试的内容

