# 十月模拟测试指引

## 测试步骤

### 1. 启动后端和前端
```powershell
# 终端1: 启动后端
cd backend
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000

# 终端2: 启动前端
cd frontend
python -m http.server 8080
```

### 2. 访问前端
打开浏览器访问: `http://127.0.0.1:8080/monitor.html`

### 3. 启动十月模拟
- 点击 "Simulate October" 按钮
- 等待黄色进度条出现
- 模拟将每5分钟模拟一天，共22个交易日

### 4. 验证项目

#### ✅ 对话显示
- Overview页面应显示Agent对话
- 每个Agent应有专属图标（📊 📈 💬 ⚠️ 🤖）
- 对话应包含工具使用信息（news_scan, vix_term, fear_greed等）
- 对话应实时更新（每30秒刷新）

#### ✅ 交易生成
- Execution Details应显示交易记录
- 每个交易日至少应有1笔交易
- 交易状态应为 "FILLED"
- 交易价格应与yfinance历史数据匹配（±1%误差）

#### ✅ 持仓更新
- Total Asset应随交易更新
- Equity Value应反映持仓市值
- Positions表格应显示持仓详情
- Unrealized P&L应正确计算：`(current_price - avg_cost) * quantity`

#### ✅ 价格真实性验证
- 交易价格应基于yfinance历史数据
- 不应使用随机价格或demo价格
- 可通过以下命令验证：
```powershell
# 查看最近的交易记录
Get-Content backend\data\logs\trades.jsonl -Tail 10

# 对比yfinance历史价格（例如NVDA在2024-10-01）
python -c "import yfinance as yf; t = yf.Ticker('NVDA'); print(t.history(start='2024-10-01', end='2024-10-02')['Close'].iloc[0])"
```

### 5. 预期结果

#### 对话数量
- 每个交易日应有多个Agent对话
- 至少包含：DiscussionAgent, MarketAnalyst, RiskAnalyst, TraderAgent
- 工具使用记录应显示在对话中

#### 交易数量
- 总交易数：20-60笔（取决于市场条件和Agent决策）
- 每个交易日：1-5笔交易
- 买卖比例：根据市场信号动态调整

#### 持仓变化
- 初始持仓：可能为空或少量持仓
- 模拟过程中：持仓数量和种类应增加
- 最终持仓：反映Agent的交易决策

#### 性能表现
- 页面不应卡顿
- 刷新应流畅（60秒间隔）
- 对话列表应快速渲染（30条限制）

### 6. 常见问题

#### 问题1: 进度条消失
- **原因**: 后端状态更新延迟
- **解决**: 等待30秒，进度条应重新出现

#### 问题2: 没有交易生成
- **原因**: Agent过于保守或市场条件不佳
- **解决**: 检查 `backend/src/agents/trader_agent.py` 的阈值设置

#### 问题3: 价格不匹配
- **原因**: yfinance数据获取失败或使用fallback价格
- **解决**: 检查 `backend/data/logs/api_execution.log` 中的错误信息

#### 问题4: 对话不显示
- **原因**: `discussion_actions.jsonl` 未正确写入
- **解决**: 检查文件权限和日志目录是否存在

### 7. 验证脚本

运行以下Python脚本验证价格真实性：
```python
import json
import yfinance as yf
from pathlib import Path

# 读取交易记录
trades_file = Path("backend/data/logs/trades.jsonl")
trades = []
with trades_file.open() as f:
    for line in f:
        if line.strip():
            trades.append(json.loads(line))

# 验证最近5笔交易的价格
for trade in trades[-5:]:
    symbol = trade.get("symbol")
    price = trade.get("price") or trade.get("fill_price")
    date = trade.get("timestamp") or trade.get("date")
    
    if symbol and price and date:
        # 从yfinance获取历史价格
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=date[:10], end=date[:10])
        if not hist.empty:
            yf_price = hist['Close'].iloc[0]
            diff = abs(price - yf_price) / yf_price * 100
            print(f"{symbol} @ {date[:10]}: Trade={price:.2f}, YF={yf_price:.2f}, Diff={diff:.2f}%")
```

## 测试通过标准

✅ 所有检查项都通过
✅ 页面流畅无卡顿
✅ 对话和交易正确显示
✅ 价格基于真实历史数据
✅ 持仓和P&L正确更新

