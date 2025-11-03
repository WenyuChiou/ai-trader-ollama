import React, { useEffect, useState } from 'react';
import EquityChart from './EquityChart';

interface Position {
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl?: number;
  unrealized_pnl_pct?: number;
}

interface PortfolioData {
  date: string;
  cash: number;
  equity_value: number;
  total_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  positions: Record<string, Position>;
}

interface EquityRecord {
  date: string;
  total_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  equity_value: number;
  cash: number;
  positions: Record<string, Position>;
}

const PortfolioDashboard: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [equityHistory, setEquityHistory] = useState<EquityRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    fetchPortfolioData();
    fetchEquityHistory();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchPortfolioData();
      fetchEquityHistory();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const fetchPortfolioData = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/portfolio/current`);
      const data = await response.json();
      
      if (data.ok && data.portfolio) {
        setPortfolio(data.portfolio);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch portfolio');
    } finally {
      setLoading(false);
    }
  };

  const fetchEquityHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/portfolio/equity-history?limit=60`);
      const data = await response.json();
      
      if (data.ok && data.records) {
        setEquityHistory(data.records);
      }
    } catch (err) {
      console.error('Failed to fetch equity history:', err);
    }
  };

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading portfolio data...</div>;
  }

  if (error) {
    return <div style={{ padding: '20px', color: 'red' }}>Error: {error}</div>;
  }

  if (!portfolio) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>No portfolio data available.</p>
        <p style={{ color: '#666', fontSize: '14px' }}>
          Run a trading cycle to start tracking portfolio performance.
        </p>
      </div>
    );
  }

  const positions = Object.entries(portfolio.positions || {});

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1>Portfolio Dashboard</h1>
      
      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        <div style={{ padding: '20px', background: '#f5f5f5', borderRadius: '8px' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Total Value</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#333' }}>
            ${portfolio.total_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        
        <div style={{ padding: '20px', background: '#f5f5f5', borderRadius: '8px' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Total P&L</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: portfolio.total_pnl >= 0 ? '#22c55e' : '#ef4444' }}>
            ${portfolio.total_pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '14px', color: portfolio.total_pnl >= 0 ? '#22c55e' : '#ef4444' }}>
            ({portfolio.total_pnl_pct >= 0 ? '+' : ''}{portfolio.total_pnl_pct.toFixed(2)}%)
          </div>
        </div>
        
        <div style={{ padding: '20px', background: '#f5f5f5', borderRadius: '8px' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Cash</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#333' }}>
            ${portfolio.cash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        
        <div style={{ padding: '20px', background: '#f5f5f5', borderRadius: '8px' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>Equity Value</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#333' }}>
            ${portfolio.equity_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      {/* Equity Chart */}
      <div style={{ marginBottom: '30px' }}>
        <h2>Equity Curve</h2>
        <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <EquityChart data={equityHistory} height={400} />
        </div>
      </div>

      {/* Positions Table */}
      {positions.length > 0 && (
        <div style={{ marginBottom: '30px' }}>
          <h2>Current Positions</h2>
          <div style={{ background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f5f5f5' }}>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Symbol</th>
                  <th style={{ padding: '12px', textAlign: 'right', borderBottom: '2px solid #ddd' }}>Quantity</th>
                  <th style={{ padding: '12px', textAlign: 'right', borderBottom: '2px solid #ddd' }}>Avg Cost</th>
                  <th style={{ padding: '12px', textAlign: 'right', borderBottom: '2px solid #ddd' }}>Current Price</th>
                  <th style={{ padding: '12px', textAlign: 'right', borderBottom: '2px solid #ddd' }}>Market Value</th>
                  <th style={{ padding: '12px', textAlign: 'right', borderBottom: '2px solid #ddd' }}>Unrealized P&L</th>
                  <th style={{ padding: '12px', textAlign: 'right', borderBottom: '2px solid #ddd' }}>P&L %</th>
                </tr>
              </thead>
              <tbody>
                {positions.map(([symbol, pos]) => {
                  const pnl = pos.unrealized_pnl ?? (pos.current_price - pos.avg_cost) * pos.quantity;
                  const pnlPct = pos.unrealized_pnl_pct ?? ((pos.current_price - pos.avg_cost) / pos.avg_cost * 100);
                  
                  return (
                    <tr key={symbol} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '12px', fontWeight: 'bold' }}>{symbol}</td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>{pos.quantity}</td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>
                        ${pos.avg_cost.toFixed(2)}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>
                        ${pos.current_price.toFixed(2)}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>
                        ${pos.market_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: pnl >= 0 ? '#22c55e' : '#ef4444' }}>
                        ${pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: pnlPct >= 0 ? '#22c55e' : '#ef4444' }}>
                        {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%
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
        <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
          No positions held.
        </div>
      )}
    </div>
  );
};

export default PortfolioDashboard;

