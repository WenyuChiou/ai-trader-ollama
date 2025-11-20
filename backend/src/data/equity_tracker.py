# src/data/equity_tracker.py
"""
每日净值追踪器
记录每日的净值、盈亏、持仓等信息，用于前端展示净值曲线图
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timezone
from src.utils.timestamp_utils import get_utc_timestamp, normalize_timestamp, ensure_timestamp_has_z_suffix


class EquityTracker:
    """
    追踪每日净值变化
    
    数据格式（JSONL）:
    {
      "date": "2025-01-28",
      "timestamp": "2025-01-28T10:00:00",
      "cash": 2197.50,
      "equity_value": 6300.00,
      "total_value": 8497.50,
      "total_pnl": -2.50,
      "total_pnl_pct": -0.03,
      "positions": {
        "NVDA": {
          "quantity": 10,
          "avg_cost": 150.25,
          "current_price": 150.25,
          "market_value": 1502.50,
          "unrealized_pnl": 0.00,
          "unrealized_pnl_pct": 0.00
        }
      }
    }
    """
    
    def __init__(self, root: str | Path = "data/logs"):
        """
        初始化 Equity Tracker
        
        参数:
        - root: 日志根目录
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.equity_file = self.root / "equity_history.jsonl"
    
    def record_daily_equity(
        self,
        date_str: str,
        portfolio_snapshot: Dict[str, Any],
    ) -> None:
        """
        记录每日净值
        
        参数:
        - date_str: 日期 (YYYY-MM-DD)
        - portfolio_snapshot: Portfolio 快照（从 trading_cycle 返回的 portfolio 字段）
        
        注意：只在市场开盘时记录（9:30 AM - 4:00 PM ET），收盘后不记录
        """
        # CRITICAL: 检查市场是否开盘，收盘后不记录
        try:
            from src.utils.trading_days import is_market_open
            if not is_market_open(None):
                print(f"[EQUITY] Market is closed, skipping equity recording (will resume at next market open)")
                return
        except Exception as e:
            print(f"[EQUITY WARNING] Failed to check market status: {e}, proceeding with record")
        
        # CRITICAL FIX: 如果portfolio_snapshot包含snapshot字段，优先使用snapshot的值
        # 这样可以正确处理从portfolio_state.json加载的数据结构
        snapshot = portfolio_snapshot.get("snapshot", {})
        if snapshot:
            # 使用snapshot字段的值（优先级更高）
            current_value = float(snapshot.get("total_value", portfolio_snapshot.get("total_value", 0.0)))
            current_cash = float(snapshot.get("cash", portfolio_snapshot.get("cash", 0.0)))
            current_equity = float(snapshot.get("equity_value", portfolio_snapshot.get("equity_value", 0.0)))
            # positions_detail可能在顶层或snapshot中
            positions = snapshot.get("positions_detail", portfolio_snapshot.get("positions_detail", {}))
        else:
            # 没有snapshot字段，使用顶层字段
            current_value = float(portfolio_snapshot.get("total_value", 0.0))
            current_cash = float(portfolio_snapshot.get("cash", 0.0))
            current_equity = float(portfolio_snapshot.get("equity_value", 0.0))
            positions = portfolio_snapshot.get("positions_detail", {})
        
        # CRITICAL FIX: Ensure positions have current_price and market_value when recording
        # If positions are missing price information, fetch real-time prices (market open only)
        positions_need_price_update = False
        if positions:
            for symbol, pos_info in positions.items():
                if isinstance(pos_info, dict):
                    # Check if current_price is missing or equals avg_cost (indicating stale/cached price)
                    current_price = pos_info.get("current_price")
                    avg_cost = pos_info.get("avg_cost", 0)
                    market_value = pos_info.get("market_value")
                    
                    # If price is missing or equals avg_cost, we need to fetch real-time price
                    if current_price is None or (current_price == avg_cost and avg_cost > 0):
                        positions_need_price_update = True
                        print(f"[EQUITY] Position {symbol} missing current_price or using cached price (equals avg_cost)")
                        break
        
        # Fetch real-time prices if needed and market is open
        if positions_need_price_update:
            try:
                from src.utils.trading_days import is_market_open
                if is_market_open(None):
                    print(f"[EQUITY] Fetching real-time prices for {len(positions)} positions...")
                    import yfinance as yf
                    
                    symbols = list(positions.keys())
                    updated_count = 0
                    
                    # Fetch prices in batch
                    try:
                        tickers = yf.Tickers(" ".join(symbols))
                        for symbol in symbols:
                            try:
                                ticker = tickers.tickers[symbol]
                                info = ticker.fast_info
                                
                                # Get current price (real-time during market hours, close price otherwise)
                                price = info.get("lastPrice") or info.get("regularMarketPrice") or info.get("previousClose")
                                
                                if price and price > 0:
                                    pos_info = positions[symbol]
                                    if isinstance(pos_info, dict):
                                        quantity = pos_info.get("quantity", 0)
                                        avg_cost = pos_info.get("avg_cost", 0)
                                        
                                        # Update position with real-time price
                                        pos_info["current_price"] = float(price)
                                        pos_info["market_value"] = quantity * float(price)
                                        pos_info["unrealized_pnl"] = (float(price) - avg_cost) * quantity
                                        pos_info["unrealized_pnl_pct"] = ((float(price) - avg_cost) / avg_cost * 100.0) if avg_cost > 0 else 0.0
                                        
                                        updated_count += 1
                                        print(f"[EQUITY] Updated {symbol}: price=${price:.2f}, market_value=${pos_info['market_value']:.2f}")
                            except Exception as e:
                                print(f"[EQUITY WARNING] Failed to fetch price for {symbol}: {e}")
                        
                        if updated_count > 0:
                            # Recalculate equity_value and total_value with updated prices
                            new_equity_value = sum(
                                pos.get("market_value", 0) 
                                for pos in positions.values() 
                                if isinstance(pos, dict)
                            )
                            current_equity = new_equity_value
                            current_value = current_cash + current_equity
                            print(f"[EQUITY] Recalculated values: equity=${current_equity:.2f}, total=${current_value:.2f} (updated {updated_count}/{len(symbols)} prices)")
                    except Exception as e:
                        print(f"[EQUITY WARNING] Failed to fetch batch prices: {e}")
                        # Log error to error logger
                        try:
                            from src.utils.error_logger import get_error_logger, ErrorLevel
                            error_logger = get_error_logger(root=str(self.root))
                            error_logger.error(
                                message="Failed to fetch batch prices for equity recording",
                                component="equity_tracker",
                                exception=e,
                                context={"function": "record_daily_equity", "symbols_count": len(positions)}
                            )
                        except Exception:
                            pass  # Ignore logging errors
                else:
                    print(f"[EQUITY] Market is closed, skipping real-time price fetch (using provided prices)")
            except Exception as e:
                print(f"[EQUITY WARNING] Failed to check market status for price update: {e}")
        
        # CRITICAL FIX: 保留所有时间戳记录，不再按日期去重
        # 每30分钟的记录都会被保留，确保历史数据完整性
        
        # CRITICAL: 检查净值是否异常下降（防止记录错误数据）
        # 同时验证portfolio_state.json中的实际状态，确保数据一致性
        if self.equity_file.exists():
            try:
                # 读取最后一条记录
                with self.equity_file.open("r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last_record = json.loads(lines[-1].strip())
                        last_value = float(last_record.get("total_value", 0))
                        last_positions = last_record.get("positions", {})
                        
                        # 验证portfolio_state.json中的实际状态
                        portfolio_state_file = self.root / "portfolio_state.json"
                        if portfolio_state_file.exists():
                            try:
                                with portfolio_state_file.open("r", encoding="utf-8") as pf:
                                    portfolio_state = json.load(pf)
                                portfolio_cash = float(portfolio_state.get("cash", 0))
                                portfolio_positions = portfolio_state.get("positions", {})
                                
                                # 如果portfolio_state.json中的状态与要记录的状态不一致，使用portfolio_state.json的状态
                                if portfolio_cash != current_cash or len(portfolio_positions) != len(positions):
                                    print(f"[EQUITY WARNING] Portfolio state mismatch detected!")
                                    print(f"[EQUITY WARNING] Recorded state: cash=${current_cash:.2f}, positions={len(positions)}")
                                    print(f"[EQUITY WARNING] Portfolio file: cash=${portfolio_cash:.2f}, positions={len(portfolio_positions)}")
                                    print(f"[EQUITY WARNING] Using portfolio_state.json values instead")
                                    
                                    # 使用portfolio_state.json中的实际状态
                                    current_cash = portfolio_cash
                                    current_equity = 0.0
                                    # 计算equity_value（需要价格，但这里先设为0，后续会重新计算）
                                    # 注意：这里暂时使用positions_detail，但应该从portfolio_state计算
                                    positions = {}
                                    for symbol, pos_info in portfolio_positions.items():
                                        if isinstance(pos_info, dict):
                                            qty = int(pos_info.get("quantity", 0))
                                            if qty > 0:
                                                positions[symbol] = {
                                                    "quantity": qty,
                                                    "avg_cost": float(pos_info.get("avg_cost", 0)),
                                                    "total_cost": float(pos_info.get("total_cost", 0)),
                                                }
                                    
                                    # 重新计算total_value（但equity_value需要价格，暂时设为0）
                                    # 这里应该从portfolio_state.json的total_value获取，如果有的话
                                    portfolio_total_value = portfolio_state.get("total_value")
                                    if portfolio_total_value:
                                        current_value = float(portfolio_total_value)
                                        current_equity = current_value - current_cash
                                    else:
                                        # 如果没有total_value，使用cash作为保守估计
                                        current_value = current_cash
                                        current_equity = 0.0
                            except Exception as e:
                                print(f"[EQUITY WARNING] Failed to read portfolio_state.json: {e}")
                                # Log error to error logger
                                try:
                                    from src.utils.error_logger import get_error_logger, ErrorLevel
                                    error_logger = get_error_logger(root=str(self.root))
                                    error_logger.warning(
                                        message="Failed to read portfolio_state.json",
                                        component="equity_tracker",
                                        exception=e,
                                        context={"function": "record_daily_equity"}
                                    )
                                except Exception:
                                    pass  # Ignore logging errors
                        
                        # 如果净值下降超过 50%，且当前是 10000.0，且之前有持仓，记录警告并跳过
                        # 或者如果净值突然回到初始值（10000），且之前有持仓，也跳过
                        suspicious_drop = (
                            last_value > 0 and 
                            current_value < last_value * 0.5 and 
                            current_value == 10000.0 and 
                            current_cash == 10000.0 and
                            current_equity == 0.0 and
                            len(last_positions) > 0 and
                            len(positions) == 0
                        )
                        # 额外检查：如果净值突然回到初始值，且之前有持仓
                        reset_to_initial = (
                            last_value > 10000.0 and
                            current_value == 10000.0 and
                            current_cash == 10000.0 and
                            current_equity == 0.0 and
                            len(last_positions) > 0 and
                            len(positions) == 0
                        )
                        if suspicious_drop or reset_to_initial:
                            print(f"[EQUITY WARNING] Suspicious equity drop/reset detected: ${last_value:.2f} -> ${current_value:.2f}")
                            print(f"[EQUITY WARNING] Previous positions: {len(last_positions)}, Current positions: {len(positions)}")
                            print(f"[EQUITY WARNING] Previous cash: ${last_record.get('cash', 0):.2f}, Current cash: ${current_cash:.2f}")
                            print(f"[EQUITY WARNING] Skipping recording to prevent data corruption (likely portfolio state not loaded correctly)")
                            return  # 不记录异常数据
            except Exception as e:
                # 如果检查失败，继续记录（但记录警告）
                print(f"[EQUITY WARNING] Failed to check previous equity: {e}, continuing with record")
        
        # CRITICAL: Ensure timestamp always includes Z suffix (UTC timezone indicator)
        # Use UTC time, ISO 8601 format with millisecond precision (3 decimal places)
        # Format: YYYY-MM-DDTHH:MM:SS.fffZ
        timestamp_str = get_utc_timestamp()
        
        # CRITICAL FIX: 从snapshot或顶层获取total_pnl和total_pnl_pct
        if snapshot:
            total_pnl = float(snapshot.get("total_pnl", portfolio_snapshot.get("total_pnl", 0.0)))
            total_pnl_pct = float(snapshot.get("total_pnl_pct", portfolio_snapshot.get("total_pnl_pct", 0.0)))
        else:
            total_pnl = float(portfolio_snapshot.get("total_pnl", 0.0))
            total_pnl_pct = float(portfolio_snapshot.get("total_pnl_pct", 0.0))
        
        # CRITICAL FIX: Ensure positions record includes current_price and market_value for all positions
        # This ensures data consistency and enables proper chart display
        positions_record = {}
        for symbol, pos_info in positions.items():
            if isinstance(pos_info, dict):
                # Include all position details, ensuring current_price and market_value are present
                positions_record[symbol] = {
                    "quantity": pos_info.get("quantity", 0),
                    "avg_cost": pos_info.get("avg_cost", 0),
                    "total_cost": pos_info.get("total_cost", pos_info.get("avg_cost", 0) * pos_info.get("quantity", 0)),
                    "cost_basis": pos_info.get("cost_basis", pos_info.get("total_cost", 0)),
                }
                
                # Include price information if available
                if "current_price" in pos_info:
                    positions_record[symbol]["current_price"] = pos_info["current_price"]
                if "market_value" in pos_info:
                    positions_record[symbol]["market_value"] = pos_info["market_value"]
                if "unrealized_pnl" in pos_info:
                    positions_record[symbol]["unrealized_pnl"] = pos_info["unrealized_pnl"]
                if "unrealized_pnl_pct" in pos_info:
                    positions_record[symbol]["unrealized_pnl_pct"] = pos_info["unrealized_pnl_pct"]
            else:
                # Fallback: if pos_info is not a dict, preserve as-is
                positions_record[symbol] = pos_info
        
        record = {
            "date": date_str,
            "timestamp": timestamp_str,  # Use UTC timezone, ISO 8601 format, ensure Z suffix
            "cash": current_cash,
            "equity_value": current_equity,
            "total_value": current_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "positions": positions_record,  # Use processed positions with guaranteed price fields
        }
        
        # Log price information status for debugging
        positions_with_price = sum(
            1 for pos in positions_record.values() 
            if isinstance(pos, dict) and "current_price" in pos
        )
        print(f"[EQUITY] Recording equity: total_value=${current_value:.2f}, positions={len(positions_record)}, positions_with_price={positions_with_price}/{len(positions_record)}")
        
        # 验证时间戳格式
        if not timestamp_str.endswith('Z'):
            print(f"[EQUITY WARNING] Timestamp missing Z suffix: {timestamp_str}, fixing...")
            record["timestamp"] = timestamp_str + 'Z'
        
        # 追加到 JSONL 文件
        with self.equity_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        print(f"[EQUITY] Recorded daily equity for {date_str}: ${record['total_value']:.2f}")
    
    def load_equity_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        start_timestamp: Optional[str] = None,
        end_timestamp: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        加载净值历史
        
        参数:
        - start_date: 开始日期 (YYYY-MM-DD)，用于日期过滤
        - end_date: 结束日期 (YYYY-MM-DD)，用于日期过滤
        - start_timestamp: 开始时间戳 (ISO 8601格式)，用于精确时间过滤
        - end_timestamp: 结束时间戳 (ISO 8601格式)，用于精确时间过滤
        - limit: 返回记录数限制
        
        返回:
        - 净值记录列表（按时间戳从旧到新）
        """
        if not self.equity_file.exists():
            return []
        
        records = []
        try:
            with self.equity_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        
                        # CRITICAL: 确保所有记录都有timestamp字段
                        # 如果旧数据缺少timestamp，从date生成一个默认的timestamp
                        if "timestamp" not in record or not record.get("timestamp"):
                            if record.get("date"):
                                # 为旧数据生成一个默认的timestamp（使用当天的中午UTC时间）
                                record["timestamp"] = record["date"] + "T12:00:00.000Z"
                                print(f"[EQUITY] Added missing timestamp for record {record.get('date')}: {record['timestamp']}")
                            else:
                                # If date is also missing, use current time
                                record["timestamp"] = get_utc_timestamp()
                        
                        # Ensure timestamp format is correct (normalize to standard format)
                        if record.get("timestamp"):
                            try:
                                record["timestamp"] = normalize_timestamp(record["timestamp"])
                            except ValueError:
                                # If normalization fails, at least ensure Z suffix
                                record["timestamp"] = ensure_timestamp_has_z_suffix(record["timestamp"])
                        
                        # 日期过滤（如果提供了日期参数）
                        record_date = record.get("date", "")
                        if start_date and record_date < start_date:
                            continue
                        if end_date and record_date > end_date:
                            continue
                        
                        # 时间戳过滤（如果提供了时间戳参数，优先使用时间戳）
                        record_timestamp = record.get("timestamp", "")
                        if start_timestamp:
                            try:
                                record_ts = datetime.fromisoformat(record_timestamp.replace("Z", "+00:00"))
                                start_ts = datetime.fromisoformat(start_timestamp.replace("Z", "+00:00"))
                                if record_ts < start_ts:
                                    continue
                            except:
                                pass
                        if end_timestamp:
                            try:
                                record_ts = datetime.fromisoformat(record_timestamp.replace("Z", "+00:00"))
                                end_ts = datetime.fromisoformat(end_timestamp.replace("Z", "+00:00"))
                                if record_ts > end_ts:
                                    continue
                            except:
                                pass
                        
                        records.append(record)
            
            # 按时间戳排序（优先使用timestamp，如果没有则使用date）
            records.sort(key=lambda x: (
                datetime.fromisoformat(x.get("timestamp", "").replace("Z", "+00:00")) 
                if x.get("timestamp") 
                else datetime.fromisoformat(x.get("date", "1970-01-01") + "T12:00:00+00:00")
            ))
            
            # 限制数量
            if limit:
                records = records[-limit:]
            
            return records
        except Exception as e:
            print(f"[EQUITY ERROR] Failed to load history: {e}")
            return []
    
    def get_latest_equity(self) -> Optional[Dict[str, Any]]:
        """获取最新的净值记录"""
        records = self.load_equity_history(limit=1)
        return records[-1] if records else None

