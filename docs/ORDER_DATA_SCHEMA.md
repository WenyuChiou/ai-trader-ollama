# 訂單數據結構標準化文檔

## 概述

本文檔定義了訂單數據的標準化結構，確保所有訂單記錄都遵循統一的格式，以便於 Performance Analysis 和其他分析工具使用。

## 訂單數據結構

### 1. PENDING 訂單（待處理訂單）

```json
{
  "order_id": "SYMBOL_ACTION_DATE_TIMESTAMP",
  "symbol": "AAPL",
  "action": "BUY" | "SELL",
  "quantity": 10,
  "limit_price": 150.0,
  "price_range": {
    "min": 149.0,
    "max": 151.0
  },
  "placed_at": "2025-01-19T10:30:00.123Z",  // ISO 8601 UTC 格式
  "status": "PENDING"
}
```

### 2. FILLED 訂單（已成交訂單）

#### BUY 訂單結構

```json
{
  "order_id": "SYMBOL_ACTION_DATE_TIMESTAMP",
  "symbol": "AAPL",
  "action": "BUY",
  "quantity": 10,
  "limit_price": 150.0,
  "price_range": {
    "min": 149.0,
    "max": 151.0
  },
  "placed_at": "2025-01-19T10:30:00.123Z",
  "status": "FILLED",
  "fill_price": 150.5,
  "fill_reason": "Order filled within price range",
  "daily_high": 151.0,
  "daily_low": 149.5,
  "filled_at": "2025-01-19T10:35:00.456Z",
  "fill_result": {
    "filled": true,
    "fill_price": 150.5,
    "fill_reason": "Order filled within price range",
    "daily_high": 151.0,
    "daily_low": 149.5,
    "current_price": 150.5
  }
}
```

#### SELL 訂單結構（包含實現損益）

```json
{
  "order_id": "SYMBOL_ACTION_DATE_TIMESTAMP",
  "symbol": "AAPL",
  "action": "SELL",
  "quantity": 10,
  "limit_price": 155.0,
  "price_range": {
    "min": 154.0,
    "max": 156.0
  },
  "placed_at": "2025-01-19T10:30:00.123Z",
  "status": "FILLED",
  "fill_price": 155.5,
  "fill_reason": "Order filled within price range",
  "daily_high": 156.0,
  "daily_low": 154.5,
  "filled_at": "2025-01-19T14:20:00.789Z",
  
  // CRITICAL: 實現損益字段（僅 SELL 訂單）
  "realized_pnl": 50.0,              // 已實現損益（金額）
  "realized_pnl_pct": 3.33,          // 已實現損益（百分比）
  "cost_basis": 1500.0,              // 成本基礎（買入成本）
  "proceeds": 1550.0,                // 賣出收益
  
  "fill_result": {
    "filled": true,
    "fill_price": 155.5,
    "fill_reason": "Order filled within price range",
    "daily_high": 156.0,
    "daily_low": 154.5,
    "current_price": 155.5,
    
    // CRITICAL: 實現損益也保存在 fill_result 中（便於查詢）
    "realized_pnl": 50.0,
    "realized_pnl_pct": 3.33,
    "cost_basis": 1500.0,
    "proceeds": 1550.0
  }
}
```

## 字段說明

### 通用字段

| 字段 | 類型 | 說明 | 必填 |
|------|------|------|------|
| `order_id` | string | 訂單唯一標識符 | ✅ |
| `symbol` | string | 股票代碼 | ✅ |
| `action` | string | 操作類型：`BUY` 或 `SELL` | ✅ |
| `quantity` | integer | 數量 | ✅ |
| `limit_price` | float | 限價 | ✅ |
| `price_range` | object | 價格範圍 `{min: float, max: float}` | ✅ |
| `placed_at` | string | 下單時間（ISO 8601 UTC） | ✅ |
| `status` | string | 訂單狀態：`PENDING` / `FILLED` / `REJECTED` | ✅ |

### FILLED 訂單專用字段

| 字段 | 類型 | 說明 | 必填 |
|------|------|------|------|
| `fill_price` | float | 成交價格 | ✅ (FILLED) |
| `fill_reason` | string | 成交原因 | ✅ (FILLED) |
| `daily_high` | float | 當日最高價 | ✅ (FILLED) |
| `daily_low` | float | 當日最低價 | ✅ (FILLED) |
| `filled_at` | string | 成交時間（ISO 8601 UTC） | ✅ (FILLED) |
| `fill_result` | object | 完整的成交結果對象 | ✅ (FILLED) |

