# AI-Trader MVP Architecture

## 系統架構概覽

本系統採用分層式多 Agent 架構，模擬真實交易團隊的協作模式。

```
┌─────────────────────────────────────────────┐
│              數據層 (Layer 1)                │
│                                             │
│  ┌─────────────┐                           │
│  │  yfinance   │ ◄─── 原始股票數據           │
│  └──────┬──────┘                           │
│         │                                   │
│         ↓                                   │
│  ┌─────────────┐                           │
│  │Market Agent │ ◄─── 數據整合與清洗         │
│  │(Data Parser)│                           │
│  └──────┬──────┘                           │
└─────────┼───────────────────────────────────┘
          │
          ↓ (結構化數據)
┌─────────┼───────────────────────────────────┐
│         │      分析層 (Layer 2)              │
│         │                                   │
│    ┌────┴──────────┐                       │
│    ↓               ↓                       │
│ ┌──────────┐   ┌──────────┐               │
│ │ Market   │◄──┤   Risk   │               │
│ │ Analyst  │──►│ Analyst  │               │
│ │          │   │          │               │
│ │(市場心理)  │   │(風險評估) │               │
│ └──────────┘   └──────────┘               │
│       ↕            ↕                       │
│    [對話與討論]                             │
└─────────┼───────────────────────────────────┘
          │
          ↓ (分析結果 + 對話記錄)
┌─────────┼───────────────────────────────────┐
│         │      決策層 (Layer 3)              │
│         │                                   │
│         ↓                                   │
│  ┌─────────────┐                           │
│  │   Trader    │ ◄─── 綜合決策與執行         │
│  │   Agent     │                           │
│  └──────┬──────┘                           │
│         │                                   │
│         ↓                                   │
│  [交易執行]                                 │
└─────────┼───────────────────────────────────┘
          │
          ↓
┌─────────┼───────────────────────────────────┐
│         │      反饋層 (Layer 4)              │
│         │                                   │
│         ↓                                   │
│  ┌─────────────┐                           │
│  │Performance  │ ◄─── 績效評估與策略調整     │
│  │   Agent     │                           │
│  └──────┬──────┘                           │
│         │                                   │
│         ↓                                   │
│  [反饋循環] ───────┐                        │
└────────────────────┼────────────────────────┘
                     │
                     └──► 回到 Trader Agent
```

---

## Agent 詳細說明

### 1. Market Agent (數據整合者)

**角色定位**: 數據工程師
**核心職責**: 將原始 yfinance 數據轉換為結構化、可分析的格式

#### 輸入
- 股票代碼列表 (e.g., ["AAPL", "MSFT", "GOOGL"])
- 日期範圍 (e.g., "2024-01-01" to "2024-01-31")

#### 處理流程
1. 從 yfinance 獲取原始 OHLCV 數據
2. 計算基本技術指標（MA, Volume 趨勢）
3. 數據清洗與驗證
4. 格式化為統一結構

#### 輸出
```json
{
  "date": "2024-01-15",
  "market_summary": {
    "total_stocks": 100,
    "gainers": 58,
    "losers": 42
  },
  "stocks": [
    {
      "symbol": "AAPL",
      "price": 185.50,
      "change_pct": 2.3,
      "volume": 50000000,
      "ma_20": 182.10,
      "ma_50": 178.90,
      "volatility": "medium"
    }
  ]
}
```

#### 重要原則
- **不做分析**: 只提供數據，不提供觀點
- **標準化**: 所有數據格式一致
- **完整性**: 確保數據完整無遺漏

---

### 2. Market Analyst (市場分析師)

**角色定位**: 市場心理專家
**核心職責**: 分析市場趨勢、心理、技術面狀態

#### 輸入
- Market Agent 的結構化數據報告

#### 分析維度
1. **趨勢分析**: 上升/下降/盤整
2. **市場情緒**: 樂觀/悲觀/中性
3. **技術形態**: 突破/回調/震盪
4. **成交量分析**: 資金流向
5. **熱點板塊**: 領漲/領跌股票

