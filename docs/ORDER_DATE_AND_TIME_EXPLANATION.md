# Order Date and Time Explanation

## 📅 Tomorrow Planning Orders

### Question 1: If I plan for tomorrow now, will `order_date` show tomorrow? What about `Time`?

**Answer:**

When you plan for tomorrow (after market close):

1. **`order_date`**: Will show **tomorrow's date** (or next trading day if tomorrow is a holiday)
   - Example: If today is 2025-11-13 (Thursday) and you plan after market close
   - `order_date` will be: `2025-11-14` (Friday)

2. **`Time` (placed_at)**: Will show **today's timestamp** (when the order was created)
   - Example: `2025-11-13T21:06:49` (today's time when you created the order)

**Code Reference:**
- `order_date` is set using `get_next_trading_day(date.today(), days_ahead=1)` in `trading_cycle.py:603`
- `placed_at` is set using `datetime.now().isoformat()` in `order_manager.py:69`

**Example Order Record:**
```json
{
  "order_id": "NVDA_BUY_2025-11-14_...",
  "symbol": "NVDA",
  "action": "BUY",
  "order_date": "2025-11-14",  // Tomorrow's date
  "placed_at": "2025-11-13T21:06:49",  // Today's timestamp
  "status": "PENDING"
}
```

---

## 🎄 Holiday Handling

### Question 2: What happens if tomorrow is a holiday?

**Answer:**

The system automatically skips holidays and weekends:

1. **Holiday Detection**: Uses `get_next_trading_day()` which:
   - Skips weekends (Saturday, Sunday)
   - Skips US market holidays (New Year's Day, Independence Day, Christmas, Thanksgiving, Labor Day, Memorial Day, MLK Day, Presidents Day, Columbus Day)

2. **Automatic Adjustment**: If tomorrow is a holiday, `order_date` will be set to the **next trading day** after the holiday

**Example Scenarios:**

**Scenario A: Tomorrow is Friday (normal)**
- Today: Thursday 2025-11-13
- Tomorrow: Friday 2025-11-14 (trading day)
- `order_date`: `2025-11-14` ✅

**Scenario B: Tomorrow is Saturday**
- Today: Friday 2025-11-14
- Tomorrow: Saturday 2025-11-15 (weekend)
- Next trading day: Monday 2025-11-17
- `order_date`: `2025-11-17` ✅ (skips weekend)

**Scenario C: Tomorrow is a Holiday (e.g., Thanksgiving)**
- Today: Wednesday 2025-11-26
- Tomorrow: Thursday 2025-11-27 (Thanksgiving - holiday)
- Next trading day: Friday 2025-11-28
- `order_date`: `2025-11-28` ✅ (skips holiday)

**Code Reference:**
- `backend/src/utils/trading_days.py`:
  - `is_trading_day()`: Checks if a date is a trading day
  - `get_next_trading_day()`: Finds the next trading day, skipping weekends and holidays

**Holiday List (US Market):**
- Fixed holidays: New Year's Day (Jan 1), Independence Day (Jul 4), Christmas (Dec 25)
- Variable holidays: Thanksgiving (Nov 4th Thursday), Labor Day (Sep 1st Monday), Memorial Day (May last Monday), MLK Day (Jan 3rd Monday), Presidents Day (Feb 3rd Monday), Columbus Day (Oct 2nd Monday)

---

## 📊 Frontend Display

In the frontend (`monitor.html`), the Execution Details table shows:

- **TIME**: Shows `placed_at` timestamp (when order was created - today)
- **ORDER DATE**: Shows `order_date` (target trading day - tomorrow or next trading day)

**Example Display:**
```
TIME: 11/13, 21:06:49  (today when you created the order)
ORDER DATE: 2025/11/14  (tomorrow - when order will be executed)
```

---

## 🔍 Verification

To verify the next trading day calculation:

```python
from backend.src.utils.trading_days import get_next_trading_day
from datetime import date

# Get next trading day
next_day = get_next_trading_day(date.today(), days_ahead=1)
print(f"Next trading day: {next_day}")
```

---

**Last Updated**: 2025-11-13