### SELL 訂單專用字段（實現損益）

| 字段 | 類型 | 說明 | 必填 | 計算公式 |
|------|------|------|------|----------|
| `realized_pnl` | float | 已實現損益（金額） | ✅ (SELL) | `proceeds - cost_basis` |
| `realized_pnl_pct` | float | 已實現損益（百分比） | ✅ (SELL) | `(realized_pnl / cost_basis) * 100` |
| `cost_basis` | float | 成本基礎（買入成本） | ✅ (SELL) | `avg_cost * quantity` |
| `proceeds` | float | 賣出收益 | ✅ (SELL) | `fill_price * quantity` |

## 數據標準化規則

### 1. 時間戳格式
- **格式**：ISO 8601 UTC 格式，包含 `Z` 後綴
- **範例**：`2025-01-19T10:30:00.123Z`
- **要求**：所有時間字段必須使用 UTC 時區

### 2. 數值精度
- **價格**：保留 2 位小數
- **百分比**：保留 2 位小數
- **數量**：整數

### 3. 實現損益計算
- **計算時機**：僅在 SELL 訂單成交時計算
- **計算方法**：使用 FIFO 方法，基於平均成本
- **存儲位置**：同時保存在訂單頂層和 `fill_result` 中

### 4. 數據完整性
- **SELL 訂單**：必須包含所有實現損益字段
- **BUY 訂單**：不包含實現損益字段
- **PENDING 訂單**：不包含成交相關字段

## Performance Analysis 使用

### 統計計算

Performance Analysis 使用以下字段進行計算：

1. **總實現損益**：
   ```python
   total_realized_pnl = sum(o.get("realized_pnl", 0.0) for o in sell_orders)
   ```

2. **勝率**：
   ```python
   winning_trades = len([o for o in sell_orders if o.get("realized_pnl", 0.0) > 0])
   win_rate = (winning_trades / total_trades) * 100.0
   ```

3. **平均交易回報**：
   ```python
   avg_trade_return = total_realized_pnl / total_trades
   ```

4. **Symbol 統計**：
   - 總買入成本：`sum(fill_price * quantity for buy_orders)`
   - 總賣出收益：`sum(fill_price * quantity for sell_orders)`
   - Symbol 實現損益：`sum(realized_pnl for sell_orders)`

### 數據驗證

在 Performance Analysis 中，會進行以下驗證：

1. **SELL 訂單必須有 `realized_pnl`**：
   ```python
   sell_orders = [o for o in filled_orders 
                  if o.get("action") == "SELL" 
                  and o.get("realized_pnl") is not None]
   ```

2. **數值類型轉換**：
   ```python
   float(o.get("realized_pnl", 0.0))  # 確保為 float 類型
   ```

3. **缺失字段處理**：
   - 如果 `realized_pnl` 缺失，使用 `0.0` 作為默認值
   - 如果 `cost_basis` 缺失，從 `fill_price * quantity` 計算

## 遷移和兼容性

### 舊數據遷移

如果遇到舊格式的訂單數據（缺少 `realized_pnl` 字段），可以：

1. **從 `fill_result` 中提取**：
   ```python
   realized_pnl = order.get("realized_pnl") or order.get("fill_result", {}).get("realized_pnl", 0.0)
   ```

2. **重新計算**（如果可能）：
   ```python
   if not order.get("realized_pnl") and order.get("action") == "SELL":
       # 嘗試從歷史 BUY 訂單計算
       cost_basis = calculate_cost_basis_from_history(symbol, quantity)
       proceeds = order.get("fill_price", 0.0) * order.get("quantity", 0)
       realized_pnl = proceeds - cost_basis
   ```

## 最佳實踐

1. **始終使用標準化字段**：確保所有訂單都包含標準字段
2. **驗證數據完整性**：在寫入訂單前驗證必填字段
3. **錯誤處理**：對於缺失字段，使用合理的默認值
4. **日誌記錄**：記錄所有實現損益計算過程，便於調試
5. **數據備份**：定期備份訂單數據，防止數據丟失

## 相關文件

- `backend/src/data/order_manager.py` - 訂單管理邏輯
- `backend/src/data/portfolio.py` - 投資組合和損益計算
- `backend/src/api/performance.py` - Performance Analysis 實現
- `backend/src/api/server.py` - API 端點實現

