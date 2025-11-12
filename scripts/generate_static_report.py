#!/usr/bin/env python3
"""
Generate static HTML report for GitHub Pages
This script generates a static HTML file that can be deployed to GitHub Pages
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from backend.src.data.memory_manager import MemoryManager
    from backend.src.data.equity_tracker import EquityTracker
    from backend.src.data.portfolio import Portfolio
except ImportError:
    # Fallback if running from different directory
    sys.path.insert(0, str(ROOT / 'backend'))
    from src.data.memory_manager import MemoryManager
    from src.data.equity_tracker import EquityTracker
    from src.data.portfolio import Portfolio


def load_recent_trades(limit: int = 50) -> List[Dict[str, Any]]:
    """Load recent trades from logs"""
    trades = []
    # Check both possible locations
    logs_dir = None
    for possible_dir in [Path("data/logs"), Path("backend/data/logs")]:
        if (ROOT / possible_dir).exists():
            logs_dir = ROOT / possible_dir
            break
    if logs_dir is None:
        logs_dir = Path("data/logs")  # Default fallback
    
    # Try multiple log files
    for log_file in [logs_dir / "trades.jsonl", logs_dir / "filled_orders.jsonl"]:
        if log_file.exists():
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        trade = json.loads(line.strip())
                        trades.append(trade)
                    except:
                        continue
    
    # Sort by timestamp (newest first)
    trades.sort(key=lambda x: x.get("timestamp", x.get("filled_at", "")), reverse=True)
    return trades[:limit]


def load_recent_conversations(limit: int = 30) -> List[Dict[str, Any]]:
    """Load recent conversations"""
    conversations = []
    # Check both possible locations
    logs_dir = None
    for possible_dir in [Path("data/logs"), Path("backend/data/logs")]:
        if (ROOT / possible_dir).exists():
            logs_dir = ROOT / possible_dir
            break
    if logs_dir is None:
        logs_dir = Path("data/logs")  # Default fallback
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    if convo_file.exists():
        with convo_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-limit * 2:]:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                    if entry.get("type") != "demo":  # Exclude demo entries
                        conversations.append(entry)
                except:
                    continue
    
    return conversations[-limit:]


def load_tool_results(limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
    """Load tool results grouped by agent and tool name"""
    tool_results = {}  # {agent: {tool_name: [results]}}
    # Check both possible locations
    logs_dir = None
    for possible_dir in [Path("data/logs"), Path("backend/data/logs")]:
        if (ROOT / possible_dir).exists():
            logs_dir = ROOT / possible_dir
            break
    if logs_dir is None:
        logs_dir = Path("data/logs")  # Default fallback
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    if convo_file.exists():
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                    if entry.get("type") == "tool":
                        agent = entry.get("agent", "Unknown")
                        tool_name = entry.get("tool_name", "unknown_tool")
                        content = entry.get("content", "")
                        timestamp = entry.get("timestamp", entry.get("date", ""))
                        
                        # Extract result from content (format: "Tool used: tool_name: {result}")
                        result_text = content
                        if "Tool used:" in content:
                            parts = content.split(":", 2)
                            if len(parts) >= 3:
                                result_text = parts[2].strip()
                        
                        tool_result = {
                            "tool_name": tool_name,
                            "result": result_text,
                            "timestamp": timestamp,
                            "date": entry.get("date", ""),
                            "full_entry": entry
                        }
                        
                        if agent not in tool_results:
                            tool_results[agent] = {}
                        if tool_name not in tool_results[agent]:
                            tool_results[agent][tool_name] = []
                        
                        tool_results[agent][tool_name].append(tool_result)
                except Exception as e:
                    continue
    
    # Limit results per tool
    for agent in tool_results:
        for tool_name in tool_results[agent]:
            tool_results[agent][tool_name] = tool_results[agent][tool_name][-limit:]
    
    return tool_results


def load_equity_history(limit: int = 60) -> List[Dict[str, Any]]:
    """Load equity history"""
    try:
        # Check both possible locations
        logs_dir = None
        for possible_dir in [Path("data/logs"), Path("backend/data/logs")]:
            if (ROOT / possible_dir).exists():
                logs_dir = ROOT / possible_dir
                break
        if logs_dir is None:
            logs_dir = Path("data/logs")  # Default fallback
        equity_tracker = EquityTracker(root=str(logs_dir))
        records = equity_tracker.load_equity_history(limit=limit)
        return records
    except Exception as e:
        print(f"Warning: Failed to load equity history: {e}")
        return []


def generate_html_report(output_path: Path) -> None:
    """Generate static HTML report"""
    
    # Load data
    print("Loading data...")
    trades = load_recent_trades(limit=50)
    conversations = load_recent_conversations(limit=30)
    equity_history = load_equity_history(limit=60)
    tool_results = load_tool_results(limit=50)  # Load tool results
    
    # Calculate summary stats
    total_trades = len(trades)
    recent_trades = [t for t in trades if t.get("status") == "FILLED"][:10]
    
    # Get latest equity
    latest_equity = equity_history[-1] if equity_history else None
    initial_value = equity_history[0].get("total_value", 10000) if equity_history else 10000
    current_value = latest_equity.get("total_value", initial_value) if latest_equity else initial_value
    total_return = current_value - initial_value
    total_return_pct = (total_return / initial_value * 100) if initial_value > 0 else 0
    
    # Count agent participation
    agents_used = set()
    for conv in conversations:
        agent = conv.get("agent", "")
        if agent:
            agents_used.add(agent)
    
    # Count tool usage
    total_tool_calls = sum(
        len(tool_list) 
        for agent_tools in tool_results.values() 
        for tool_list in agent_tools.values()
    )
    unique_tools = set()
    for agent_tools in tool_results.values():
        unique_tools.update(agent_tools.keys())
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Trader Daily Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            color: #e5e7eb;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #22d3ee;
            margin-bottom: 10px;
            font-size: 32px;
        }}
        .subtitle {{
            color: #94a3b8;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(20, 20, 25, 0.8);
            border: 1px solid rgba(34, 211, 238, 0.3);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: 700;
            color: #22d3ee;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .section {{
            background: rgba(20, 20, 25, 0.8);
            border: 1px solid rgba(34, 211, 238, 0.3);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .section h2 {{
            color: #22d3ee;
            font-size: 20px;
            margin-bottom: 16px;
            border-bottom: 2px solid rgba(34, 211, 238, 0.3);
            padding-bottom: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{
            background: rgba(34, 211, 238, 0.1);
            color: #22d3ee;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid rgba(34, 211, 238, 0.3);
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        tr:hover {{
            background: rgba(34, 211, 238, 0.05);
        }}
        .positive {{
            color: #10b981;
        }}
        .negative {{
            color: #ef4444;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-filled {{
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
        }}
        .badge-pending {{
            background: rgba(251, 191, 36, 0.2);
            color: #fbbf24;
        }}
        .footer {{
            text-align: center;
            color: #94a3b8;
            font-size: 12px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .update-time {{
            color: #22d3ee;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 AI-Trader Daily Report</h1>
        <p class="subtitle">Last updated: <span class="update-time">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</span></p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${current_value:,.2f}</div>
                <div class="stat-label">Current Value</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {'positive' if total_return >= 0 else 'negative'}">
                    {'+' if total_return >= 0 else ''}${total_return:,.2f}
                </div>
                <div class="stat-label">Total Return</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {'positive' if total_return_pct >= 0 else 'negative'}">
                    {'+' if total_return_pct >= 0 else ''}{total_return_pct:.2f}%
                </div>
                <div class="stat-label">Return %</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_trades}</div>
                <div class="stat-label">Total Trades</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(agents_used)}</div>
                <div class="stat-label">Agents Active</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(conversations)}</div>
                <div class="stat-label">Conversations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_tool_calls}</div>
                <div class="stat-label">Tool Calls</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(unique_tools)}</div>
                <div class="stat-label">Unique Tools</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Recent Trades</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Symbol</th>
                        <th>Action</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    if recent_trades:
        for trade in recent_trades[:20]:
            symbol = trade.get("symbol", "N/A")
            action = trade.get("action", trade.get("side", "N/A"))
            quantity = trade.get("quantity", 0)
            price = trade.get("price", trade.get("fill_price", 0))
            status = trade.get("status", "UNKNOWN")
            timestamp = trade.get("timestamp", trade.get("filled_at", ""))
            date_str = timestamp.split("T")[0] if "T" in timestamp else timestamp[:10] if len(timestamp) >= 10 else "N/A"
            
            status_class = "badge-filled" if status == "FILLED" else "badge-pending"
            action_class = "positive" if action == "BUY" else "negative"
            
            html += f"""
                    <tr>
                        <td>{date_str}</td>
                        <td><strong>{symbol}</strong></td>
                        <td class="{action_class}">{action}</td>
                        <td>{quantity}</td>
                        <td>${price:.2f}</td>
                        <td><span class="badge {status_class}">{status}</span></td>
                    </tr>
