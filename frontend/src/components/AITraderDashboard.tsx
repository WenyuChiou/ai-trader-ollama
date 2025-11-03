import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import './AITraderDashboard.css';

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

interface TradingAction {
  timestamp: string;
  symbol: string;
  action: 'BUY' | 'SELL';
  quantity: number;
  price: number;
}

const API_BASE = 'http://localhost:8000';

export default function AITraderDashboard() {
  const [portfolio, setPortfolio] = useState<PortfolioSnapshot | null>(null);
  const [equityHistory, setEquityHistory] = useState<any[]>([]);
  const [recentActions, setRecentActions] = useState<TradingAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRealTimePortfolio = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/portfolio/real-time`);
      if (!response.ok) throw new Error('Failed to fetch real-time portfolio');
      const data = await response.json();
      if (!data.ok || data.error) throw new Error(data.error || 'Failed to load portfolio');
      // data already contains the snapshot fields directly
      setPortfolio(data as PortfolioSnapshot);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching real-time portfolio:', err);
    }
  };

  const fetchEquityHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/portfolio/equity-history?limit=60`);
      if (!response.ok) throw new Error('Failed to fetch equity history');
      const data = await response.json();
      if (!data.ok || data.error) {
        console.warn('Equity history not available:', data.error);
        return;
      }
      
      // Transform data for chart
      const chartData = (data.records || []).map((item: any) => ({
        date: item.date || item.timestamp?.split('T')[0] || '',
        value: item.total_value || 0,
        pnl: item.total_pnl || 0,
      }));
      setEquityHistory(chartData);
    } catch (err) {
      console.error('Error fetching equity history:', err);
    }
  };

  const fetchRecentActions = async () => {
    // TODO: Implement when trading actions API is available
    // For now, using placeholder
    setRecentActions([]);
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchRealTimePortfolio(),
        fetchEquityHistory(),
        fetchRecentActions(),
      ]);
      setLoading(false);
    };

    loadData();
    
    // Refresh every minute
    const interval = setInterval(() => {
      fetchRealTimePortfolio();
    }, 60000);

    // Refresh equity history every 5 minutes
    const equityInterval = setInterval(() => {
      fetchEquityHistory();
    }, 300000);

    return () => {
      clearInterval(interval);
      clearInterval(equityInterval);
    };
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading trading data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="ai-trader-dashboard">
      <header className="dashboard-header">
        <h1>📊 AI-Trader</h1>
        <div className="header-stats">
          <div className="stat-item">
            <span className="stat-label">Total Value</span>
            <span className="stat-value">${portfolio?.total_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total P&L</span>
            <span className={`stat-value ${(portfolio?.total_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
              ${portfolio?.total_pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              ({portfolio?.total_pnl_pct.toFixed(2) || '0.00'}%)
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Cash</span>
            <span className="stat-value">${portfolio?.cash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}</span>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        {/* Asset Evolution Chart */}
        <section className="chart-section">
          <h2>Total Asset Value Over Time</h2>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={equityHistory}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                />
                <Tooltip 
                  formatter={(value: any) => `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#8884d8" 
                  fillOpacity={1} 
                  fill="url(#colorValue)"
                  name="Total Value"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Portfolio Positions */}
        <section className="positions-section">
          <h2>Current Positions</h2>
          {portfolio?.positions && Object.keys(portfolio.positions).length > 0 ? (
            <div className="positions-grid">
              {Object.entries(portfolio.positions).map(([symbol, pos]) => {
                const pnl = portfolio.positions_pnl[symbol];
                return (
                  <div key={symbol} className="position-card">
                    <div className="position-header">
                      <h3>{symbol}</h3>
                      <span className={`pnl-badge ${(pnl?.unrealized_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                        {pnl?.unrealized_pnl_pct.toFixed(2) || '0.00'}%
                      </span>
                    </div>
                    <div className="position-details">
                      <div className="detail-row">
                        <span>Quantity:</span>
                        <span>{pos.quantity}</span>
                      </div>
                      <div className="detail-row">
                        <span>Avg Cost:</span>
                        <span>${pos.avg_cost.toFixed(2)}</span>
                      </div>
                      <div className="detail-row">
                        <span>Current Price:</span>
                        <span>${pos.current_price.toFixed(2)}</span>
                      </div>
                      <div className="detail-row">
                        <span>Market Value:</span>
                        <span>${pos.market_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      </div>
                      <div className="detail-row">
                        <span>Unrealized P&L:</span>
                        <span className={(pnl?.unrealized_pnl || 0) >= 0 ? 'positive' : 'negative'}>
                          ${pnl?.unrealized_pnl.toFixed(2) || '0.00'}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="no-data">No positions currently held</p>
          )}
        </section>

        {/* Recent Trading Actions */}
        <section className="actions-section">
          <h2>Recent Trading Actions</h2>
          {recentActions.length > 0 ? (
            <div className="actions-list">
              {recentActions.map((action, idx) => (
                <div key={idx} className="action-item">
                  <span className="action-time">{new Date(action.timestamp).toLocaleString()}</span>
                  <span className={`action-type ${action.action.toLowerCase()}`}>{action.action}</span>
                  <span className="action-symbol">{action.symbol}</span>
                  <span className="action-quantity">{action.quantity}</span>
                  <span className="action-price">${action.price.toFixed(2)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-data">No recent trading actions</p>
          )}
        </section>
      </main>

      <footer className="dashboard-footer">
        <p>AI-Trader © 2025 | Real-Time Portfolio Monitoring</p>
        <p>Last updated: {portfolio?.timestamp ? new Date(portfolio.timestamp).toLocaleString() : 'Never'}</p>
      </footer>
    </div>
  );
}

