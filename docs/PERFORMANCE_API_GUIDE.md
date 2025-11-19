# Performance API 使用指南

## API 端點

### 1. `/api/performance/statistics` - 整體績效統計

**請求方式**: `GET`

**參數**:
- `start_date` (可選): 開始日期 (YYYY-MM-DD)，預設為7天前
- `end_date` (可選): 結束日期 (YYYY-MM-DD)，預設為今天

**範例**:
```
GET /api/performance/statistics?start_date=2025-11-12&end_date=2025-11-19
```

**返回數據結構**:
```json
{
  "ok": true,
  "statistics": {
    "initial_value": 10000.0,           // 初始投資金額
    "current_value": 9960.11,            // 當前投資組合價值
    "total_return": -39.89,              // 總回報（美元）
    "total_return_pct": -0.40,           // 總回報百分比
    "annualized_return_pct": 0.0,        // 年化回報百分比
    "max_drawdown": 100.0,               // 最大回撤（美元）
    "max_drawdown_pct": 1.0,             // 最大回撤百分比
    "win_rate": 100.0,                   // 勝率（%）
    "total_trades": 2,                   // 總交易數（SELL訂單數）
    "winning_trades": 2,                 // 獲勝交易數
    "losing_trades": 0,                  // 失敗交易數
    "total_realized_pnl": 100.0,         // 總已實現損益（美元）
    "avg_trade_return": 50.0,            // 平均交易回報（美元）
    "sharpe_ratio": 0.0,                 // Sharpe Ratio（風險調整後回報）
    "sortino_ratio": 0.0,                // Sortino Ratio（只考慮下行風險）
    "calmar_ratio": 0.0,                 // Calmar Ratio（年化回報/最大回撤）
    "avg_holding_days": 5.0,             // 平均持倉天數
    "best_trade": {                      // 最佳交易
      "symbol": "MSFT",
      "realized_pnl": 50.0,
      "realized_pnl_pct": 2.63
    },
    "worst_trade": {                     // 最差交易
      "symbol": "MSFT",
      "realized_pnl": 50.0,
      "realized_pnl_pct": 2.63
    },
    "trading_days": 7,                   // 交易天數
    "data_points": 1                     // 數據點數（equity history記錄數）
  },
  "period": {
    "start_date": "2025-11-12",
    "end_date": "2025-11-19"
  }
}
```

**關鍵指標說明**:
- **total_realized_pnl**: 所有 SELL 訂單的已實現損益總和（來自 `realized_pnl` 字段）
- **win_rate**: 基於 SELL 訂單的 `realized_pnl` 計算（>0 為獲勝）
- **best_trade / worst_trade**: 基於 SELL 訂單的 `realized_pnl` 和 `realized_pnl_pct` 識別

---

### 2. `/api/performance/trades-by-date` - 按日期分組的交易

**請求方式**: `GET`

**參數**:
- `start_date` (可選): 開始日期 (YYYY-MM-DD)
- `end_date` (可選): 結束日期 (YYYY-MM-DD)
- `limit` (可選): 限制返回的日期數量（1-1000）

**範例**:
```
GET /api/performance/trades-by-date?start_date=2025-11-12&end_date=2025-11-19
```

**返回數據結構**:
```json
{
  "ok": true,
  "trades_by_date": [
    {
      "date": "2025-11-19",
      "buy_orders": [
        {
          "order_id": "AAPL_BUY_2025-11-19_...",
          "symbol": "AAPL",
          "action": "BUY",
          "quantity": 10,
          "fill_price": 150.50,
          "placed_at": "2025-11-19T20:56:53.633Z",
          "filled_at": "2025-11-19T20:56:53.634Z"
        }
      ],
      "sell_orders": [
        {
          "order_id": "MSFT_SELL_2025-11-19_...",
          "symbol": "MSFT",
          "action": "SELL",
          "quantity": 5,
          "fill_price": 380.00,
          "placed_at": "2025-11-19T20:56:53.646Z",
          "filled_at": "2025-11-19T20:56:53.646Z",
          "realized_pnl": 50.0,           // 已實現損益
          "realized_pnl_pct": 2.63,       // 已實現損益百分比
          "cost_basis": 370.0,             // 成本基礎
          "proceeds": 1900.0               // 收益
        }
      ],
      "total_buy_cost": 1505.0,           // 當日總買入成本
      "total_sell_proceeds": 1900.0,      // 當日總賣出收益
      "net_realized_pnl": 50.0            // 當日淨已實現損益
    }
  ],
  "total_dates": 1,
  "total_orders": 4
}
```

**關鍵字段說明**:
- **sell_orders**: 包含完整的 P&L 信息（`realized_pnl`, `realized_pnl_pct`, `cost_basis`, `proceeds`）
- **net_realized_pnl**: 當日所有 SELL 訂單的已實現損益總和

