from __future__ import annotations

"""Utility script to settle or expire pending orders after the trading day."""

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Dict, Any

from src.data.order_manager import OrderManager
from src.data.portfolio import Portfolio, Position
from src.utils.trading_days import is_trading_day

DEFAULT_LOG_ROOT = Path("data/logs")
DEFAULT_STATE_FILE = DEFAULT_LOG_ROOT / "portfolio_state.json"


def load_portfolio(state_file: Path) -> Portfolio:
    if not state_file.exists():
        raise FileNotFoundError(f"Portfolio state file not found: {state_file}")

    with state_file.open("r", encoding="utf-8") as f:
        state = json.load(f)

    portfolio = Portfolio(
        cash=float(state.get("cash", 10000.0)),
        initial_value=float(state.get("initial_value", 10000.0)),
    )

    positions = state.get("positions", {}) or {}
    for symbol, pos_info in positions.items():
        if isinstance(pos_info, dict):
            qty = int(pos_info.get("quantity", 0))
            avg_cost = float(pos_info.get("avg_cost", 0.0))
            total_cost = float(pos_info.get("total_cost", avg_cost * qty))
            if qty > 0:
                portfolio._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=qty,
                    avg_cost=avg_cost,
                    total_cost=total_cost,
                )

    return portfolio


def save_portfolio(portfolio: Portfolio, state_file: Path) -> None:
    positions: Dict[str, Dict[str, float]] = {}
    for symbol, pos in portfolio._positions.items():
        positions[symbol] = {
            "quantity": pos.quantity,
            "avg_cost": pos.avg_cost,
            "total_cost": pos.total_cost,
        }

    state = {
        "cash": portfolio.cash,
        "initial_value": portfolio.initial_value,
        "positions": positions,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def settle_order(
    order_manager: OrderManager,
    portfolio: Portfolio,
    order: Dict[str, Any],
    target_date: str,
) -> tuple[bool, bool]:
    """Attempt to settle a single order. Returns (filled, rejected)."""
    symbol = order.get("symbol")
    action = (order.get("action") or "").upper()
    quantity = int(order.get("quantity", 0))
    if not symbol or quantity <= 0:
        fill_result = {
            "filled": False,
            "fill_price": None,
            "fill_reason": "Invalid order payload",
            "daily_high": None,
            "daily_low": None,
            "current_price": None,
        }
        order_manager.mark_order_filled(order, fill_result)
        return False, True

    try:
        fill_result = order_manager.check_order_fill(order, target_date, use_realtime=False)
    except Exception as exc:  # pragma: no cover - guard against YF issues
        fill_result = {
            "filled": False,
            "fill_price": None,
            "fill_reason": f"Fill check error: {exc}",
            "daily_high": None,
            "daily_low": None,
            "current_price": None,
        }

    if fill_result.get("filled"):
        fill_price = float(fill_result.get("fill_price", 0.0) or 0.0)
        if action == "BUY":
            portfolio.buy(symbol, quantity, fill_price)
            order_manager.mark_order_filled(order, fill_result)
            return True, False
        if action == "SELL":
            realized_pnl = portfolio.sell(symbol, quantity, fill_price)
            order_manager.mark_order_filled(order, fill_result, realized_pnl=realized_pnl)
            return True, False

    # Not filled: expire order
    expire_result = {
        "filled": False,
        "fill_price": None,
        "fill_reason": "Order expired without fill",
        "daily_high": fill_result.get("daily_high"),
        "daily_low": fill_result.get("daily_low"),
        "current_price": fill_result.get("current_price"),
    }
    order_manager.mark_order_filled(order, expire_result)
    return False, True


def purge_stale_orders(order_manager: OrderManager, target_date: str) -> int:
    """Remove pending orders whose order_date < target_date."""
    all_pending = order_manager.load_pending_orders()
    stale_orders = [o for o in all_pending if o.get("order_date", "") < target_date]
    rejected = 0
    for order in stale_orders:
        expire_result = {
            "filled": False,
            "fill_price": None,
            "fill_reason": "Order expired before settlement run",
            "daily_high": None,
            "daily_low": None,
            "current_price": None,
        }
        order_manager.mark_order_filled(order, expire_result)
        rejected += 1
    return rejected


def check_and_execute_pending_orders(
    check_date: Optional[str] = None,
    portfolio_state_file: Path | str = DEFAULT_STATE_FILE,
    logs_root: Path | str = DEFAULT_LOG_ROOT,
    portfolio: Optional[Portfolio] = None,
) -> Dict[str, Any]:
    """Settle pending orders for a given trade date."""
    logs_root = Path(logs_root)
    order_manager = OrderManager(root=str(logs_root))
    portfolio_state_file = Path(portfolio_state_file)

    if check_date is None:
        check_date = date.today().isoformat()

    if not is_trading_day(datetime.strptime(check_date, "%Y-%m-%d").date()):
        return {
            "ok": False,
            "error": f"{check_date} is not a trading day",
            "filled_count": 0,
            "rejected_count": 0,
        }

    if portfolio is None:
        portfolio = load_portfolio(portfolio_state_file)

    rejected_count = purge_stale_orders(order_manager, check_date)

    pending_orders = order_manager.load_pending_orders(order_date=check_date)
    filled_count = 0

    for order in pending_orders:
        filled, rejected = settle_order(order_manager, portfolio, order, check_date)
        if filled:
            filled_count += 1
        if rejected:
            rejected_count += 1

    save_portfolio(portfolio, portfolio_state_file)

    remaining = order_manager.load_pending_orders(order_date=check_date)

    return {
        "ok": True,
        "date": check_date,
        "filled_count": filled_count,
        "rejected_count": rejected_count,
        "pending_remaining": len(remaining),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Settle pending limit orders")
    parser.add_argument("--date", dest="check_date", help="Trading date (YYYY-MM-DD)")
    parser.add_argument(
        "--state-file",
        dest="state_file",
        default=str(DEFAULT_STATE_FILE),
        help="Portfolio state JSON path",
    )
    parser.add_argument(
        "--logs-root",
        dest="logs_root",
        default=str(DEFAULT_LOG_ROOT),
        help="Logs directory containing pending/filled files",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = check_and_execute_pending_orders(
        check_date=args.check_date,
        portfolio_state_file=Path(args.state_file),
        logs_root=Path(args.logs_root),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
