# 测试工具说明

这个文件夹包含了所有测试脚本，用于测试系统的各个组件。

## 主要测试脚本

### 1. `test_tools.py` - 综合工具测试（推荐使用）

测试所有工具的功能，支持分类测试和多种选项。

**用法：**
```bash
# 从项目根目录运行
python test/test_tools.py

# 或从 test 文件夹运行
cd test
python test_tools.py
```

**选项：**
- `--category {all,fundamental,technical,market,sentiment,news}` - 选择测试类别
- `--symbol SYMBOL` - 指定测试用的股票代码（默认：NVDA）
- `--save FILE` - 保存测试结果到 JSON 文件

**示例：**
```bash
# 测试所有工具
python test/test_tools.py

# 只测试基本面工具
python test/test_tools.py --category fundamental

# 只测试新闻工具
python test/test_tools.py --category news

# 使用不同股票代码
python test/test_tools.py --symbol AAPL

# 保存结果
python test/test_tools.py --save results.json
```

### 2. `test_all_tools.py` - 快速测试所有工具

快速测试所有主要工具，显示简要结果。

**用法：**
```bash
python test/test_all_tools.py
```

### 3. 其他测试脚本

- `test_fundamental_tools.py` - 测试基本面分析工具
- `test_news_scan.py` - 测试新闻扫描功能
- `test_news_scan_issue.py` - 测试新闻扫描问题
- `test_tool_display.py` - 测试工具结果显示
- `test_tool_result_flow.py` - 测试工具结果数据流
- `test_frontend_flow.py` - 测试前端数据流
- `test_frontend_agent_speed.py` - 测试前端 Agent 速度
- `check_tool_results.py` - 检查工具结果
- `verify_tool_results.py` - 验证工具结果
- `check_model_performance.py` - 检查模型性能

## 工具类别

### 基本面工具 (fundamental)
- `get_company_fundamentals` - 获取公司基本面数据
- `get_earnings_history` - 获取收益历史
- `get_financial_statements` - 获取财务报表

### 技术分析工具 (technical)
- `get_advanced_indicators` - 获取高级技术指标
- `get_support_resistance` - 获取支撑阻力位

### 市场工具 (market)
- `get_market_indices` - 获取市场指数
- `get_sector_rotation` - 获取板块轮动
- `get_market_breadth` - 获取市场广度

### 情绪工具 (sentiment)
- `vix_term` - VIX 期限结构
- `fear_greed` - 恐惧贪婪指数

### 新闻工具 (news)
- `news_scan` - 新闻扫描

## 运行测试

### 从项目根目录运行：
```bash
python test/test_tools.py --category all
```

### 从 test 文件夹运行：
```bash
cd test
python test_tools.py --category all
```

## 注意事项

1. 确保后端服务已启动（某些测试需要）
2. 某些工具需要网络连接（如新闻、市场数据）
3. 某些工具可能需要额外的依赖（如 scipy 用于 get_support_resistance）
4. 测试结果中的 "⚠️ NO DATA" 不一定是错误，可能是正常情况（如某些股票没有收益数据）

