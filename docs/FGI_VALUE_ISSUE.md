# FGI 值显示问题分析

## 问题描述

用户报告 FGI 值从 11 (EXTREME FEAR) 变成了 50 (NEUTRAL)。

## 可能原因

### 1. 数据源优先级问题

`fetch_fear_greed()` 函数按以下顺序尝试数据源：
1. CNN JSON 端点（`production.dataviz.cnn.io`）
2. feargreedmeter.com（替代数据源）
3. CNN HTML 页面（fallback）

**问题**：如果 CNN JSON 端点返回了 50，而 feargreedmeter.com 返回了 11，系统会优先使用 CNN JSON 的值（50）。

### 2. 前端分级逻辑错误（已修复）

在 `renderSummaryCards()` 函数中，使用了错误的分级逻辑：
- **错误**：`if (fgValue >= 45)` → 值 50 被分类为 "Neutral"
- **正确**：`if (fgValue <= 55)` → 值 50 应该被分类为 "NEUTRAL"

**修复**：已更新为使用标准分级逻辑（`<=` 而不是 `>=`）。

### 3. 数据源返回不同值

不同数据源可能返回不同的 FGI 值：
- CNN 可能使用不同的计算方法
- feargreedmeter.com 可能使用不同的数据源
- 数据更新频率不同

## 解决方案

### 已实施的修复

1. **统一分级标准**：
   - 所有数据源使用 `_get_fgi_label()` 函数统一分级
   - 前端和后端使用相同的分级阈值

2. **修复前端显示**：
   - `renderSummaryCards()` 现在使用标准分级逻辑
   - 值 50 正确显示为 "NEUTRAL"（如果确实是 50）

3. **增强调试日志**：
   - 后端记录数据源和值
   - 前端记录 FGI 值的来源

### 建议的改进

1. **数据源优先级调整**：
   - 考虑优先使用 feargreedmeter.com（如果它更准确）
   - 或者比较多个数据源，选择最合理的值

2. **值验证**：
   - 如果值变化超过阈值（例如从 11 跳到 50），记录警告
   - 允许用户选择数据源

3. **缓存策略**：
   - 如果值变化太大，可能需要重新获取
   - 显示数据源信息，让用户知道值的来源

## 当前状态

- ✅ 前端分级逻辑已修复
- ✅ 后端使用统一分级标准
- ⚠️ 需要确认实际数据源返回的值

## 调试步骤

1. 检查后端日志，查看实际获取的 FGI 值：
   ```
   [FGI] Fetched from CNN JSON: value=50, label=NEUTRAL
   ```
   或
   ```
   [FGI] Fetched from feargreedmeter.com: value=11, label=EXTREME FEAR
   ```

2. 检查前端控制台，查看显示的 FGI 值：
   ```
   [F&G] Fetched: value=50, label=NEUTRAL
   ```

3. 如果值确实是 50，可能是：
   - 市场情绪确实发生了变化
   - CNN 数据源返回了不同的值
   - 数据源使用了不同的计算方法

## 下一步

1. 运行 `python scripts/test_api_fgi.py` 检查当前实际值
2. 检查后端日志，确认数据源
3. 如果值确实是 50，这是正常的市场数据变化
4. 如果值应该是 11，需要调整数据源优先级