"""
    else:
        html += """
                    <tr>
                        <td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">
                            No trades yet. Run a trading cycle to generate trades.
                        </td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>🤖 Active Agents</h2>
            <div style="display: flex; flex-wrap: wrap; gap: 12px;">
"""
    
    agent_icons = {
        "MarketAnalyst": "🌐",
        "TechnicalAnalyst": "📈",
        "FundamentalAnalyst": "💼",
        "SentimentAnalyst": "😊",
        "RiskAnalyst": "⚠️",
        "TraderAgent": "🤖",
    }
    
    for agent in sorted(agents_used):
        icon = agent_icons.get(agent, "🤖")
        html += f"""
                <div style="padding: 12px; background: rgba(34, 211, 238, 0.1); border-radius: 8px; border: 1px solid rgba(34, 211, 238, 0.3);">
                    <span style="font-size: 20px;">{icon}</span>
                    <span style="margin-left: 8px; font-weight: 600;">{agent}</span>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>🛠️ Tool Results by Agent</h2>
"""
    
    # Add tool results section
    if tool_results:
        agent_icons = {
            "MarketAnalyst": "🌐",
            "TechnicalAnalyst": "📈",
            "FundamentalAnalyst": "💼",
            "SentimentAnalyst": "😊",
            "RiskAnalyst": "⚠️",
            "TraderAgent": "🤖",
            "DiscussionCoordinator": "💬",
        }
        
        for agent in sorted(tool_results.keys()):
            agent_tools = tool_results[agent]
            total_tools_for_agent = sum(len(tool_list) for tool_list in agent_tools.values())
            icon = agent_icons.get(agent, "🤖")
            
            html += f"""
            <div class="tool-section">
                <div class="agent-header">
                    <span class="agent-icon">{icon}</span>
                    <span class="agent-name">{agent}</span>
                    <span class="tool-count">({total_tools_for_agent} tool calls)</span>
                </div>