#### 輸出
```json
{
  "market_sentiment": "bullish",
  "confidence_level": 0.75,
  "trend_analysis": {
    "direction": "upward",
    "strength": "strong",
    "duration": "5 days"
  },
  "recommended_actions": {
    "buy": ["AAPL", "MSFT"],
    "sell": ["XYZ"],
    "hold": ["GOOGL"]
  },
  "key_observations": [
    "科技股持續強勢",
    "成交量放大，資金積極進場"
  ],
  "concerns": [
    "短期漲幅過大，需注意回調風險"
  ]
}
```

#### 分析風格
- 樂觀進取，尋找機會
- 關注技術面和市場心理
- 傾向於積極操作

---

### 3. Risk Analyst (風險分析師)

**角色定位**: 風險管理專家
**核心職責**: 評估風險、提供風控建議

#### 輸入
- Market Agent 的數據報告
- Market Analyst 的分析結果

#### 評估維度
1. **市場風險**: 波動率、Beta
2. **集中度風險**: 持倉分散度
3. **流動性風險**: 成交量分析
4. **極端風險**: 最大回撤可能
5. **資金管理**: 倉位控制

#### 輸出
```json
{
  "overall_risk_level": "medium",
  "risk_score": 6.5,
  "max_position_size": {
    "per_stock": 0.15,
    "total_equity": 0.60
  },
  "stop_loss_recommendations": {
    "AAPL": "5%",
    "MSFT": "7%"
  },
  "risk_warnings": [
    "AAPL 近期波動率上升",
    "市場整體風險偏高"
  ],
  "safe_stocks": ["MSFT", "GOOGL"],
  "high_risk_stocks": ["NVDA"],
  "diversification_advice": "建議增加防禦型股票"
}
```

#### 風控原則
- 保守謹慎，優先保護資本
- 關注下行風險
- 強調分散投資
- 傾向於控制倉位

---

### 4. Analyst Discussion (分析師對話)

**核心功能**: 促進 Market Analyst 和 Risk Analyst 的討論

#### 對話流程

```
Round 1:
  Market Analyst: "我看好 AAPL，建議買入 20%"
  Risk Analyst: "AAPL 波動率高，建議控制在 10%"

Round 2:
  Market Analyst: "理解風險，但技術面強勢，可否 15%？"
  Risk Analyst: "可以接受 15%，但需設定 5% 止損"

Round 3:
  Market Analyst: "同意，15% + 5% 止損"
  Risk Analyst: "確認，達成共識"

結果:
  - Action: BUY AAPL
  - Position: 15%
  - Stop Loss: 5%
  - Consensus: True
```

#### 對話規則
1. **最多 3 輪**: 避免過度討論
2. **尋求共識**: 目標是達成一致
3. **記錄分歧**: 如無法達成共識，記錄雙方觀點
4. **互相尊重**: 考慮對方專業意見

#### 輸出
```json
{
  "consensus_reached": true,
  "final_recommendation": {
    "action": "BUY",
    "symbol": "AAPL",
    "position_size": 0.15,
    "stop_loss": 0.05
  },
  "conversation_log": [
    {
      "round": 1,
      "market_analyst": "...",
      "risk_analyst": "..."
    }
  ],
  "disagreements": []
}
```

---

### 5. Trader Agent (決策執行者)

**角色定位**: 最終決策者與執行者
**核心職責**: 綜合所有信息，做出最終交易決策並執行

#### 輸入
- Market Agent 的數據報告
- Market Analyst 的分析
- Risk Analyst 的風控建議
- 分析師對話結果
- 當前投資組合狀態

#### 決策流程

```python
def make_decision(inputs):
    # 1. 審查數據完整性
    validate_market_data()
    
    # 2. 分析分析師意見
    market_view = inputs.market_analyst
    risk_view = inputs.risk_analyst
    
    # 3. 評估共識程度
    if consensus_reached:
        # 執行共識決策
        execute_consensus()
    else:
        # 權衡利弊，自主決策
        balance_views()
    
    # 4. 檢查資金與風控
    check_capital()
    apply_risk_limits()
    
    # 5. 最終決策
    decision = finalize_decision()
    
    # 6. 執行交易
    execute_trade(decision)
    
    # 7. 記錄推理鏈
    log_reasoning()
    
    return decision
```

