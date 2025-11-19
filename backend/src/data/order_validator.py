"""
訂單數據驗證和標準化模組

確保所有訂單數據符合標準格式，便於 Performance Analysis 使用
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


def validate_order(order: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    驗證訂單數據是否符合標準格式
    
    參數:
        order: 訂單字典
    
    返回:
        (is_valid, errors): (是否有效, 錯誤列表)
    """
    errors = []
    
    # 必填字段檢查
    required_fields = ["order_id", "symbol", "action", "quantity", "status"]
    for field in required_fields:
        if field not in order:
            errors.append(f"Missing required field: {field}")
    
    # 驗證 action
    if "action" in order and order["action"] not in ["BUY", "SELL"]:
        errors.append(f"Invalid action: {order['action']} (must be BUY or SELL)")
    
    # 驗證 status
    if "status" in order and order["status"] not in ["PENDING", "FILLED", "REJECTED"]:
        errors.append(f"Invalid status: {order['status']} (must be PENDING, FILLED, or REJECTED)")
    
    # FILLED 訂單必填字段
    if order.get("status") == "FILLED":
        filled_required = ["fill_price", "filled_at", "fill_result"]
        for field in filled_required:
            if field not in order:
                errors.append(f"FILLED order missing required field: {field}")
    
    # SELL 訂單必須有實現損益字段
    if order.get("action") == "SELL" and order.get("status") == "FILLED":
        pnl_fields = ["realized_pnl", "realized_pnl_pct", "cost_basis", "proceeds"]
        missing_fields = [f for f in pnl_fields if f not in order]
        if missing_fields:
            errors.append(f"SELL FILLED order missing realized P&L fields: {', '.join(missing_fields)}")
    
    # 驗證時間戳格式
    for time_field in ["placed_at", "filled_at"]:
        if time_field in order:
            timestamp = order[time_field]
            if not isinstance(timestamp, str):
                errors.append(f"{time_field} must be a string (ISO 8601 format)")
            elif not (timestamp.endswith('Z') or '+' in timestamp or '-' in timestamp[10:]):
                errors.append(f"{time_field} must be in ISO 8601 UTC format (e.g., 2025-01-19T10:30:00.123Z)")
    
    # 驗證數值類型
    numeric_fields = ["quantity", "limit_price", "fill_price"]
    for field in numeric_fields:
        if field in order:
            value = order[field]
            if not isinstance(value, (int, float)):
                errors.append(f"{field} must be a number, got {type(value).__name__}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def normalize_order(order: Dict[str, Any]) -> Dict[str, Any]:
    """
    標準化訂單數據，確保所有字段符合標準格式
    
    參數:
        order: 訂單字典
    
    返回:
        標準化後的訂單字典
    """
    normalized = order.copy()
    
    # 確保 status 存在
    if "status" not in normalized:
        if "fill_price" in normalized or "filled_at" in normalized:
            normalized["status"] = "FILLED"
        else:
            normalized["status"] = "PENDING"
    
    # 標準化時間戳格式
    for time_field in ["placed_at", "filled_at"]:
        if time_field in normalized:
            timestamp = normalized[time_field]
            if isinstance(timestamp, str):
                # 如果已經是 ISO 8601 格式，確保有 Z 後綴
                if not timestamp.endswith('Z') and '+' not in timestamp and '-' not in timestamp[10:]:
                    # 嘗試解析並轉換為 UTC
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        normalized[time_field] = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                    except:
                        pass
    
    # SELL FILLED 訂單：確保實現損益字段存在
    if normalized.get("action") == "SELL" and normalized.get("status") == "FILLED":
        # 如果缺少實現損益字段，嘗試從 fill_result 中提取
        if "realized_pnl" not in normalized:
            fill_result = normalized.get("fill_result", {})
            if isinstance(fill_result, dict):
                normalized["realized_pnl"] = fill_result.get("realized_pnl", 0.0)
                normalized["realized_pnl_pct"] = fill_result.get("realized_pnl_pct", 0.0)
                normalized["cost_basis"] = fill_result.get("cost_basis", 0.0)
                normalized["proceeds"] = fill_result.get("proceeds", 0.0)
        
        # 如果仍然缺少，嘗試計算（如果可能）
        if "realized_pnl" not in normalized or normalized.get("realized_pnl") is None:
            fill_price = normalized.get("fill_price", 0.0)
            quantity = normalized.get("quantity", 0)
            proceeds = fill_price * quantity
            
            # 嘗試從 fill_result 獲取 cost_basis
            fill_result = normalized.get("fill_result", {})
            cost_basis = fill_result.get("cost_basis", 0.0)
            
            # 如果 cost_basis 為 0，嘗試估算（使用 limit_price 作為近似值）
            if cost_basis == 0.0:
                limit_price = normalized.get("limit_price", fill_price)
                cost_basis = limit_price * quantity
            
            realized_pnl = proceeds - cost_basis
            realized_pnl_pct = (realized_pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0
            
            normalized["realized_pnl"] = realized_pnl
            normalized["realized_pnl_pct"] = realized_pnl_pct
            normalized["cost_basis"] = cost_basis
            normalized["proceeds"] = proceeds
            
            # 同時更新 fill_result
            if "fill_result" not in normalized:
                normalized["fill_result"] = {}
            normalized["fill_result"]["realized_pnl"] = realized_pnl
            normalized["fill_result"]["realized_pnl_pct"] = realized_pnl_pct
            normalized["fill_result"]["cost_basis"] = cost_basis
            normalized["fill_result"]["proceeds"] = proceeds
    
    # 確保數值類型正確
    numeric_fields = ["quantity", "limit_price", "fill_price", "realized_pnl", 
                     "realized_pnl_pct", "cost_basis", "proceeds"]
    for field in numeric_fields:
        if field in normalized:
            value = normalized[field]
            if isinstance(value, str):
                try:
                    normalized[field] = float(value)
                except:
                    pass
            elif value is None:
                normalized[field] = 0.0
    
    # 確保 fill_result 存在（對於 FILLED 訂單）
    if normalized.get("status") == "FILLED" and "fill_result" not in normalized:
        normalized["fill_result"] = {
            "filled": True,
            "fill_price": normalized.get("fill_price", 0.0),
            "fill_reason": normalized.get("fill_reason", "Order filled"),
            "daily_high": normalized.get("daily_high", 0.0),
            "daily_low": normalized.get("daily_low", 0.0),
        }
    
    return normalized


def validate_orders_for_performance(orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    驗證訂單列表是否適合 Performance Analysis
    
    參數:
        orders: 訂單列表
    
    返回:
        {
            "valid": bool,
            "total_orders": int,
            "sell_orders": int,
            "sell_orders_with_pnl": int,
            "missing_pnl_count": int,
            "errors": List[str],
            "normalized_orders": List[Dict[str, Any]]
        }
    """
    result = {
        "valid": True,
        "total_orders": len(orders),
        "sell_orders": 0,
        "sell_orders_with_pnl": 0,
        "missing_pnl_count": 0,
        "errors": [],
        "normalized_orders": []
    }
    
    normalized_orders = []
    for order in orders:
        # 標準化訂單
        normalized = normalize_order(order)
        normalized_orders.append(normalized)
        
        # 驗證訂單
        is_valid, errors = validate_order(normalized)
        if not is_valid:
            result["valid"] = False
            result["errors"].extend([f"Order {normalized.get('order_id', 'unknown')}: {e}" for e in errors])
        
        # 統計 SELL 訂單
        if normalized.get("action") == "SELL":
            result["sell_orders"] += 1
            if normalized.get("realized_pnl") is not None:
                result["sell_orders_with_pnl"] += 1
            else:
                result["missing_pnl_count"] += 1
    
    result["normalized_orders"] = normalized_orders
    
    return result

