import React, { useState, useEffect } from 'react';
import { usePortfolio } from '../hooks/usePortfolio';
import { fetchEquityHistory, getApiBase } from '../utils/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import './PortfolioMonitor.css';

interface EquityData {
  date: string;
  value: number;
  pnl: number;
}

export default function PortfolioMonitor() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [equityHistory, setEquityHistory] = useState<EquityData[]>([]);
  const [chartScale, setChartScale] = useState<'linear' | 'log'>('linear');
  const {
    portfolio,
    loading,
    error,
    lastUpdate,
    isRefreshing,
    apiConnected,
    refresh,
  } = usePortfolio(autoRefresh, 30000);

  // Load equity history for chart
  useEffect(() => {
    const loadEquityHistory = async () => {
      try {
        const data = await fetchEquityHistory(60);
        setEquityHistory(data);
      } catch (err) {
        console.error('Failed to load equity history:', err);
      }
    };
    
    loadEquityHistory();
    if (autoRefresh) {
      const interval = setInterval(loadEquityHistory, 300000); // Every 5 minutes
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  if (loading) {
    return (
      <div className="portfolio-monitor">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading portfolio data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="portfolio-monitor">
        <div className="error-container">
          <h2>❌ Connection Error</h2>
          <p>{error}</p>
          <button onClick={() => refresh(true)} className="retry-btn">Retry Connection</button>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="portfolio-monitor">
        <div className="no-data-container">
          <p>No portfolio data available</p>
          <p className="hint">Run a trading cycle to generate data</p>
        </div>
      </div>
    );
  }

  const positions = portfolio.positions ? Object.entries(portfolio.positions) : [];
  const hasPositions = positions.length > 0;

  // Calculate statistics
  const totalPositionsValue = positions.reduce((sum, [_, pos]) => sum + (pos.market_value || 0), 0);
  const totalUnrealizedPnL = positions.reduce((sum, [symbol, _]) => {
    const pnl = portfolio.positions_pnl[symbol]?.unrealized_pnl || 0;
    return sum + pnl;
  }, 0);

  // Format chart data
  const chartData = equityHistory.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: item.value,
    pnl: item.pnl,
  }));

  return (
    <div className="portfolio-monitor">
      {/* Header */}
      <header className="monitor-header">
        <div className="header-title">
          <h1>📊 AI-Trader Portfolio Monitor</h1>
          <div className="connection-status">
            <span className={`status-dot ${apiConnected ? 'connected' : 'disconnected'}`}></span>
            <span>{apiConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
        <div className="header-controls">
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            <span>Auto Refresh (30s)</span>
          </label>
          <button 
            onClick={() => refresh(true)} 
            disabled={isRefreshing}
            className="refresh-btn"
          >
            {isRefreshing ? '🔄 Refreshing...' : '🔄 Refresh'}
          </button>
          {lastUpdate && (
            <span className="last-update">
              Last: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      {/* Summary Cards */}
      <div className="summary-section">
        <div className="summary-card total-value">
          <div className="card-label">Total Portfolio Value</div>
          <div className="card-value">
            ${portfolio.total_value.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </div>
          <div className="card-subtitle">
            Initial: ${portfolio.initial_value?.toLocaleString('en-US', { 
              minimumFractionDigits: 2 
            }) || '10,000.00'}
          </div>
        </div>

        <div className={`summary-card pnl ${portfolio.total_pnl >= 0 ? 'positive' : 'negative'}`}>
          <div className="card-label">Total P&L</div>
          <div className="card-value">
            {portfolio.total_pnl >= 0 ? '+' : ''}
            ${portfolio.total_pnl.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </div>
          <div className="card-percent">
            {portfolio.total_pnl >= 0 ? '+' : ''}
            {portfolio.total_pnl_pct.toFixed(2)}%
          </div>
        </div>

        <div className="summary-card cash">
          <div className="card-label">Available Cash</div>
          <div className="card-value">
            ${portfolio.cash.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </div>
          <div className="card-subtitle">
            {((portfolio.cash / portfolio.total_value) * 100).toFixed(1)}% of portfolio
          </div>
        </div>

        <div className="summary-card equity">
          <div className="card-label">Equity Value</div>
          <div className="card-value">
            ${portfolio.equity_value.toLocaleString('en-US', { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </div>
          <div className="card-subtitle">
            {positions.length} position{positions.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {/* Asset Evolution Chart */}
      {equityHistory.length > 0 && (
        <div className="chart-section">
          <div className="chart-header">
            <h2>Total Asset Value Over Time</h2>
            <div className="chart-controls">
              <button
                className={`scale-btn ${chartScale === 'linear' ? 'active' : ''}`}
                onClick={() => setChartScale('linear')}
              >
                Linear Scale
              </button>
              <button
                className={`scale-btn ${chartScale === 'log' ? 'active' : ''}`}
                onClick={() => setChartScale('log')}
              >
                Log Scale
              </button>
            </div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#667eea" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#667eea" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="date" 
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                />
                <YAxis 
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    padding: '12px',
                  }}
                  formatter={(value: number) => `$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#667eea"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorValue)"
                  name="Portfolio Value"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Positions Section */}
      {hasPositions ? (
        <div className="positions-section">
          <div className="section-header">
            <h2>Current Holdings</h2>
            <span className="position-count">{positions.length} holdings</span>
          </div>
          
          <div className="positions-table-container">
            <table className="positions-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Shares</th>
                  <th>Avg Cost</th>
                  <th>Current Price</th>
                  <th>Market Value</th>
                  <th>Unrealized P&L</th>
                  <th>P&L %</th>
                  <th>Weight</th>
                </tr>
              </thead>
              <tbody>
                {positions.map(([symbol, pos]) => {
                  const pnl = portfolio.positions_pnl[symbol] || { 
                    unrealized_pnl: 0, 
                    unrealized_pnl_pct: 0 
                  };
                  const isProfit = pnl.unrealized_pnl >= 0;
                  const weight = portfolio.total_value > 0 
                    ? ((pos.market_value / portfolio.total_value) * 100).toFixed(2)
                    : '0.00';
                  
                  return (
                    <tr key={symbol} className={isProfit ? 'profit-row' : 'loss-row'}>
                      <td className="symbol-cell">
                        <strong>{symbol}</strong>
                      </td>
                      <td>{pos.quantity}</td>
                      <td>${pos.avg_cost.toFixed(2)}</td>
                      <td>${pos.current_price.toFixed(2)}</td>
                      <td>${pos.market_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                      <td className={isProfit ? 'positive' : 'negative'}>
                        {isProfit ? '+' : ''}${pnl.unrealized_pnl.toFixed(2)}
                      </td>
                      <td className={isProfit ? 'positive' : 'negative'}>
                        {isProfit ? '+' : ''}{pnl.unrealized_pnl_pct.toFixed(2)}%
                      </td>
                      <td>{weight}%</td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="total-row">
                  <td colSpan={4}><strong>Total</strong></td>
                  <td><strong>${totalPositionsValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong></td>
                  <td className={totalUnrealizedPnL >= 0 ? 'positive' : 'negative'}>
                    <strong>{totalUnrealizedPnL >= 0 ? '+' : ''}${totalUnrealizedPnL.toFixed(2)}</strong>
                  </td>
                  <td>-</td>
                  <td>{portfolio.total_value > 0 ? ((totalPositionsValue / portfolio.total_value) * 100).toFixed(2) : '0.00'}%</td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Position Summary Stats */}
          <div className="position-stats">
            <div className="stat-item">
              <span className="stat-label">Total Positions Value:</span>
              <span className="stat-value">${totalPositionsValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Total Unrealized P&L:</span>
              <span className={`stat-value ${totalUnrealizedPnL >= 0 ? 'positive' : 'negative'}`}>
                {totalUnrealizedPnL >= 0 ? '+' : ''}${totalUnrealizedPnL.toFixed(2)}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Average Position Size:</span>
              <span className="stat-value">
                ${positions.length > 0 ? (totalPositionsValue / positions.length).toLocaleString('en-US', { minimumFractionDigits: 2 }) : '0.00'}
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="no-positions-section">
          <div className="empty-state">
            <div className="empty-icon">📊</div>
            <h3>No Positions</h3>
            <p>You don't have any open positions yet.</p>
            <p className="hint">Run a trading cycle to generate positions</p>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="monitor-footer">
        <div className="footer-info">
          <div className="api-info">
            <span className="api-label">API:</span>
            <span className="api-url">{getApiBase()}</span>
          </div>
          <div className="timestamp">
            {portfolio.timestamp ? (
              <>Data: {new Date(portfolio.timestamp).toLocaleString()}</>
            ) : (
              'No timestamp'
            )}
          </div>
        </div>
      </footer>
    </div>
  );
}
