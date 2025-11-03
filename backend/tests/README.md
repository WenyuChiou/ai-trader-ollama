# 测试文件说明

## 📁 测试文件组织

所有测试文件都在 `backend/tests/` 目录下，按功能分类：

### 🔧 核心测试（必须运行）

| 测试文件 | 说明 |
|---------|------|
| `test_00_config.py` | 配置文件加载测试 |
| `test_01_market_batch_vix.py` | 市场数据和 VIX 获取测试 |
| `test_02_discussion_rounds.py` | 讨论轮次测试 |
| `test_03_trading_cycle_e2e.py` | 端到端交易循环测试 |
| `test_04_discussion_tools.py` | 讨论工具使用测试 |

### ⭐ 重要测试（推荐运行）

| 测试文件 | 说明 |
|---------|------|
| `test_05_full_trading_loop.py` | **完整交易循环测试（多股票持仓）** |
| `test_10_tools_integration.py` | 工具集成测试（Crypto、Fear & Greed、Jin10、Treasury Bonds） |
| `test_vix_fetch.py` | VIX 数据获取测试 |

### 🔍 可选测试

| 测试文件 | 说明 |
|---------|------|
| `test_prompts.py` | Prompt 模板测试 |
| `test_prompts_debug.py` | Prompt 调试测试 |

## 🚀 运行方式

### 运行所有测试

```bash
cd backend
python tests/run_all.py
```

### 运行单个测试

```bash
cd backend

# 完整交易循环测试（推荐）
python tests/test_05_full_trading_loop.py

# 工具集成测试
python tests/test_10_tools_integration.py

# 配置测试
python tests/test_00_config.py
```

### 运行特定类别测试

```bash
cd backend

# 只运行核心测试
python tests/test_00_config.py
python tests/test_01_market_batch_vix.py
python tests/test_02_discussion_rounds.py
python tests/test_03_trading_cycle_e2e.py
python tests/test_04_discussion_tools.py
```

## 📋 测试覆盖范围

### ✅ 已测试功能

- ✅ 配置文件加载
- ✅ 市场数据获取（股票、VIX、国债）
- ✅ 讨论 Agent（多轮讨论、工具调用）
- ✅ 交易循环（完整流程）
- ✅ 多股票持仓功能
- ✅ 工具集成（Crypto、Fear & Greed、Jin10）
- ✅ Portfolio 管理
- ✅ Trade Logger

### ⏳ 需要特定环境的测试

以下测试需要 Ollama 服务运行：

- `test_02_discussion_rounds.py` - 需要 LLM
- `test_03_trading_cycle_e2e.py` - 需要 LLM
- `test_04_discussion_tools.py` - 需要 LLM
- `test_05_full_trading_loop.py` - 需要 LLM

### 🌐 需要网络连接的测试

以下测试需要网络连接：

- `test_01_market_batch_vix.py` - 需要 yfinance API
- `test_10_tools_integration.py` - 需要各种外部 API
- `test_vix_fetch.py` - 需要网络连接

## 🔧 测试文件路径设置

所有测试文件都使用标准的路径设置：

```python
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  # backend/
SRC = ROOT / "src"  # backend/src/
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))
```

确保在 `backend/` 目录下运行测试。

## 📝 测试结果

测试结果会显示：
- ✅ `[OK]` - 测试通过
- ❌ `[FAIL]` - 测试失败
- ⚠️ `[WARN]` - 测试警告（可能缺少数据但功能正常）
- `[SKIP]` - 测试跳过（文件不存在）

## 🐛 故障排除

### 错误：`ModuleNotFoundError: No module named 'src'`

**解决**：确保在 `backend/` 目录下运行测试

```bash
cd backend
python tests/test_00_config.py
```

### 错误：`FileNotFoundError: agents config not found`

**解决**：确保 `backend/config/agents.yaml` 存在

### 错误：`ConnectionError` 或网络相关错误

**说明**：某些测试需要网络连接，如果离线运行会失败，这是正常的。

## 📚 相关文档

- `HOW_TO_RUN_TESTS.md` - 详细的运行说明
- `TEST_RESULTS.md` - 测试结果文档
- `TESTING_SUMMARY.md` - 测试总结