#### 輸出
```json
{
  "date": "2024-01-15",
  "decision": "BUY",
  "symbol": "AAPL",
  "amount": 15,
  "price": 185.50,
  "position_size": 0.15,
  "reasoning": {
    "market_view": "技術面強勢，建議買入",
    "risk_view": "控制倉位在 15%，設定止損",
    "trader_judgment": "兩位分析師達成共識，執行買入",
    "final_rationale": "綜合考慮機會與風險，決定買入 AAPL 15 股"
  },
  "risk_management": {
    "stop_loss": "5%",
    "position_limit": "15%",
    "diversification_check": "passed"
  },
  "execution": {
    "status": "success",
    "executed_price": 185.50,
    "slippage": 0.00
  },
  "portfolio_after": {
    "cash": 7217.50,
    "positions": {
      "AAPL": 15
    },
    "total_value": 10000.00
  }
}
```

#### 決策原則
- **獨立判斷**: 最終決策權在 Trader
- **風險優先**: 寧可錯過機會，不可承擔過度風險
- **可追溯性**: 所有決策有清晰推理鏈
- **靈活性**: 根據市場變化調整策略

---

## 數據流動

### 完整交易循環 (Daily)

```
1. 市場開盤
   ↓
2. Market Agent 獲取數據
   yfinance → 原始數據 → 結構化報告
   ↓
3. 分析師分析
   Market Analyst → 市場分析
   Risk Analyst → 風險評估
   ↓
4. 分析師對話
   3 輪對話 → 達成共識 / 記錄分歧
   ↓
5. Trader 決策
   審查所有輸入 → 做出決策 → 確定交易
   ↓
6. 執行交易
   buy/sell → 更新投資組合 → 記錄日志
   ↓
7. 績效評估 (每週)
   計算回報 → 分析表現 → 調整策略
   ↓
8. 反饋循環
   調整風險偏好 → 優化決策流程
   ↓
9. 回到步驟 1 (下一個交易日)
```

---

## 關鍵設計原則

### 1. 職責分離
- 每個 Agent 有明確、單一的職責
- 避免職責重疊
- 清晰的輸入輸出邊界

### 2. 信息流動
- 數據從上到下流動
- 反饋從下到上流動
- 分析師橫向交流

### 3. 可追溯性
- 每個決策都有完整推理鏈
- 記錄所有對話和分析
- 便於事後復盤

### 4. 容錯機制
- 數據異常處理
- 分析師意見衝突處理
- 交易執行失敗處理

### 5. 可擴展性
- 易於添加新的分析師
- 易於替換數據源
- 易於調整決策流程

---

## 技術實現

### LangChain 組件

```python
# Market Agent - ReAct Agent
market_agent = create_react_agent(
    llm=ChatOpenAI(model="gpt-4"),
    tools=[fetch_stock_data, calculate_indicators],
    prompt=market_agent_prompt
)

# Market Analyst - ReAct Agent
market_analyst = create_react_agent(
    llm=ChatOpenAI(model="gpt-4"),
    tools=[analyze_trend, analyze_sentiment],
    prompt=market_analyst_prompt
)

# Risk Analyst - ReAct Agent
risk_analyst = create_react_agent(
    llm=ChatOpenAI(model="gpt-4"),
    tools=[calculate_volatility, assess_risk],
    prompt=risk_analyst_prompt
)

# Analyst Discussion - Multi-Agent Conversation
discussion = MultiAgentConversation(
    agents=[market_analyst, risk_analyst],
    max_rounds=3
)

# Trader Agent - ReAct Agent
trader_agent = create_react_agent(
    llm=ChatOpenAI(model="gpt-4"),
    tools=[buy_stock, sell_stock, get_portfolio],
    prompt=trader_agent_prompt
)
```

---

## 測試策略

### 單元測試
- 每個 Agent 獨立測試
- Tool 功能測試
- 數據格式驗證

### 集成測試
- Agent 間通訊測試
- 完整交易循環測試
- 錯誤處理測試

### 端到端測試
- 30 天回測
- 不同市場情況測試
- 績效指標驗證

---

## 未來擴展

### 短期 (MVP 後)
- 添加第三位分析師（基本面分析師）
- 支援更多技術指標
- 優化對話機制

### 中期
- 多市場支援（A 股、加密貨幣）
- 實時交易執行
- Web 界面展示

### 長期
- 強化學習優化
- 情緒分析整合
- 高頻交易支援

---

**版本**: MVP v1.0
**最後更新**: 2024-10-30
