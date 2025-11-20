# 净值图表显示为直线问题修复

## 问题描述

用户报告净值图表显示为一条直线，无法看到净值的变化。

## 问题分析

### 数据检查结果

✅ **数据记录正常**:
- 26 条记录（2025-11-20）
- 净值范围: $9,797.43 - $9,833.49
- 净值变化: $36.05
- 数据一致性: 通过

### 问题原因

**Y 轴范围设置问题**:
- 净值变化只有 $36.05（相对于 $9,800 左右）
- 如果 Y 轴自动设置为 0 - $10,000 的范围
- $36 的变化在 $10,000 的范围内几乎不可见
- 导致图表看起来像一条直线

## 解决方案

### 1. 智能 Y 轴范围设置

**修复逻辑**:
- 检测净值变化范围
- 如果范围 < $100，自动扩展 Y 轴范围
- 设置 `suggestedMin` 和 `suggestedMax`，让变化更明显
- 边距设置为变化范围的 50% 或至少 $50

**代码修复** (`frontend/monitor.html`):
```javascript
// 计算 Y 轴范围
if (valueRange < 100 && valueRange > 0) {
    const margin = Math.max(valueRange * 0.5, 50);
    yAxisMin = Math.max(0, minVal - margin);
    yAxisMax = maxVal + margin;
}
```

### 2. 数据验证增强

**添加的检查**:
- 验证数据有效性
- 检查值的变化范围
- 记录调试信息到控制台
- 警告用户如果所有值相同

### 3. 调试日志

**添加的日志**:
- 净值范围（最小值、最大值、变化范围）
- Y 轴设置（如果范围很小）
- 数据点数量
- 数据摘要（用于调试）

## 修复内容

### 文件修改

**`frontend/monitor.html`**:
1. ✅ 添加数据有效性检查
2. ✅ 计算 Y 轴范围（针对小范围优化）
3. ✅ 设置 `suggestedMin` 和 `suggestedMax`
4. ✅ 添加调试日志
5. ✅ 增强错误处理

### 更新机制验证

**图表更新频率**:
- ✅ 每 30 分钟自动更新一次
- ✅ 市场开盘时实时更新（每 30 秒更新价格，每 30 分钟更新图表）
- ✅ 市场收盘后显示历史数据

**数据获取**:
- ✅ 从 API `/api/portfolio/equity-history` 获取数据
- ✅ 支持时间范围过滤（day/week/month/custom）
- ✅ 数据缓存机制（`equityHistory` 全局变量）

## 验证步骤

### 1. 检查浏览器控制台

打开浏览器开发者工具（F12），查看控制台日志：
```
[Chart] Value range: min=$9797.43, max=$9833.49, range=$36.05
[Chart] Small range detected, expanding Y axis: 9777.43 - 9853.49
[Chart] Equity chart rendered with 26 points
[Chart] Data summary: {count: 26, min: "9797.43", max: "9833.49", ...}
```

### 2. 检查图表显示

- ✅ 图表应该显示净值变化曲线
- ✅ Y 轴范围应该适合显示变化（不是 0-$10,000）
- ✅ 可以看到净值从 $9,833 降至 $9,797 的变化

### 3. 手动刷新图表

如果图表仍然显示为直线：
1. 打开浏览器控制台（F12）
2. 执行：`renderEquityChart()`
3. 查看控制台日志
4. 检查是否有错误信息

### 4. 检查数据更新

**验证数据是否在更新**:
```javascript
// 在浏览器控制台执行
fetch('/api/portfolio/equity-history?limit=10')
  .then(r => r.json())
  .then(d => console.log('Latest records:', d.records.slice(-5)));
```

## 预期效果

修复后，图表应该：
1. ✅ 正确显示净值变化曲线
2. ✅ Y 轴范围适合显示变化（不是全范围）
3. ✅ 可以看到 $36 的变化
4. ✅ 图表每 30 分钟自动更新
5. ✅ 数据记录正常

## 如果问题仍然存在

### 检查清单

1. **清除浏览器缓存**
   - 按 Ctrl+Shift+R 强制刷新
   - 或清除浏览器缓存后重新加载

2. **检查 API 数据**
   ```bash
   python backend/scripts/test_equity_api.py
   ```

3. **检查浏览器控制台**
   - 查看是否有 JavaScript 错误
   - 查看图表渲染日志

4. **手动触发图表更新**
   - 在浏览器控制台执行：`renderEquityChart()`
   - 查看是否有错误

5. **检查时间范围选择**
   - 确保选择了正确的时间范围（Day/Week/Month）
   - 尝试切换到不同的时间范围

## 相关文件

- `frontend/monitor.html` - 前端图表代码（已修复）
- `backend/scripts/test_equity_api.py` - API 测试脚本
- `backend/scripts/analyze_equity_chart_data.py` - 数据分析脚本
- `docs/EQUITY_CHART_ANALYSIS_REPORT.md` - 数据分析报告

---

**最后更新**: 2025-01-28

