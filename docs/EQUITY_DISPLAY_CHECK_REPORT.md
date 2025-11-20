# 净值显示和记录检查报告

## 检查日期
2025-01-28

## 检查内容

### 1. 后端数据记录检查

#### ✅ equity_history.jsonl 文件
- **状态**: 正常
- **记录数**: 1 条
- **数据格式**: 正确
  - 包含所有必需字段：`date`, `timestamp`, `total_value`, `cash`, `equity_value`
  - `timestamp` 格式正确（ISO 8601 UTC，带 'Z' 后缀）
  - 数值一致性检查通过：`total_value = cash + equity_value`

#### ✅ EquityTracker API
- **状态**: 正常
- **功能**: 正确加载和返回净值历史数据
- **数据格式**: 所有记录格式正确

#### ✅ portfolio_state.json 文件
- **状态**: 正常
- **数据一致性**: 通过
  - `total_value (10000.00) = cash (10000.00) + equity_value (0.00)`

### 2. 前端显示检查

#### ✅ 净值图表显示
- **主图表**: `renderEquityChart()` 使用 Chart.js 显示净值曲线
- **数据获取**: `fetchEquityHistory()` 正确从 API 获取数据
- **字段映射**: 
  - 优先使用 `total_value`
  - 后备使用 `value` 或 `equity_value`
- **修复**: 已更新代码确保优先使用 `total_value` 字段

#### ✅ Performance 页面图表
- **图表**: `renderEquityValueChart()` 显示净值曲线
- **数据格式**: 正确映射 `total_value` 字段

#### ⚠️ SVG 图表函数（已修复）
- **函数**: `drawChart()` 
- **问题**: 仅使用 `d.value` 字段
- **修复**: 已更新为优先使用 `total_value`，然后是 `value`，最后是 `equity_value`

## 数据流验证

### 记录流程
1. **前端记录**: `recordEquityToBackend()` → POST `/api/portfolio/record-equity`
2. **后端处理**: `EquityTracker.record_daily_equity()` → 写入 `equity_history.jsonl`
3. **数据格式**: 
   ```json
   {
     "date": "YYYY-MM-DD",
     "timestamp": "YYYY-MM-DDTHH:MM:SS.fffZ",
     "cash": float,
     "equity_value": float,
     "total_value": float,
     "total_pnl": float,
     "total_pnl_pct": float,
     "positions": {}
   }
   ```

### 显示流程
1. **前端获取**: `fetchEquityHistory()` → GET `/api/portfolio/equity-history`
2. **后端返回**: `EquityTracker.load_equity_history()` → 返回格式化的记录列表
3. **前端显示**: `renderEquityChart()` → Chart.js 渲染净值曲线

## 修复内容

### 1. 前端代码修复

#### `frontend/monitor.html`

**修复 1**: `renderEquityChart()` 函数
```javascript
// 修复前
const values = equityData.map(item => item.value || item.total_value || item.equity || 0);

// 修复后
const values = equityData.map(item => item.total_value || item.value || item.equity_value || item.equity || 0);
```

**修复 2**: `drawChart()` 函数
```javascript
// 修复前
const values = sorted.map(d => d.value);
const y = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight;

// 修复后
const values = sorted.map(d => d.total_value || d.value || d.equity_value || 0);
const pointValue = point.total_value || point.value || point.equity_value || 0;
const y = padding.top + chartHeight - ((pointValue - minValue) / valueRange) * chartHeight;
```

## 检查工具

创建了检查脚本：`backend/scripts/check_equity_display.py`

**功能**:
- 检查 `equity_history.jsonl` 文件格式
- 验证 EquityTracker API 返回数据
- 检查 `portfolio_state.json` 数据一致性
- 验证时间戳格式
- 验证数值一致性

**使用方法**:
```bash
cd backend
python scripts/check_equity_display.py
```

## 结论

✅ **所有检查通过**

净值显示和记录功能正常：
1. ✅ 后端正确记录净值到 `equity_history.jsonl`
2. ✅ API 正确返回净值历史数据
3. ✅ 前端正确显示净值图表
4. ✅ 数据格式一致性和完整性验证通过

## 建议

1. **定期运行检查脚本**: 建议在每次交易周期后运行检查脚本，确保数据完整性
2. **监控净值记录**: 关注净值记录的频率（每30分钟一次）
3. **数据备份**: 定期备份 `equity_history.jsonl` 文件
4. **前端测试**: 在不同浏览器中测试净值图表显示是否正常

## 相关文件

- `backend/src/data/equity_tracker.py` - 净值追踪器
- `backend/src/api/server.py` - API 端点
- `frontend/monitor.html` - 前端显示代码
- `backend/scripts/check_equity_display.py` - 检查脚本
- `backend/data/logs/equity_history.jsonl` - 净值历史数据
- `backend/data/logs/portfolio_state.json` - 投资组合状态

