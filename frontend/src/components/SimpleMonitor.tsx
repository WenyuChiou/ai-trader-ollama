import React, { useEffect, useState } from 'react';
import './SimpleMonitor.css';

interface PortfolioSnapshot {
  timestamp: string;
  total_value: number;
  cash: number;
  equity_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  positions: Record<string, {
    quantity: number;
    avg_cost: number;
    current_price: number;
    market_value: number;
  }>;
  positions_pnl: Record<string, {
    unrealized_pnl: number;
    unrealized_pnl_pct: number;
  }>;
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export default function SimpleMonitor() {
  const [portfolio, setPortfolio] = useState<PortfolioSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchPortfolio = async (showLoading: boolean = false) => {
    if (showLoading) {
      setIsRefreshing(true);
    }
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时
      
      const response = await fetch(`${API_BASE}/api/portfolio/real-time`, {
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) throw new Error('Failed to fetch portfolio');
      const data = await response.json();
      if (!data.ok || data.error) throw new Error(data.error || 'Failed to load');
      
      setPortfolio(data as PortfolioSnapshot);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setError('请求超时，请检查网络连接');
      } else {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
      console.error('Error fetching portfolio:', err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPortfolio(true);
    
    // Auto-refresh every 30 seconds if enabled
    const interval = setInterval(() => {
      if (autoRefresh && !isRefreshing) {
        fetchPortfolio(false);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  if (loading) {
    return (
      <div className="simple-monitor">
        <div className="loading">
          <div className="spinner"></div>
          <p>加载中...</p>
          <p className="hint">正在连接后端 API...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="simple-monitor">
        <div className="error-box">
          <h2>❌ 连接错误</h2>
          <p>{error}</p>
          <p className="hint">请确认后端 API 正在运行: <code>uvicorn src.api.server:app</code></p>
          <button onClick={fetchPortfolio}>重试</button>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="simple-monitor">
        <div className="no-data">
          <p>暂无投资组合数据</p>
          <p className="hint">运行一次交易循环后会有数据</p>
        </div>
      </div>
    );
  }

  const positions = portfolio.positions ? Object.entries(portfolio.positions) : [];

  return (
    <div className="simple-monitor">
      <header className="monitor-header">
        <h1>📊 AI Trader - 简易监控</h1>
        <div className="header-controls">
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            自动刷新 (30秒)
          </label>
          <button onClick={() => fetchPortfolio(true)} disabled={isRefreshing}>
            {isRefreshing ? '刷新中...' : '手动刷新'}
          </button>
          {lastUpdate && (
            <span className="last-update">
              最后更新: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      <div className="stats-grid">
        <div className="stat-card total-value">
          <div className="stat-label">总资产</div>
          <div className="stat-value">
            ${portfolio.total_value.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </div>
        </div>

        <div className={`stat-card pnl ${portfolio.total_pnl >= 0 ? 'positive' : 'negative'}`}>
          <div className="stat-label">总盈亏</div>
          <div className="stat-value">
            ${portfolio.total_pnl.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </div>
          <div className="stat-percent">
            {portfolio.total_pnl >= 0 ? '+' : ''}
            {portfolio.total_pnl_pct.toFixed(2)}%
          </div>
        </div>

        <div className="stat-card cash">
          <div className="stat-label">现金</div>
          <div className="stat-value">
            ${portfolio.cash.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </div>
        </div>

        <div className="stat-card equity">
          <div className="stat-label">持仓市值</div>
          <div className="stat-value">
            ${portfolio.equity_value.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </div>
        </div>
      </div>

      {positions.length > 0 && (
        <div className="positions-section">
          <h2>当前持仓 ({positions.length})</h2>
          <div className="positions-table">
            <table>
              <thead>
                <tr>
                  <th>股票</th>
                  <th>数量</th>
                  <th>成本价</th>
                  <th>当前价</th>
                  <th>市值</th>
                  <th>盈亏</th>
                  <th>盈亏%</th>
                </tr>
              </thead>
              <tbody>
                {positions.map(([symbol, pos]) => {
                  const pnl = portfolio.positions_pnl[symbol] || { unrealized_pnl: 0, unrealized_pnl_pct: 0 };
                  return (
                    <tr key={symbol}>
                      <td className="symbol">{symbol}</td>
                      <td>{pos.quantity}</td>
                      <td>${pos.avg_cost.toFixed(2)}</td>
                      <td>${pos.current_price.toFixed(2)}</td>
                      <td>${pos.market_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                      <td className={pnl.unrealized_pnl >= 0 ? 'positive' : 'negative'}>
                        ${pnl.unrealized_pnl.toFixed(2)}
                      </td>
                      <td className={pnl.unrealized_pnl_pct >= 0 ? 'positive' : 'negative'}>
                        {pnl.unrealized_pnl_pct >= 0 ? '+' : ''}{pnl.unrealized_pnl_pct.toFixed(2)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {positions.length === 0 && (
        <div className="no-positions">
          <p>当前无持仓</p>
        </div>
      )}

      <footer className="monitor-footer">
        <p>API: {API_BASE}</p>
        <p>数据时间: {portfolio.timestamp ? new Date(portfolio.timestamp).toLocaleString('zh-CN') : 'N/A'}</p>
      </footer>
    </div>
  );
}