---

### 3. `/api/performance/symbol-analysis` - 符號級別分析

**請求方式**: `GET`

**參數**:
- `symbol` (可選): 股票代碼，如果不提供則返回所有符號
- `start_date` (可選): 開始日期 (YYYY-MM-DD)
- `end_date` (可選): 結束日期 (YYYY-MM-DD)

**範例1 - 所有符號**:
```
GET /api/performance/symbol-analysis?start_date=2025-11-12&end_date=2025-11-19
```

**範例2 - 特定符號**:
```
GET /api/performance/symbol-analysis?symbol=AAPL&start_date=2025-11-12&end_date=2025-11-19
```

**返回數據結構（所有符號）**:
```json
{
  "ok": true,
  "symbols": [
    {
      "symbol": "AAPL",
      "total_trades": 2,
      "buy_orders": 2,
      "sell_orders": 0,
      "total_buy_quantity": 20.0,
      "total_sell_quantity": 0.0,
      "total_buy_cost": 3010.0,
      "total_sell_proceeds": 0.0,
      "total_realized_pnl": 0.0,
      "win_rate": 0.0,
      "avg_holding_days": null
    },
    {
      "symbol": "MSFT",
      "total_trades": 2,
      "buy_orders": 0,
      "sell_orders": 2,
      "total_buy_quantity": 0.0,
      "total_sell_quantity": 10.0,
      "total_buy_cost": 0.0,
      "total_sell_proceeds": 3800.0,
      "total_realized_pnl": 100.0,        // 總已實現損益
      "win_rate": 100.0,                  // 勝率（基於 realized_pnl > 0）
      "avg_holding_days": null
    }
  ],
  "total_symbols": 2
}
```

**返回數據結構（特定符號）**:
```json
{
  "ok": true,
  "symbol": {
    "symbol": "MSFT",
    "total_trades": 2,
    "buy_orders": 0,
    "sell_orders": 2,
    "total_buy_quantity": 0.0,
    "total_sell_quantity": 10.0,
    "total_buy_cost": 0.0,
    "total_sell_proceeds": 3800.0,
    "total_realized_pnl": 100.0,          // 基於 SELL 訂單的 realized_pnl
    "win_rate": 100.0,                    // 基於 realized_pnl > 0 計算
    "avg_holding_days": null
  }
}
```

**關鍵字段說明**:
- **total_realized_pnl**: 該符號所有 SELL 訂單的 `realized_pnl` 總和
- **win_rate**: 基於 SELL 訂單的 `realized_pnl` 計算（>0 為獲勝）
- **total_buy_cost**: 所有 BUY 訂單的 `fill_price * quantity` 總和
- **total_sell_proceeds**: 所有 SELL 訂單的 `fill_price * quantity` 總和（或使用 `proceeds` 字段）

---

## 數據來源

所有 Performance API 都從 `filled_orders.jsonl` 讀取訂單數據，並使用 `normalize_order()` 標準化：

1. **訂單標準化**: 確保所有字段符合標準格式
2. **P&L 字段**: SELL 訂單必須包含 `realized_pnl`, `realized_pnl_pct`, `cost_basis`, `proceeds`
3. **時間戳格式**: ISO 8601 UTC 格式（帶 Z 後綴）

---

## 預期看到的數據

### 1. 整體統計 (`/api/performance/statistics`)
- ✅ 總回報和百分比
- ✅ 勝率（基於 SELL 訂單的 `realized_pnl`）
- ✅ 總已實現損益（所有 SELL 訂單的 `realized_pnl` 總和）
- ✅ 平均交易回報
- ✅ 最佳/最差交易（基於 `realized_pnl` 和 `realized_pnl_pct`）
- ✅ Sharpe/Sortino/Calmar Ratio（如果有足夠的 equity history）
- ✅ 最大回撤（基於 equity history）

### 2. 按日期分組 (`/api/performance/trades-by-date`)
- ✅ 每日的 BUY/SELL 訂單列表
- ✅ SELL 訂單的完整 P&L 信息
- ✅ 每日淨已實現損益

### 3. 符號分析 (`/api/performance/symbol-analysis`)
- ✅ 每個符號的交易統計
- ✅ 買入/賣出數量和成本
- ✅ 符號級別的已實現損益
- ✅ 符號級別的勝率

---

## 注意事項

1. **SELL 訂單必須有 P&L**: 只有包含 `realized_pnl` 的 SELL 訂單才會被用於計算勝率和統計
2. **日期範圍**: 預設查詢最近7天，需要歷史數據請明確指定日期範圍
3. **Equity History**: Sharpe Ratio 等指標需要 `equity_history.jsonl` 數據
4. **數據標準化**: 所有訂單都會自動標準化，確保字段完整

