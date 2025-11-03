import React, { useState } from 'react';
import './SimpleMonitor.css';
import { usePortfolio } from '../hooks/usePortfolio';
import { getApiBase } from '../utils/api';

export default function SimpleMonitor() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const {
    portfolio,
    loading,
    error,
    lastUpdate,
    isRefreshing,
    apiConnected,
    refresh,
  } = usePortfolio(autoRefresh, 30000);

  if (loading) {
    return (
      <div className="simple-monitor">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading...</p>
          <p className="hint">Connecting to backend API...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="simple-monitor">
        <div className="error-box">
          <h2>❌ Connection Error</h2>
          <p>{error}</p>
          <p className="hint">Please ensure the backend API is running: <code>uvicorn src.api.server:app</code></p>
          <button onClick={() => refresh(true)}>Retry</button>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="simple-monitor">
        <div className="no-data">
          <p>No portfolio data available</p>
          <p className="hint">Run a trading cycle to generate data</p>
        </div>
      </div>
    );
  }

  const positions = portfolio.positions ? Object.entries(portfolio.positions) : [];

  return (
    <div className="simple-monitor">
      <header className="monitor-header">
        <h1>📊 AI Trader - Simple Monitor</h1>
        <div className="header-controls">
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto Refresh (30s)
          </label>
          <button onClick={() => refresh(true)} disabled={isRefreshing}>
            {isRefreshing ? 'Refreshing...' : 'Manual Refresh'}
          </button>
          {lastUpdate && (
            <span className="last-update">
              Last Update: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      <div className="stats-grid">
        <div className="stat-card total-value">
          <div className="stat-label">Total Value</div>
          <div className="stat-value">
            ${portfolio.total_value.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </div>
        </div>

        <div className={`stat-card pnl ${portfolio.total_pnl >= 0 ? 'positive' : 'negative'}`}>
          <div className="stat-label">Total P&L</div>
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
          <div className="stat-label">Cash</div>
          <div className="stat-value">
            ${portfolio.cash.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </div>
        </div>

        <div className="stat-card equity">
          <div className="stat-label">Equity Value</div>
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
          <h2>Current Positions ({positions.length})</h2>
          <div className="positions-table">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Quantity</th>
                  <th>Avg Cost</th>
                  <th>Current Price</th>
                  <th>Market Value</th>
                  <th>Unrealized P&L</th>
                  <th>P&L %</th>
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
          <p>No positions held</p>
        </div>
      )}

      <footer className="monitor-footer">
        <div className="footer-info">
          <div className="api-status">
            <span className={`status-indicator ${apiConnected === true ? 'connected' : apiConnected === false ? 'disconnected' : 'unknown'}`}>
              {apiConnected === true ? '●' : apiConnected === false ? '○' : '◐'}
            </span>
            <span>API: {getApiBase()}</span>
          </div>
          <div className="data-time">
            Data Time: {portfolio.timestamp ? new Date(portfolio.timestamp).toLocaleString() : 'N/A'}
          </div>
        </div>
      </footer>
    </div>
  );
}