"""
            
            # Group by tool name
            for tool_name in sorted(agent_tools.keys()):
                tool_calls = agent_tools[tool_name]
                html += f"""
                <div class="tool-group">
                    <h3>🔧 {tool_name} <span style="color: #94a3b8; font-size: 14px; font-weight: normal;">({len(tool_calls)} calls)</span></h3>
"""
                
                # Show latest 15 results per tool (most recent first)
                for tool_call in tool_calls[-15:][::-1]:
                    result_text = tool_call.get("result", "")
                    date_str = tool_call.get("date", tool_call.get("timestamp", ""))[:10] if tool_call.get("date") or tool_call.get("timestamp") else "N/A"
                    
                    # Truncate very long results
                    # News tools get more space (5000 chars), others get 3000 chars
                    is_news_tool = tool_name in ["news_scan", "plan_and_scan_news", "fetch_jin10_news", "business_rss"]
                    max_length = 5000 if is_news_tool else 3000
                    if len(result_text) > max_length:
                        result_text = result_text[:max_length] + f"\n... (truncated, showing first {max_length} characters)"
                    
                    html += f"""
                    <div class="tool-item">
                        <div class="tool-item-header">
                            <span class="tool-name">{tool_name}</span>
                            <span class="tool-date">{date_str}</span>
                        </div>
                        <div class="tool-result">{result_text}</div>
                    </div>
"""
                
                html += """
                </div>
"""
            
            html += """
            </div>
"""
    else:
        html += """
            <div style="color: #94a3b8; text-align: center; padding: 40px;">
                <p>No tool results yet. Run a trading cycle to generate tool calls.</p>
            </div>
"""
    
    html += """
        </div>
        
        <div class="section">
            <h2>📊 Equity History (Last 30 Days)</h2>
            <div style="color: #94a3b8; font-size: 14px;">
                <p>Total records: {equity_count}</p>
                <p style="margin-top: 8px;">Latest value: <span style="color: #22d3ee; font-weight: 600;">${current_value:,.2f}</span></p>
            </div>
        </div>
        
        <div class="footer">
            <p>This report is generated automatically from trading data.</p>
            <p>For real-time data, visit the <a href="monitor.html" style="color: #22d3ee;">Live Dashboard</a></p>
        </div>
    </div>
</body>
</html>
""".format(
        current_value=current_value,
        total_return=total_return,
        total_return_pct=total_return_pct,
        total_trades=total_trades,
        agents_used=agents_used,
        conversations=conversations,
        equity_count=len(equity_history)
    )
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Report generated: {output_path}")
    print(f"   - Trades: {total_trades}")
    print(f"   - Conversations: {len(conversations)}")
    print(f"   - Equity records: {len(equity_history)}")
    print(f"   - Tool calls: {total_tool_calls}")
    print(f"   - Unique tools: {len(unique_tools)}")
    print(f"   - Agents with tools: {len(tool_results)}")
    print(f"   - Current value: ${current_value:,.2f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate static HTML report for GitHub Pages")
    parser.add_argument("--output", type=str, default="frontend/report.html", 
                       help="Output file path (default: frontend/report.html)")
    
    args = parser.parse_args()
    output_path = Path(args.output)
    
    try:
        generate_html_report(output_path)
        print(f"\n✅ Success! Report saved to: {output_path}")
        print(f"   You can now commit and push this file to GitHub Pages")
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

