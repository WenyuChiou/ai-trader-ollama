# tests/test_prompts.py
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.factory import AgentFactory

# 相容匯入：若專案沒有 ensure_valid_json，就提供內建簡易版
try:
    from src.utils.validators import ensure_valid_json  # type: ignore
except Exception:
    def ensure_valid_json(text: str) -> dict:
        obj = json.loads(text)
        required = [
            "agent",
            "timestamp_utc",
            "inputs_digest",
            "result",
            "decision",
            "signals_used",
            "confidence",
            "to_agent_notes",
        ]
        missing = [k for k in required if k not in obj]
        if missing:
            raise ValueError(f"Missing keys: {sorted(missing)}")
        return obj


def _default_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _ensure_llm(agent) -> None:
    """If agent.llm is None, build a ChatOllama via get_llm()."""
    if getattr(agent, "llm", None) is None:
        try:
            from src.llm.ollama_client import get_llm  # your robust builder
        except Exception as e:
            raise RuntimeError(
                "Agent has no LLM and get_llm() is unavailable. "
                "Ensure src/llm/ollama_client.py exports get_llm(model=..., temperature=...)."
            ) from e
        m = agent.spec.model if getattr(agent, "spec", None) else None
        t = agent.spec.temperature if getattr(agent, "spec", None) else None
        agent.llm = get_llm(model=m, temperature=t)


def main():
    ap = argparse.ArgumentParser(description="Render and test agent prompts")
    ap.add_argument("--agent", required=True, help="agent key in config/agents.yaml")
    ap.add_argument("--config", default="config/agents.yaml")
    ap.add_argument("--symbol", default="NVDA")
    ap.add_argument("--timeframe", default="1D")
    ap.add_argument("--lookback", type=int, default=200)
    ap.add_argument("--now_utc", default=_default_now_iso())

    # 模式：
    ap.add_argument("--dry-run", action="store_true",
                    help="render only; do not call model")
    ap.add_argument("--free", action="store_true",
                    help="free-form reply: bypass JSON validation & BaseAgent.run() contract")

    args = ap.parse_args()

    # 先用不帶 llm 的 Factory 只為了 render
    factory = AgentFactory(config_path=args.config, llm_client=None)
    agent = factory.create(args.agent)

    # 測試變數（共通）
    vars = {
        "agent": args.agent,
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "lookback": args.lookback,
        "now_utc": args.now_utc,
        "risk_budget_pct": 0.01,
        "nav_usd": 100000,
        "recent_drawdown": 0.05,
        "volatility": 0.25,
    }

    # 針對 market/sandbox：提供小型 quotes 預覽
    if args.agent in {"market_agent", "sandbox_agent"}:
        vars.update({
            "raw_quotes": {
                "close_preview": [100.0, 101.2, 99.8, 100.5, 100.9],
                "last_ts_utc": "2025-10-31T20:00:00Z",
            }
        })
        vars.setdefault("raw_quotes_preview", vars["raw_quotes"])

    # 針對 risk_analyst：提供風險與持倉快照
    if args.agent == "risk_analyst":
        vars.update({
            "cash_usd": 100_000,
            "positions_snapshot": {
                "NVDA": {"qty": 0, "avg_px": 0.0},
                "MSFT": {"qty": 10, "avg_px": 405.25},
            },
            "quotes_snapshot": {
                "NVDA": {"last": 100.9, "atr": None, "vol": None},
                "MSFT": {"last": 410.0, "atr": None, "vol": None},
            },
            "max_position_pct": 0.25,
            "stop_loss_bps": 200,
            "take_profit_bps": 400,
            "max_orders_per_day": 5,
        })

    # 渲染
    rendered_system = agent.render(agent.spec.system or "", vars)
    rendered_user = agent.render(agent.spec.user or "", vars)

    print("======== RENDERED SYSTEM PROMPT ========")
    print(rendered_system)
    print("========================================\n")
    print("========= RENDERED USER PROMPT =========")
    print(rendered_user)
    print("========================================\n")

    # 只渲染
    if args.dry_run:
        print("[DRY RUN] Skipping model invocation.")
        return

    # 自由輸出模式：直接以訊息列表呼叫模型（不驗 JSON）
    if args.free:
        fac_llm = AgentFactory(config_path=args.config, llm_client=None)
        agent_free = fac_llm.create(args.agent)
        _ensure_llm(agent_free)
        msgs = [SystemMessage(content=rendered_system),
                HumanMessage(content=rendered_user)]
        print("============== MODEL OUTPUT =============")
        try:
            ai = agent_free.llm.invoke(msgs)
            print(ai.content)
        except Exception as e:
            print(f"[error] free-form call failed: {e}")
        print("=========================================")
        return

    # 預設：照原行為呼叫並嘗試驗 JSON
    fac_llm = AgentFactory(config_path=args.config, llm_client=None)
    agent_llm = fac_llm.create(args.agent)
    _ensure_llm(agent_llm)
    msgs = [SystemMessage(content=rendered_system),
            HumanMessage(content=rendered_user)]
    output_text = agent_llm.llm.invoke(msgs).content

    print("============== MODEL OUTPUT =============")
    print(output_text)
    print("=========================================\n")

    # 嘗試驗證 JSON（若不是 JSON，這裡會印警告但不結束流程）
    try:
        ensure_valid_json(output_text)
    except Exception as e:
        print(f"[warn] JSON validation failed: {e}")


if __name__ == "__main__":
    main()
